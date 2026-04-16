# Copyright (c) 2026, Aakvatech and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_time


class AnesthesiaRecord(Document):
    def before_save(self):
        self.validate_timing()

    def validate_timing(self):
        """Ensure end_time is after start_time if both are set."""
        if self.start_time and self.end_time:
            if get_time(self.end_time) < get_time(self.start_time):
                frappe.throw(
                    _("End Time cannot be before Start Time")
                )
