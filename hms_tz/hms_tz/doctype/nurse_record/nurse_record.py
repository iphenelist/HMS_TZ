# Copyright (c) 2026, Aakvatech and contributors
# For license information, please see license.txt

from datetime import timedelta as td

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import (
    cint,
    now_datetime,
    nowdate,
    nowtime,
    time_diff_in_seconds,
    to_timedelta,
)
from healthcare.healthcare.doctype.patient_encounter.patient_encounter import (
    get_prescription_dates,
)


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


@frappe.whitelist()
def get_pending_medications(patient, inpatient_record):
    """Fetch pending (not completed) IMO entries for a patient.

    Returns entries for today and any overdue from previous days,
    excluding entries with administration_status = 'Held' separately.
    """
    today = nowdate()

    imo_list = frappe.db.get_all(
        "Inpatient Medication Order",
        filters={
            "patient": patient,
            "inpatient_record": inpatient_record,
            "docstatus": 1,
            "status": ["in", ["Pending", "In Process"]],
        },
        fields=["name"],
        pluck="name",
    )

    if not imo_list:
        return []

    entries = frappe.db.get_all(
        "Inpatient Medication Order Entry",
        filters={
            "parent": ["in", imo_list],
            "is_completed": 0,
            "date": ["<=", today],
        },
        fields=[
            "name", "drug", "drug_name", "dosage", "dosage_form",
            "date", "time", "instructions", "parent",
            "administration_status",
        ],
        order_by="date asc, time asc",
    )

    return entries


@frappe.whitelist()
def update_medication_status(
    imo_entry_name, status, notes=None, nurse_record=None
):
    """Update IMO Entry with administration status and related fields.

    Args:
        imo_entry_name: Name of the Inpatient Medication Order Entry
        status: One of 'Administered', 'Skipped', 'Refused', 'Held'
        notes: Optional notes/reason
        nurse_record: Optional Nurse Record name for context
    """
    valid_statuses = ["Administered", "Skipped", "Refused", "Held"]
    if status not in valid_statuses:
        frappe.throw(_("Invalid status: {0}").format(status))

    imo_entry = frappe.db.get_value(
        "Inpatient Medication Order Entry",
        imo_entry_name,
        ["parent", "drug", "date", "time"],
        as_dict=True,
    )

    if not imo_entry or not imo_entry.parent:
        frappe.throw(_("IMO Entry {0} not found or has no parent.").format(imo_entry_name))

    now = now_datetime()

    # Update IMO Entry custom fields
    update_fields = {
        "administration_status": status,
        "administered_time": now,
        "administered_by": frappe.session.user,
    }
    if notes:
        update_fields["administration_notes"] = notes

    # For Administered, Skipped, Refused → mark as completed (resolved)
    # For Held → keep as not completed (stays in pending)
    if status in ("Administered", "Skipped", "Refused"):
        update_fields["is_completed"] = 1

    for field, value in update_fields.items():
        frappe.db.set_value(
            "Inpatient Medication Order Entry",
            imo_entry_name,
            field,
            value,
            update_modified=False,
        )

    # Update parent IMO completed count and status
    if status in ("Administered", "Skipped", "Refused"):
        imo = frappe.get_doc("Inpatient Medication Order", imo_entry.parent)
        completed = cint(imo.completed_orders) + 1
        frappe.db.set_value(
            "Inpatient Medication Order",
            imo.name,
            "completed_orders",
            completed,
            update_modified=False,
        )
        imo.reload()
        imo.set_status()

    # Recalculate remaining schedules if administered late (> 60 min delta)
    if status == "Administered":
        scheduled_time = imo_entry.time
        actual_time = now.time()

        delta_seconds = abs(
            time_diff_in_seconds(str(actual_time), str(scheduled_time))
        )
        if delta_seconds > 3600:
            recalculate_remaining_schedules(
                imo_entry.parent,
                imo_entry.drug,
                imo_entry.date,
                scheduled_time,
                actual_time,
            )

    return {"status": "success", "administration_status": status}


def recalculate_remaining_schedules(
    imo_name, drug, reference_date, scheduled_time, actual_time
):
    """Recalculate remaining scheduled doses for the same drug on the same day.

    If the administered time differs from the scheduled time, shift all remaining
    pending entries for that drug on that day forward by the same delta.

    Args:
        imo_name: Inpatient Medication Order name
        drug: Item code of the drug
        reference_date: The date of the administered dose
        scheduled_time: Originally scheduled time
        actual_time: Time medication was actually administered
    """

    # Calculate the time delta
    scheduled_td = to_timedelta(str(scheduled_time))
    actual_td = to_timedelta(str(actual_time))
    delta = actual_td - scheduled_td  # positive = late, negative = early

    # Get remaining pending entries for the same drug on the same day
    remaining = frappe.db.get_all(
        "Inpatient Medication Order Entry",
        filters={
            "parent": imo_name,
            "drug": drug,
            "date": reference_date,
            "is_completed": 0,
        },
        fields=["name", "time"],
        order_by="time asc",
    )

    if not remaining:
        return

    for entry in remaining:
        old_time = to_timedelta(str(entry.time))
        new_time = old_time + delta

        # Clamp to same day (don't go past midnight or before 00:00)
        total_seconds = new_time.total_seconds()
        if total_seconds < 0:
            total_seconds = 0
        elif total_seconds >= 86400:  # 24 hours
            total_seconds = 86399  # 23:59:59

        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        seconds = int(total_seconds % 60)
        new_time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

        frappe.db.set_value(
            "Inpatient Medication Order Entry",
            entry.name,
            "time",
            new_time_str,
            update_modified=False,
        )


