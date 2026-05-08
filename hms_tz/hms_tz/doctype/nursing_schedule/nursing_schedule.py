# Copyright (c) 2026, Aakvatech Limited and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class NursingSchedule(Document):
    def validate(self):
        self.validate_assignment_fields()
        self.set_shift_times()
        self.validate_no_duplicate()

    def on_submit(self):
        self.create_shift_assignment()

    def on_update_after_submit(self):
        self.update_shift_assignment()

    def on_cancel(self):
        self.maybe_cancel_shift_assignment()

    def validate_assignment_fields(self):
        """Ensure the correct location field is filled based on assign_based_on."""
        if self.assign_based_on == "Room" and not self.room:
            frappe.throw(
                _("Room is required when assigning based on Room."),
                title=_("Missing Field"),
            )
        if self.assign_based_on == "Ward" and not self.ward:
            frappe.throw(
                _("Ward is required when assigning based on Ward."),
                title=_("Missing Field"),
            )

    def set_shift_times(self):
        """Auto-fill shift start/end times from the linked Shift Type."""
        if self.shift_type:
            shift = frappe.get_cached_value(
                "Shift Type",
                self.shift_type,
                ["start_time", "end_time"],
                as_dict=True,
            )
            if shift:
                self.shift_start_time = shift.start_time
                self.shift_end_time = shift.end_time

    def validate_no_duplicate(self):
        """Prevent duplicate: same nurse + same date + same shift type."""
        filters = {
            "nurse": self.nurse,
            "assignment_date": self.assignment_date,
            "shift_type": self.shift_type,
            "name": ["!=", self.name],
            "docstatus": ["!=", 2],
        }

        existing = frappe.db.exists("Nursing Schedule", filters)
        if existing:
            frappe.throw(msg=_(f"Nurse {self.nurse_name} already has a {self.shift_type} shift on {str(self.assignment_date)} ({existing})."), title=_("Duplicate Assignment"))

    def _is_auto_shift_enabled(self) -> bool:
        """Check if auto Shift Assignment creation is enabled for this company."""

        return bool(
            frappe.db.get_value(
                "HMS TZ Setting",
                self.company,
                "auto_create_shift_assignment_from_nursing_roster",
            )
        )

    def _get_employee(self) -> str | None:
        """Get the Employee linked to this nurse (Healthcare Practitioner)."""

        return frappe.db.get_value(
            "Healthcare Practitioner", self.nurse, "employee"
        )

    def create_shift_assignment(self):
        """Create and submit a Shift Assignment when this Nursing Schedule is submitted."""
        if not self._is_auto_shift_enabled():
            return

        employee = self._get_employee()
        if not employee:
            frappe.msgprint(
                _(f"Shift Assignment not created: Nurse {self.nurse_name} has no linked Employee."),
                alert=True,
                indicator="orange",
            )
            return

        sa = frappe.new_doc("Shift Assignment")
        sa.employee = employee
        sa.shift_type = self.shift_type
        sa.company = self.company
        sa.start_date = self.assignment_date
        sa.end_date = self.assignment_date
        sa.insert(ignore_permissions=True)
        sa.submit()

        self.db_set("shift_assignment", sa.name, update_modified=False)

    def update_shift_assignment(self):
        """Update the linked Shift Assignment if key fields changed."""

        if not self.shift_assignment:
            return

        if not frappe.db.exists("Shift Assignment", self.shift_assignment):
            return

        sa = frappe.get_doc("Shift Assignment", self.shift_assignment)
        if sa.docstatus != 1:
            return

        needs_save = False

        if str(sa.start_date) != str(self.assignment_date):
            sa.start_date = self.assignment_date
            sa.end_date = self.assignment_date
            needs_save = True

        if sa.shift_type != self.shift_type:
            sa.shift_type = self.shift_type
            needs_save = True

        if needs_save:
            sa.db_update()

    def cancel_shift_assignment(self):
        """Cancel the linked Shift Assignment when this Nursing Schedule is cancelled."""
        if not self.shift_assignment:
            return

        if not frappe.db.exists("Shift Assignment", self.shift_assignment):
            return

        sa = frappe.get_doc("Shift Assignment", self.shift_assignment)
        if sa.docstatus == 1:
            sa.flags.ignore_permissions = True
            sa.cancel()
