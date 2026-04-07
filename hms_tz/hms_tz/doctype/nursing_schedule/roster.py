# Copyright (c) 2026, Aakvatech Limited and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import add_to_date, getdate


@frappe.whitelist()
def get_roster_data(company: str, start_date: str, end_date: str) -> dict:
    """Return nurses and their existing assignments for the given company and date range.

    Nurses fully on leave for the entire date range are excluded.
    For nurses with partial leave overlap, their leave dates are returned
    so the frontend can mark those cells as non-editable.

    Returns:
        dict with keys:
        - nurses: list of {name, practitioner_name, employee}
        - assignments: list of {nurse, assignment_date, assign_based_on,
          service_unit_type, service_unit, parent, name}
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

            # Calculate the overlap between leave period and roster range
            overlap_start = max(getdate(leave.from_date), roster_start)
            overlap_end = min(getdate(leave.to_date), roster_end)

            if nurse_name not in nurse_leave_dates:
                nurse_leave_dates[nurse_name] = []

            # Generate all leave dates within the overlap
            current = overlap_start
            while current <= overlap_end:
                date_str = current.strftime("%Y-%m-%d")
                if date_str not in nurse_leave_dates[nurse_name]:
                    nurse_leave_dates[nurse_name].append(date_str)
                current = add_to_date(current, days=1)

    # Calculate total roster days for full-leave exclusion
    total_roster_days = (roster_end - roster_start).days + 1

    # Exclude nurses whose leave covers the entire date range
    filtered_nurses = []
    for n in nurses:
        # leave_days = nurse_leave_dates.get(n.name, [])
        # if len(leave_days) >= total_roster_days:
        #     # Nurse is on leave for the entire range — exclude them
        #     nurse_leave_dates.pop(n.name, None)
        #     continue

        filtered_nurses.append(n)

    nurse_names = [n.name for n in filtered_nurses]

    # Get all assignments in the date range for these nurses
    assignments = []
    if nurse_names:
        assignments = frappe.db.get_all(
            "Nurse Schedule Detail",
            filters={
                "nurse": ["in", nurse_names],
                "assignment_date": ["between", [start_date, end_date]],
            },
            fields=[
                "name",
                "parent",
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
        "nurses": filtered_nurses,
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
    """Batch-save roster assignments.

    Each assignment dict should have:
    - nurse: str (Healthcare Practitioner name)
    - assignment_date: str (YYYY-MM-DD)
    - assign_based_on: str (Service Unit Type / Service Unit)
    - service_unit_type: str (optional)
    - service_unit: str (optional)
    - existing_name: str (optional - if editing an existing row)
    - action: str (add / edit / remove)

    This function finds or creates Nursing Schedule documents for the
    given company/start_date/end_date/frequency and updates their
    child table rows accordingly.
    """
    import json

    if isinstance(assignments, str):
        assignments = json.loads(assignments)

    if not assignments:
        return {"message": _("No assignments to save.")}

    # Find existing Nursing Schedule for this period, or create one
    existing_schedule = frappe.db.get_value(
        "Nursing Schedule",
        filters={
            "company": company,
            "start_date": start_date,
            "end_date": end_date,
            "docstatus": ["!=", 2],
        },
        fieldname="name",
    )

    if existing_schedule:
        schedule = frappe.get_doc("Nursing Schedule", existing_schedule)
    else:
        schedule = frappe.new_doc("Nursing Schedule")
        schedule.company = company
        schedule.frequency = frequency
        schedule.start_date = start_date
        schedule.end_date = end_date

    for assignment in assignments:
        action = assignment.get("action", "add")
        existing_name = assignment.get("existing_name")

        if action == "remove" and existing_name:
            # Remove the row from the child table
            schedule.assignments = [
                row for row in schedule.assignments if row.name != existing_name
            ]
            continue

        if action == "edit" and existing_name:
            # Find and update the existing row
            for row in schedule.assignments:
                if row.name == existing_name:
                    row.assign_based_on = assignment.get("assign_based_on", "")
                    row.service_unit_type = assignment.get("service_unit_type", "")
                    row.service_unit = assignment.get("service_unit", "")
                    break
            continue

        # action == "add"
        # Validate: no duplicate nurse + date
        duplicate = False
        for row in schedule.assignments:
            if (
                row.nurse == assignment.get("nurse")
                and str(row.assignment_date) == str(assignment.get("assignment_date"))
            ):
                duplicate = True
                break

        if duplicate:
            frappe.msgprint(
                _("Nurse {0} already has an assignment on {1}. Skipping.").format(
                    assignment.get("nurse"), assignment.get("assignment_date")
                ),
                alert=True,
            )
            continue

        schedule.append(
            "assignments",
            {
                "nurse": assignment.get("nurse"),
                "assignment_date": assignment.get("assignment_date"),
                "assign_based_on": assignment.get("assign_based_on", "Service Unit Type"),
                "service_unit_type": assignment.get("service_unit_type", ""),
                "service_unit": assignment.get("service_unit", ""),
            },
        )

    schedule.save(ignore_permissions=False)

    return {
        "message": _("Roster saved successfully."),
        "schedule_name": schedule.name,
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
