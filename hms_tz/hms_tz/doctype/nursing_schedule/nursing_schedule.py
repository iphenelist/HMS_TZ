# Copyright (c) 2026, Aakvatech Limited and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class NursingSchedule(Document):
    def validate(self):
        self.validate_dates()
        self.validate_duplicate_nurse_shifts()

    def validate_dates(self):
        """Ensure start_date is before or equal to end_date."""
        if self.start_date and self.end_date:
            if self.start_date > self.end_date:
                frappe.throw(
                    _("Start Date {0} cannot be after End Date {1}").format(
                        frappe.bold(self.start_date), frappe.bold(self.end_date)
                    ),
                    title=_("Invalid Dates"),
                )

    def validate_duplicate_nurse_shifts(self):
        """Warn if the same nurse appears in conflicting shifts in the same schedule."""
        seen: dict = {}
        for row in self.shifts or []:
            # Check for same nurse, shift type, and assignment target
            key = (row.nurse, row.shift_type, row.shift_based_on, row.service_unit if row.shift_based_on == 'Service Unit' else row.service_unit_type)
            if key in seen:
                frappe.throw(
                    _(
                        "Row #{0}: Nurse <b>{1}</b> is already assigned to the same "
                        "shift/unit combination in Row #{2}."
                    ).format(row.idx, row.nurse, seen[key]),
                    title=_("Duplicate Shift Assignment"),
                )
            seen[key] = row.idx
