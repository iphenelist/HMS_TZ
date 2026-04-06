# Copyright (c) 2026, Aakvatech Limited and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_to_date, getdate


class NursingSchedule(Document):
    def validate(self):
        self.calculate_end_date()
        self.validate_dates()
        self.validate_duplicate_nurse_shifts()

    def calculate_end_date(self):
        """Auto-calculate end_date based on start_date and frequency."""
        if not self.start_date or not self.frequency:
            return

        frequency_map = {
            "Daily": {"days": 0},
            "Weekly": {"days": 6},
            "Monthly": {"months": 1},
            "Quarterly": {"months": 3},
            "Bi-Yearly": {"months": 6},
            "Yearly": {"years": 1},
        }

        offset = frequency_map.get(self.frequency)
        if not offset:
            return

        if "days" in offset:
            self.end_date = add_to_date(getdate(self.start_date), days=offset["days"])
        elif "months" in offset:
            # Add months, then subtract 1 day to get the last day of the period
            self.end_date = add_to_date(
                getdate(self.start_date), months=offset["months"], days=-1
            )
        elif "years" in offset:
            self.end_date = add_to_date(
                getdate(self.start_date), years=offset["years"], days=-1
            )

    def validate_dates(self):
        """Ensure start_date is before or equal to end_date."""
        if self.start_date and self.end_date:
            if getdate(self.start_date) > getdate(self.end_date):
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
