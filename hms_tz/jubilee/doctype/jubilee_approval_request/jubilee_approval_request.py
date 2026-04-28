# Copyright (c) 2025, Aakvatech and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from frappe.model.document import Document
from frappe.query_builder import DocType
from frappe.utils import get_datetime, get_fullname, get_time, getdate, nowdate, nowtime

from hms_tz.hms_tz.doctype.healthcare_service_request.healthcare_service_request import (
    get_childs_map,
    get_item_rate,
    get_item_refcode,
)
from hms_tz.jubilee.api.api import send_preauthorization

ct = DocType("Codification Table")
pe = DocType("Patient Encounter")


class JubileeApprovalRequest(Document):
    def before_save(self):
        """Auto-populate fields from Patient Encounter for manual creation (Path B)."""

        self.set_missing_values()

    def set_missing_values(self):
        """Pull patient demographics, diseases, and items from the linked encounter."""
        if not self.patient_encounter:
            frappe.throw(_("Patient Encounter is required"))

        encounter = frappe.get_doc("Patient Encounter", self.patient_encounter)

        self.appointment = encounter.appointment
        self.patient = encounter.patient
        self.patient_name = encounter.patient_name
        self.company = encounter.company

        patient_doc = frappe.get_cached_doc("Patient", encounter.patient)
        self.first_name = patient_doc.first_name
        self.last_name = patient_doc.last_name or ""
        self.gender = patient_doc.sex
        self.date_of_birth = patient_doc.dob
        self.telephone_no = patient_doc.mobile or ""
        self.inpatient_record = patient_doc.inpatient_record

        if encounter.appointment:
            appt = frappe.get_cached_doc("Patient Appointment", encounter.appointment)
            self.card_no = appt.coverage_plan_card_number or ""
            self.authorization_no = appt.authorization_number or ""
            self.attendance_date = f"{appt.appointment_date} {appt.appointment_time or '00:00:00'}"

        if encounter.practitioner:
            mct_code = frappe.db.get_value(
                "Healthcare Practitioner", encounter.practitioner, "tz_mct_code"
            )
            self.practitioner_no = mct_code or ""

        self.jubilee_procedure = encounter.get("jubilee_procedure") or ""

        self.provider_id = frappe.get_cached_value(
            "HMS TZ Setting", self.company, "jubilee_provider_id"
        ) or ""

        if not self.posting_date:
            self.posting_date = nowdate()
        if not self.posting_time:
            self.posting_time = nowtime()

        posting = getdate(self.posting_date)
        self.claim_year = posting.year
        self.claim_month = posting.month

        self.bill_no = "".join(self.name.split("-")[1:])

        self.set_diseases()
        self.set_items(encounter)
        self.set_inpatient_dates()

    def set_diseases(self):
        """Populate disease child table from encounter's preliminary and final diagnoses."""

        self.diseases = []

        diagnosis_list = (
            frappe.qb.from_(ct)
            .join(pe)
            .on(ct.parent == pe.name)
            .select(
                ct.name,
                ct.parent,
                ct.code_value,
                ct.code_value.as_("medical_code"),
                ct.code.as_("code"),
                ct.definition,
                ct.modified,
                ct.parentfield,
                pe.practitioner,
            )
            .where(
                (ct.parenttype == "Patient Encounter")
                & (ct.parent == self.patient_encounter)
            )
            .groupby(ct.code_value, ct.parentfield)
            .orderby(ct.parentfield, order=frappe.qb.desc)
        ).run(as_dict=True)

        for row in diagnosis_list:
            new_row = self.append("diseases", {})
            if row.parentfield == "patient_encounter_preliminary_diagnosis":
                new_row.status = "Provisional"
            elif row.parentfield == "patient_encounter_final_diagnosis":
                new_row.status = "Final"

            new_row.patient_encounter = row.parent
            new_row.codification_table = row.name
            new_row.medical_code = row.code_value

            # Convert ICD code format (CDC to NHIF style)
            if row.code and len(row.code) > 3 and "." not in row.code:
                new_row.disease_code = row.code[:3] + "." + (row.code[3:4] or "0")
            elif row.code and len(row.code) <= 5 and "." in row.code:
                new_row.disease_code = row.code
            else:
                new_row.disease_code = row.code[:3] if row.code else ""

            new_row.description = (row.definition or "")[:139]
            new_row.created_by = row.practitioner
            new_row.date_created = row.modified

    def set_items(self, encounter_doc):
        """Populate item child table from encounter's service items."""

        self.items = []

        total_amount = 0
        for child in get_childs_map():
            if not encounter_doc.get(child.get("table")):
                continue

            for row in encounter_doc.get(child.get("table")):
                if not row.get(child.get("item")):
                    continue

                # Skip cancelled/prescribed/restricted items
                if (
                    row.get("prescribe")
                    or row.get("is_not_available_inhouse")
                    or row.get("is_cancelled")
                    or row.get("is_restricted")
                ):
                    continue

                ref_code = get_item_refcode(
                    child.get("doctype"),
                    row.get(child.get("item")),
                    encounter_doc.company,
                    encounter_doc.insurance_company,
                )

                item_code = frappe.get_cached_value(
                    child.get("doctype"),
                    row.get(child.get("item")),
                    "item",
                )
                if not item_code:
                    continue

                item_rate = get_item_rate(
                    item_code,
                    encounter_doc.company,
                    encounter_doc.insurance_subscription,
                    encounter_doc.insurance_company,
                )

                quantity = row.get("quantity") or 1
                amount = item_rate * quantity

                new_row = self.append("items", {})
                new_row.item_name = row.get(child.get("item"))
                new_row.item_code = str(ref_code) if ref_code else ""
                new_row.item_quantity = quantity
                new_row.unit_price = item_rate
                new_row.amount_claimed = amount
                new_row.ref_doctype = row.get("doctype")
                new_row.ref_docname = row.get("name")
                new_row.patient_encounter = encounter_doc.name
                new_row.created_by = get_fullname(frappe.session.user)
                new_row.date_created = nowdate()

                total_amount += amount

        self.total_amount = total_amount

    def set_inpatient_dates(self):
        """Set admitted/discharged dates from the encounter's inpatient record."""

        if not self.inpatient_record:
            return

        (
            discharge_date,
            scheduled_date,
            admitted_datetime,
            time_created,
        ) = frappe.get_cached_value(
            "Inpatient Record",
            self.inpatient_record,
            [
                "discharge_date",
                "scheduled_date",
                "admitted_datetime",
                "creation",
            ],
        )

        if not admitted_datetime:
            return

        if scheduled_date and getdate(scheduled_date) < getdate(admitted_datetime):
            self.admitted_date = f"{scheduled_date} {get_time(get_datetime(time_created))}"
        else:
            self.admitted_date = str(admitted_datetime)

        if discharge_date and getdate(self.admitted_date) == getdate(discharge_date):
            self.patient_type_code = "OP"
            self.admitted_date = None
            self.discharge_date = None
        elif discharge_date:
            self.patient_type_code = "IN"
            self.discharge_date = f"{discharge_date} {nowtime()}"

            # Override claim year/month from discharge date when inpatient
            d = getdate(discharge_date)
            self.claim_year = d.year
            self.claim_month = d.month

    def calculate_totals(self):
        """Recalculate total_amount from items."""
        total = 0
        for row in self.items:
            row.amount_claimed = (row.unit_price or 0) * (row.item_quantity or 1)
            total += row.amount_claimed

        self.total_amount = total

    @frappe.whitelist()
    def send_to_jubilee(self):
        """Send the pre-authorization request to Jubilee API on submit."""
        result = send_preauthorization(self.name)
        self.preauth_status = result.get("status") or ""
        self.preauth_description = result.get("description") or ""
        self.submission_id = result.get("submission_id") or ""

        self.db_update()

        self.add_comment(
            comment_type="Comment",
            text=f"""Jubilee Pre-Authorization request sent<br/>Status: {self.preauth_status}<br/>\
                Description: {self.preauth_description}<br/>Submission ID: {self.submission_id}""",
        )

        return {
            "status": self.preauth_status,
            "description": self.preauth_description,
            "submission_id": self.submission_id,
        }

