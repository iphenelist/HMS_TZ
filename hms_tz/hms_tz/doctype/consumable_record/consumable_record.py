# Copyright (c) 2026, Aakvatech and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class ConsumableRecord(Document):
    def before_save(self):
        self.set_inpatient_record()
        self.calculate_totals()

    def on_submit(self):
        self.update_status("Dispensed")

    def set_inpatient_record(self):
        """Auto-set inpatient_record if patient has an active admission."""
        if not self.inpatient_record and self.patient:
            inpatient_record = frappe.db.get_value(
                "Patient", self.patient, "inpatient_record"
            )
            if inpatient_record:
                self.inpatient_record = inpatient_record

    def calculate_totals(self):
        """Calculate amount per item and total amount."""
        total = 0
        for item in self.items:
            qty = flt(item.qty_used) or flt(item.qty_dispensed) or flt(item.qty_requested)
            item.amount = flt(qty * flt(item.rate))
            total += flt(item.amount)
        self.total_amount = total

    def update_status(self, status: str):
        self.db_set("status", status)

    def validate_quantities(self):
        """Ensure qty_returned does not exceed qty_dispensed."""
        for item in self.items:
            if flt(item.qty_returned) > flt(item.qty_dispensed):
                frappe.throw(
                    _("Row {0}: Qty Returned ({1}) cannot exceed Qty Dispensed ({2})").format(
                        item.idx, item.qty_returned, item.qty_dispensed
                    )
                )
            if flt(item.qty_used) > flt(item.qty_dispensed):
                frappe.throw(
                    _("Row {0}: Qty Used ({1}) cannot exceed Qty Dispensed ({2})").format(
                        item.idx, item.qty_used, item.qty_dispensed
                    )
                )
