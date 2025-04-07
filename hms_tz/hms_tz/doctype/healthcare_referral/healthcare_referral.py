# Copyright (c) 2025, Aakvatech and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import now_datetime
from frappe.model.document import Document

class HealthcareReferral(Document):
	def before_save(self):
		self.posting_date = now_datetime()
		self.patient_type_code = "IN" if frappe.get_cached_value("Patient", self.patient, "inpatient_record") else "OUT"


	def before_submit(self):
		self.posting_date = now_datetime()



