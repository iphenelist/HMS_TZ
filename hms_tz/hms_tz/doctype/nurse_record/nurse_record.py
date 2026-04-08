# Copyright (c) 2026, Aakvatech and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import nowdate, nowtime


class NurseRecord(Document):
    def before_save(self):
        self.set_inpatient_record()
        self.validate_posting_date()
        self.validate_no_duplicate()
        self.validate_service_unit_fields()
        self.set_status_on_save()
        self.set_previous_notes()

    def set_inpatient_record(self):
        """Auto-set inpatient_record from the patient if not already set."""
        if self.patient and not self.inpatient_record:
            self.inpatient_record = frappe.db.get_value(
                "Patient",
                self.patient,
                "inpatient_record",
            )

    def validate_posting_date(self):
        if not self.posting_date:
            self.posting_date = nowdate()
            self.posting_time = nowtime()

    def validate_no_duplicate(self):
        """Prevent duplicate nurse records for the same patient + nurse + date."""
        filters = {
            "patient": self.patient,
            "nurse": self.nurse,
            "posting_date": self.posting_date,
            "docstatus": ["!=", 2],
        }
        if not self.is_new():
            filters["name"] = ["!=", self.name]

        existing = frappe.db.exists("Nurse Record", filters)
        if existing:
            frappe.throw(
                _(
                    "A Nurse Record already exists for patient {0} with nurse"
                    " {1} on {2}: {3}"
                ).format(self.patient, self.nurse, self.posting_date, existing)
            )

    def validate_service_unit_fields(self):
        """Validate service unit fields.

        Rules:
        - If service_unit is set but service_unit_type is missing: OK
        - If service_unit_type is set but service_unit is missing: OK
        - If BOTH are missing: throw validation error
        """
        if not self.service_unit and not self.service_unit_type:
            frappe.throw(
                _(
                    "Please set at least one of Service Unit or Service Unit"
                    " Type."
                )
            )

    def set_status_on_save(self):
        """Auto-update status based on content."""
        if self.status == "Open" and (
            self.care_plans or self.nursing_notes or self.observations
        ):
            self.status = "In Progress"

    def set_previous_notes(self):
        """Copy nursing_notes from the most recent previous Nurse Record for this patient."""

        if not self.is_new() or not self.patient:
            return

        nurse_details = frappe.db.get_value(
            "Nurse Record",
            filters={
                "patient": self.patient,
                "docstatus": ["!=", 2],
                "name": ["!=", self.name or ""],
            },
            fieldname=["nursing_notes", "previous_notes", "posting_date", "posting_time"],
            order_by="posting_date desc, creation desc",
            as_dict=True
        )

        if not nurse_details:
            return

        nurse_info = ""
        if nurse_details.nursing_notes:
            nurse_info = f"""
            Nurse: <b>{nurse_details.nurse}</b>: Date: <b>{nurse_details.posting_date + ' ' + nurse_details.posting_time}</b><br>{nurse_details.nursing_notes}
            """
        self.previous_notes = nurse_info + "\n\n" + (nurse_details.previous_notes or "")


@frappe.whitelist()
def get_vital_signs(patient, appointment=None):
    """Fetch vital signs for a patient's episode (from appointment to current).

    Returns vital signs data for rendering charts and table in the Nurse Record.
    """
    filters = {
        "patient": patient,
        "docstatus": 1,
    }
    if appointment:
        filters["appointment"] = appointment

    vitals = frappe.db.get_all(
        "Vital Signs",
        filters=filters,
        fields=[
            "name",
            "signs_date",
            "signs_time",
            "temperature",
            "pulse",
            "respiratory_rate",
            "bp_systolic",
            "bp_diastolic",
            "bp",
            "weight",
            "height",
            "bmi",
            "vital_signs_note",
        ],
        order_by="signs_date asc, signs_time asc",
        limit_page_length=0,
    )

    return vitals


@frappe.whitelist()
def create_vital_signs(patient, nurse_record, **kwargs):
    """Create a Vital Signs record from the Nurse Record dialog.

    Args:
        patient: Patient ID
        nurse_record: Nurse Record name for linking
        **kwargs: Vital signs field values (temperature, pulse, bp_systolic, etc.)
    """
    nr = frappe.get_doc("Nurse Record", nurse_record)
    vs = frappe.new_doc("Vital Signs")
    vs.patient = patient
    vs.appointment = nr.appointment
    vs.inpatient_record = nr.inpatient_record
    vs.company = nr.company
    vs.signs_date = nowdate()

    # Set vital sign values from kwargs
    vital_fields = [
        "temperature",
        "pulse",
        "respiratory_rate",
        "bp_systolic",
        "bp_diastolic",
        "weight",
        "height",
        "tongue",
        "abdomen",
        "reflexes",
        "vital_signs_note",
    ]
    for field in vital_fields:
        if kwargs.get(field):
            vs.set(field, kwargs[field])

    vs.insert(ignore_permissions=True)
    vs.submit()

    return vs.name


