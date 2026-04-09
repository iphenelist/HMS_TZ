# Copyright (c) 2026, Aakvatech and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class PreoperativeAssessment(Document):
    def before_save(self):
        self.validate_clearance_checks()

    def validate_clearance_checks(self):
        """Warn if marking as Cleared without all checks complete."""
        if self.status != "Cleared for Surgery":
            return

        required_checks = [
            "fasting_status_verified",
            "consent_signed",
            "site_marking_verified",
        ]

        missing = []
        for check in required_checks:
            if not self.get(check):
                missing.append(frappe.unscrub(check))

        if missing:
            frappe.throw(
                _("Cannot mark as 'Cleared for Surgery'. The following checks are incomplete: {0}").format(
                    ", ".join(missing)
                )
            )
