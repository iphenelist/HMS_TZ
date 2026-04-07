# Copyright (c) 2026, Aakvatech Limited and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import add_to_date, getdate, today


@frappe.whitelist()
def get_roster_data(company: str, start_date: str, end_date: str) -> dict:
    """Return nurses and their existing assignments for the given company and date range.

    Nurses fully on leave for the entire date range are kept visible but
    their leave dates are marked so the frontend can render them as non-editable.

    Returns:
        dict with keys:
        - nurses: list of {name, practitioner_name, employee}
        - assignments: list of {name, nurse, nurse_name, assignment_date,
          assign_based_on, service_unit_type, service_unit}
        - nurse_leave_dates: dict mapping nurse name → list of leave date strings
    """
    if not company or not start_date or not end_date:
        frappe.throw(_("Company, Start Date, and End Date are required."))

    nurses = frappe.db.get_all(
        "Healthcare Practitioner",
        filters={
            "practitioner_role": "Nurse",
            "hms_tz_company": company,
            "status": "Active",
        },
        fields=["name", "practitioner_name", "employee"],
        order_by="practitioner_name asc",
    )

    # Build employee → nurse mapping for leave lookups
    employee_nurse_map = {}
    employee_ids = []
    for n in nurses:
        if n.employee:
            employee_nurse_map[n.employee] = n.name
            employee_ids.append(n.employee)

    # Query approved leaves overlapping the roster date range
    nurse_leave_dates: dict[str, list[str]] = {}
    roster_start = getdate(start_date)
    roster_end = getdate(end_date)

    if employee_ids:
        leaves = frappe.db.get_all(
            "Leave Application",
            filters={
                "employee": ["in", employee_ids],
                "status": "Approved",
                "from_date": ["<=", end_date],
                "to_date": [">=", start_date],
            },
            fields=["employee", "from_date", "to_date"],
        )

        for leave in leaves:
            nurse_name = employee_nurse_map.get(leave.employee)
            if not nurse_name:
                continue

            overlap_start = max(getdate(leave.from_date), roster_start)
            overlap_end = min(getdate(leave.to_date), roster_end)

            if nurse_name not in nurse_leave_dates:
                nurse_leave_dates[nurse_name] = []

            current = overlap_start
            while current <= overlap_end:
                date_str = current.strftime("%Y-%m-%d")
                if date_str not in nurse_leave_dates[nurse_name]:
                    nurse_leave_dates[nurse_name].append(date_str)
                current = add_to_date(current, days=1)

    nurse_names = [n.name for n in nurses]

    # Get assignments from Nursing Schedule (individual records)
    assignments = []
    if nurse_names:
        assignments = frappe.db.get_all(
            "Nursing Schedule",
            filters={
                "nurse": ["in", nurse_names],
                "assignment_date": ["between", [start_date, end_date]],
                "docstatus": ["!=", 2],
            },
            fields=[
                "name",
                "nurse",
                "nurse_name",
                "assignment_date",
                "assign_based_on",
                "service_unit_type",
                "service_unit",
            ],
            order_by="assignment_date asc",
        )

    return {
        "nurses": nurses,
        "assignments": assignments,
        "nurse_leave_dates": nurse_leave_dates,
    }


@frappe.whitelist()
def save_roster_assignments(
    company: str,
    start_date: str,
    end_date: str,
    frequency: str,
    assignments: list | str,
) -> dict:
    """Batch-save roster assignments as individual Nursing Schedule records.

    Each assignment dict should have:
    - nurse: str (Healthcare Practitioner name)
    - assignment_date: str (YYYY-MM-DD)
    - assign_based_on: str (Service Unit Type / Service Unit)
    - service_unit_type: str (optional)
    - service_unit: str (optional)
    - existing_name: str (optional - for editing/removing existing records)
    - action: str (add / edit / remove)

    New records are created and immediately submitted.
    Edits to existing (submitted) records are applied directly to the database.
    Modifications to records with past assignment dates are blocked.
    """
    import json

    if isinstance(assignments, str):
        assignments = json.loads(assignments)

    if not assignments:
        return {"message": _("No assignments to save.")}

    today_date = getdate(today())
    created = 0
    updated = 0
    removed = 0

    for assignment in assignments:
        action = assignment.get("action", "add")
        existing_name = assignment.get("existing_name")
        assignment_date = getdate(assignment.get("assignment_date"))

        # Block modifications to past-date assignments
        if assignment_date < today_date:
            frappe.msgprint(
                _("Cannot modify assignment for {0} — date has already passed.").format(
                    frappe.bold(str(assignment_date))
                ),
                alert=True,
            )
            continue

        if action == "remove" and existing_name:
            # Cancel the submitted record
            doc = frappe.get_doc("Nursing Schedule", existing_name)
            if doc.docstatus == 1:
                doc.cancel()
            frappe.delete_doc("Nursing Schedule", existing_name, force=True)
            removed += 1
            continue

        if action == "edit" and existing_name:
            # Direct DB update on the submitted record
            update_values = {
                "assign_based_on": assignment.get("assign_based_on", ""),
            }
            if assignment.get("assign_based_on") == "Service Unit Type":
                update_values["service_unit_type"] = assignment.get("service_unit_type", "")
                update_values["service_unit"] = ""
            else:
                update_values["service_unit"] = assignment.get("service_unit", "")
                update_values["service_unit_type"] = ""

            frappe.db.set_value(
                "Nursing Schedule",
                existing_name,
                update_values,
                update_modified=True,
            )
            updated += 1
            continue

        # action == "add" — create and submit a new individual record
        # Check for duplicate first
        existing = frappe.db.exists(
            "Nursing Schedule",
            {
                "nurse": assignment.get("nurse"),
                "assignment_date": assignment.get("assignment_date"),
                "docstatus": ["!=", 2],
            },
        )
        if existing:
            frappe.msgprint(
                _("Nurse {0} already has an assignment on {1}. Skipping.").format(
                    assignment.get("nurse"), assignment.get("assignment_date")
                ),
                alert=True,
            )
            continue

        doc = frappe.new_doc("Nursing Schedule")
        doc.company = company
        doc.frequency = frequency
        doc.nurse = assignment.get("nurse")
        doc.assignment_date = assignment.get("assignment_date")
        doc.assign_based_on = assignment.get("assign_based_on", "Service Unit Type")
        doc.service_unit_type = assignment.get("service_unit_type", "")
        doc.service_unit = assignment.get("service_unit", "")
        doc.insert(ignore_permissions=False)
        doc.submit()
        created += 1

    frappe.db.commit()

    parts = []
    if created:
        parts.append(_("{0} created").format(created))
    if updated:
        parts.append(_("{0} updated").format(updated))
    if removed:
        parts.append(_("{0} removed").format(removed))

    return {
        "message": _("Roster saved: {0}.").format(", ".join(parts)) if parts else _("No changes made."),
    }


@frappe.whitelist()
def get_service_options(company: str) -> dict:
    """Return service unit types and service units for dropdowns."""
    service_unit_types = frappe.db.get_all(
        "Healthcare Service Unit Type",
        filters={"disabled": 0},
        fields=["name"],
        order_by="name asc",
    )

    service_units = frappe.db.get_all(
        "Healthcare Service Unit",
        filters={"is_group": 0, "disabled": 0, "company": company},
        fields=["name", "service_unit_type"],
        order_by="name asc",
    )

    return {
        "service_unit_types": [s.name for s in service_unit_types],
        "service_units": [{"name": s.name, "type": s.service_unit_type} for s in service_units],
    }