def create_nurse_records_for_admitted_patients():
    """Background job (every 4 hours): auto-create Nurse Records for admitted patients.

    Logic:
    1. Get all Nursing Schedule records for today that haven't yet generated
       a Nurse Record (nurse_record_created == 0).
    2. Get all Inpatient Records with status 'Admitted'.
    3. For each admitted patient, get the last service unit from the
       inpatient_occupancies child table.
    4. Match nursing schedules by comparing:
       - schedule.service_unit == last occupancy service_unit, OR
       - schedule.service_unit_type == service_unit_type of the last
         occupancy's service unit
    5. Create a Nurse Record for each match if one doesn't already exist.
    6. Mark the Nursing Schedule's nurse_record_created checkbox.
    """
    today = nowdate()

    # Get today's nursing schedules that haven't generated records
    schedules = frappe.db.get_all(
        "Nursing Schedule",
        filters={
            "assignment_date": today,
            "docstatus": 1,
            "nurse_record_created": 0,
        },
        fields=[
            "name",
            "nurse",
            "nurse_name",
            "company",
            "assign_based_on",
            "service_unit",
            "service_unit_type",
        ],
    )

    if not schedules:
        return

    # Get all admitted inpatient records
    admitted_records = frappe.db.get_all(
        "Inpatient Record",
        filters={"status": "Admitted"},
        fields=["name", "patient", "company", "patient_appointment"],
    )

    if not admitted_records:
        return

    for ip in admitted_records:
        # Get the last service unit from inpatient occupancies
        last_occupancy = frappe.db.get_value(
            "Inpatient Occupancy",
            filters={
                "parent": ip.name,
                "parenttype": "Inpatient Record",
                "left": 0,
            },
            fieldname="service_unit",
            order_by="check_in desc",
        )

        if not last_occupancy:
            continue

        # Get the service unit type of the last occupancy's service unit
        last_su_type = frappe.db.get_value(
            "Healthcare Service Unit",
            last_occupancy,
            "service_unit_type",
        )

        for schedule in schedules:
            # Only match schedules in the same company
            if schedule.company != ip.company:
                continue

            # Match by service_unit or service_unit_type
            matched = False
            if (
                schedule.assign_based_on == "Service Unit"
                and schedule.service_unit
            ):
                matched = schedule.service_unit == last_occupancy
            elif (
                schedule.assign_based_on == "Service Unit Type"
                and schedule.service_unit_type
            ):
                matched = schedule.service_unit_type == last_su_type

            if not matched:
                continue

            #Check if a record already exists
            existing = frappe.db.exists(
                "Nurse Record",
                {
                    "patient": ip.patient,
                    "nurse": schedule.nurse,
                    "posting_date": today,
                    "docstatus": ["!=", 2],
                    "nurse": schedule.nurse,
                },
            )
            if existing:
                # Still mark the schedule as processed
                frappe.db.set_value(
                    "Nursing Schedule",
                    schedule.name,
                    "nurse_record_created",
                    1,
                    update_modified=False,
                )
                continue


            try:
                nr = frappe.new_doc("Nurse Record")
                nr.appointment = ip.patient_appointment
                nr.patient = ip.patient
                nr.nurse = schedule.nurse
                nr.posting_date = today
                nr.company = ip.company
                nr.inpatient_record = ip.name
                nr.service_unit = (
                    last_occupancy
                    if schedule.assign_based_on == "Service Unit"
                    else None
                )
                nr.service_unit_type = (
                    last_su_type
                    if schedule.assign_based_on == "Service Unit Type"
                    else None
                )
                nr.flags.ignore_validate = True
                nr.insert(ignore_permissions=True)

                # Mark the nursing schedule
                frappe.db.set_value(
                    "Nursing Schedule",
                    schedule.name,
                    "nurse_record_created",
                    1,
                    update_modified=False,
                )

            except Exception:
                frappe.log_error(
                    title="Nurse Record Auto-Creation Error",
                    message=(
                        f"Failed to create Nurse Record for patient"
                        f" {ip.patient}, nurse {schedule.nurse},"
                        f" schedule {schedule.name}"
                    ),
                    reference_doctype="Nursing Schedule",
                    reference_name=schedule.name,
                )
                frappe.db.rollback()




