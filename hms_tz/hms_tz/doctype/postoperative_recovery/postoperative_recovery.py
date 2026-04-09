# Copyright (c) 2026, Aakvatech and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class PostoperativeRecovery(Document):
    def before_submit(self):
        self.validate_discharge_criteria()

    def validate_discharge_criteria(self):
        """Validate Aldrete score meets minimum before discharge."""
        if self.status in ("Discharged to Ward", "Discharged Home"):
            if not self.discharge_criteria_met:
                frappe.throw(
                    _("Please confirm that discharge criteria have been met before discharging the patient.")
                )

            total_score = sum(flt(row.score) for row in (self.recovery_scores or []))
            total_max = sum(flt(row.max_score) for row in (self.recovery_scores or []))

            if total_max > 0 and total_score < (total_max * 0.7):
                frappe.msgprint(
                    _("Warning: Total recovery score ({0}/{1}) is below 70% threshold. "
                      "Please confirm patient is safe for discharge.").format(
                        total_score, total_max
                    ),
                    alert=True,
                    indicator="orange",
                )
