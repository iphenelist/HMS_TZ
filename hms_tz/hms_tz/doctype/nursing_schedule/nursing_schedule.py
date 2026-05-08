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