@frappe.whitelist()
def get_completed_medications(patient, inpatient_record):
    """Fetch all completed medication entries for the history section.

    Returns a list of dicts with drug_name, dosage, date, time, status, etc.
    """
    imo_list = frappe.db.get_all(
        "Inpatient Medication Order",
        filters={
            "patient": patient,
            "inpatient_record": inpatient_record,
            "docstatus": 1,
        },
        fields=["name"],
    )

    if not imo_list:
        return []

    imo_names = [imo.name for imo in imo_list]

    entries = frappe.db.get_all(
        "Inpatient Medication Order Entry",
        filters={
            "parent": ["in", imo_names],
            "is_completed": 1,
        },
        fields=[
            "name", "drug", "drug_name", "dosage", "dosage_form",
            "date", "time", "parent",
            "administration_status", "administered_time",
            "administered_by", "administration_notes",
        ],
        order_by="date desc, time desc",
        limit_page_length=50,
    )

    return entries


@frappe.whitelist()
def get_medication_progress(patient, inpatient_record):
    """Returns aggregated data for the medication progress chart.

    Groups by drug_name and counts: total, completed, pending.
    """
    imo_list = frappe.db.get_all(
        "Inpatient Medication Order",
        filters={
            "patient": patient,
            "inpatient_record": inpatient_record,
            "docstatus": 1,
        },
        fields=["name"],
    )

    if not imo_list:
        return []

    imo_names = [imo.name for imo in imo_list]

    entries = frappe.db.get_all(
        "Inpatient Medication Order Entry",
        filters={
            "parent": ["in", imo_names],
        },
        fields=["drug_name", "is_completed"],
        limit_page_length=0,
    )

    # Aggregate by drug_name
    progress = {}
    for entry in entries:
        name = entry.drug_name or "Unknown"
        if name not in progress:
            progress[name] = {"drug_name": name, "total": 0, "completed": 0, "pending": 0}
        progress[name]["total"] += 1
        if entry.is_completed:
            progress[name]["completed"] += 1
        else:
            progress[name]["pending"] += 1

    return list(progress.values())


@frappe.whitelist()
def get_upcoming_medications(nurse, within_minutes=60):
    """Check upcoming medications for ALL patients assigned to this nurse.

    Returns list of {patient, patient_name, drug_name, scheduled_time, nurse_record_name}.
    This is used for the dashboard alert banner showing all patients under the nurse.
    """
    today = nowdate()
    now = now_datetime()

    cutoff_time = (now + td(minutes=cint(within_minutes))).time()
    current_time = now.time()

    # Get all active Nurse Records for this nurse
    nurse_records = frappe.db.get_all(
        "Nurse Record",
        filters={
            "nurse": nurse,
            "posting_date": today,
            "status": ["in", ["Open", "In Progress"]],
            "docstatus": ["!=", 2],
        },
        fields=["name", "patient", "patient_name", "inpatient_record"],
    )

    if not nurse_records:
        return []

    results = []
    for nr in nurse_records:
        if not nr.inpatient_record:
            continue

        # Get pending IMO entries for this patient due within the window
        imo_list = frappe.db.get_all(
            "Inpatient Medication Order",
            filters={
                "patient": nr.patient,
                "inpatient_record": nr.inpatient_record,
                "docstatus": 1,
                "status": ["in", ["Pending", "In Process"]],
            },
            fields=["name"],
            pluck="name",
        )

        if not imo_list:
            continue

        upcoming = frappe.db.get_all(
            "Inpatient Medication Order Entry",
            filters=[
                ["parent", "in", imo_list],
                ["is_completed", "=", 0],
                ["date", "=", today],
                ["time", ">=", str(current_time)],
                ["time", "<=", str(cutoff_time)],
            ],
            fields=["drug_name", "drug", "time", "dosage", "dosage_form"],
        )

        for med in upcoming:
            results.append({
                "patient": nr.patient,
                "patient_name": nr.patient_name,
                "drug_name": med.drug_name,
                "dosage": med.dosage,
                "dosage_form": med.dosage_form or "",
                "scheduled_time": str(med.time),
                "nurse_record_name": nr.name,
            })

    return results


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


