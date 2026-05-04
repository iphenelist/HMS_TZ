# Copyright (c) 2026, Aakvatech Limited and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class NursingSchedule(Document):
    def validate(self):
        self.validate_assignment_fields()
        self.validate_no_duplicate()

    def validate_assignment_fields(self):
        """Ensure the correct location field is filled based on assign_based_on."""
        if self.assign_based_on == "Service Unit" and not self.service_unit:
            frappe.throw(
                _("Service Unit is required when assigning based on Service Unit."),
                title=_("Missing Field"),
            )
        if self.assign_based_on == "Service Unit Type" and not self.service_unit_type:
            frappe.throw(
                _("Service Unit Type is required when assigning based on Service Unit Type."),
                title=_("Missing Field"),
            )

    def validate_no_duplicate(self):
        """Prevent duplicate: same nurse + same date + same location."""
        filters = {
            "nurse": self.nurse,
            "assignment_date": self.assignment_date,
            "name": ["!=", self.name],
            "docstatus": ["!=", 2],
        }

        existing = frappe.db.exists("Nursing Schedule", filters)
        if existing:
            frappe.throw(
                _("Nurse {0} already has an assignment on {1} ({2}).").format(
                    frappe.bold(self.nurse_name or self.nurse),
                    frappe.bold(str(self.assignment_date)),
                    existing,
                ),
                title=_("Duplicate Assignment"),
            )
