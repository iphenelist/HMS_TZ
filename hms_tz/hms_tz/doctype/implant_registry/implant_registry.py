# Copyright (c) 2026, Aakvatech and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import random_string


class ImplantRegistry(Document):
    def before_insert(self):
        self.generate_barcode()

    def before_save(self):
        self.validate_expiry()

    def generate_barcode(self):
        """Auto-generate a unique barcode for the implant."""
        if not self.barcode:
            self.barcode = f"IMP-{random_string(10).upper()}"

    def validate_expiry(self):
        """Warn if the implant is expired."""
        if self.expiry_date and self.implant_date:
            from frappe.utils import getdate

            if getdate(self.expiry_date) < getdate(self.implant_date):
                frappe.throw(
                    _("Implant has expired (Expiry Date: {0}). Cannot proceed with implantation.").format(
                        self.expiry_date
                    )
                )