def create_imo_from_delivery_note(doc, method):
    """On submit of Delivery Note, auto-create Inpatient Medication Order.

    Only runs for admitted patients (those with an active inpatient_record).
    Groups drug prescriptions by patient encounter and creates one IMO per encounter.

    Args:
        doc: Delivery Note document
        method: Hook method name (on_submit)
    """
    if not doc.patient:
        return

    if doc.get("reference_doctype") != "Patient Encounter":
        return

    # Get encounter info from DN
    encounter_name = doc.get("reference_name")
    if not encounter_name:
        return

    # Check if patient is admitted
    inpatient_record = frappe.db.get_value("Patient", doc.patient, "inpatient_record")
    if not inpatient_record:
        return

    # Collect Drug Prescription refs from DN Items
    drug_prescriptions = []
    for item in doc.items:
        ref_dt = item.get("reference_doctype")
        ref_dn = item.get("reference_name")

        if ref_dt != "Drug Prescription" or not ref_dn:
            continue

        drug_prescriptions.append({
            "dp_name": ref_dn,
        })

    if not drug_prescriptions:
        return

    start_date = doc.posting_date or nowdate()

    imo = frappe.new_doc("Inpatient Medication Order")
    imo.patient = doc.patient
    imo.patient_name = doc.get("patient_name") or ""
    imo.inpatient_record = inpatient_record
    imo.patient_encounter = encounter_name
    imo.practitioner = doc.get("healthcare_practitioner") or ""
    imo.company = doc.company
    imo.start_date = start_date

    has_entries = False

    for dp_info in drug_prescriptions:
        dp_name = dp_info["dp_name"]

        dp = frappe.get_doc("Drug Prescription", dp_name)
        dosage_name = dp.get("dosage")
        period = dp.get("period")
        drug = dp.get("drug_code")
        drug_name = dp.get("drug_name")
        dosage_form = dp.get("dosage_form") or ""

        if not dosage_name or not period:
            # If no dosage/period, create a single entry for today
            imo.append("medication_orders", {
                "drug": drug,
                "drug_name": drug_name,
                "dosage": 1,
                "dosage_form": dosage_form,
                "date": start_date,
                "time": "08:00:00",
                "instructions": dp.get("comment") or "",
                "ref_doctype": "Drug Prescription",
                "ref_docname": dp_name,
            })
            has_entries = True
            continue

        dates = get_prescription_dates(period, start_date)
        dosage_doc = frappe.get_doc("Prescription Dosage", dosage_name)

        for date in dates:
            for dose in dosage_doc.dosage_strength:
                dose_value = dose.strength or 1

                dose_time = dose.strength_time
                if not dose_time:
                    dose_time = _get_default_dose_time(
                        dose.idx, len(dosage_doc.dosage_strength)
                    )

                imo.append("medication_orders", {
                    "drug": drug,
                    "drug_name": drug_name,
                    "dosage": dose_value,
                    "dosage_form": dosage_form,
                    "date": date,
                    "time": dose_time,
                    "instructions": dp.get("comment") or "",
                    "ref_doctype": "Drug Prescription",
                    "ref_docname": dp_name,
                })
                has_entries = True

    if not has_entries:
        return

    # Set end_date from the last entry
    if imo.medication_orders:
        imo.end_date = imo.medication_orders[-1].date

    try:
        imo.insert(ignore_permissions=True)
        imo.submit()

        frappe.msgprint(
            _(
                "Inpatient Medication Order {0} created and submitted"
                " from Delivery Note {1}"
            ).format(frappe.bold(imo.name), frappe.bold(doc.name)),
            alert=True,
        )
    except frappe.DuplicateEntryError:
        # IMO already exists for this encounter — skip silently
        frappe.log_error(
            title="IMO Creation: Duplicate",
            message=(
                f"IMO already exists for encounter {encounter_name}."
                f" Skipping creation from DN {doc.name}."
            ),
            reference_doctype="Delivery Note",
            reference_name=doc.name,
        )
    except Exception:
        frappe.log_error(
            title="IMO Creation Error",
            message=frappe.get_traceback(),
            reference_doctype="Delivery Note",
            reference_name=doc.name,
        )


def _get_default_dose_time(idx, total_doses):
    """Return a proportionally distributed time when strength_time is not set.

    Divides 24 hours equally by the number of doses per day, starting from
    06:00 (common hospital first-dose time).

    Examples:
        - 1x/day  → 06:00
        - 2x/day  → 06:00, 18:00  (every 12 hours)
        - 3x/day  → 06:00, 14:00, 22:00  (every 8 hours)
        - 4x/day  → 06:00, 12:00, 18:00, 00:00  (every 6 hours)
        - 6x/day  → 06:00, 10:00, 14:00, 18:00, 22:00, 02:00  (every 4 hours)

    Args:
        idx: 1-based index of the dose in the dosage strength list
        total_doses: Total number of doses per day

    Returns:
        Time string in HH:MM:SS format
    """
    if total_doses <= 0:
        return "06:00:00"

    # Calculate the equal interval in hours
    interval_hours = 24 / total_doses

    # Start from 06:00 (common hospital first-dose time), then space evenly
    start_hour = 6
    total_minutes = int((start_hour + (idx - 1) * interval_hours) * 60) % (24 * 60)

    hours = total_minutes // 60
    minutes = total_minutes % 60
    return f"{hours:02d}:{minutes:02d}:00"