@frappe.whitelist()
def create_preauthorization_doc(source_doctype, source_docname, benefit_code):
    """Create or reuse a Jubilee Approval Request record and submit it."""

    if not source_docname:
        frappe.throw(_("Source document name is required"))

    source_doc = frappe.get_doc(source_doctype, source_docname)

    benefit_name = ""
    benefit_balance = 0
    if benefit_code:
        benefit_name, benefit_balance = frappe.get_cached_value(
            "Jubilee Benefit",
            {"appointment": source_doc.appointment, "benefit_code": benefit_code},
            ["benefit_name", "benefit_balance"],
        ) or ("", 0)

    existing_jar = frappe.db.get_value(
        "Jubilee Approval Request",
        {"patient_encounter": source_docname},
        "name"
    )

    jar_doc = None
    if existing_jar:
        jar_doc = frappe.get_doc("Jubilee Approval Request", existing_jar)
        jar_doc.benefit_code = benefit_code
        jar_doc.benefit_name = benefit_name
        jar_doc.benefit_balance = benefit_balance
        jar_doc.save(ignore_permissions=True)
    else:
        jar_doc = frappe.new_doc("Jubilee Approval Request")
        jar_doc.patient_encounter = source_docname
        jar_doc.benefit_code = benefit_code
        jar_doc.benefit_name = benefit_name
        jar_doc.benefit_balance = benefit_balance
        jar_doc.save(ignore_permissions=True)

    result = jar_doc.send_to_jubilee()

    source_doc.add_comment(
        comment_type="Comment",
        text=(
            f"Jubilee Pre-Authorization request sent<br>"
            f"Approval Request: <b>{jar_doc.name}</b><br>"
            f"Status: <b>{result.get('status') or 'N/A'}</b><br>"
            f"Submission ID: <b>{result.get('submission_id') or 'N/A'}</b>"
        ),
    )

    return {
        "status": result.get('status') or "ERROR",
        "submission_id": result.get('submission_id') or "",
        "description": result.get('description') or "",
        "service_request": jar_doc.name,
    }
