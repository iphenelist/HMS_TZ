# Copyright (c) 2022, Aakvatech and contributors
# For license information, please see license.txt

import frappe
import json
import requests
from frappe.utils import nowdate, flt
from frappe.model.document import Document

class NHIFClaimReconciliation(Document):
	def validate(self):
		if not self.posting_date: 
			self.posting_date = nowdate()
		
	def validate_reqd_fields(self):
		for fieldname in ["company", "claim_year", "claim_month"]:
			if not self.get(fieldname):
				frappe.throw(frappe.bold(f"{fieldname} is required"))
	
	def before_submit(self):
		if self.status == "Pending":
			frappe.throw("Cannot submit a pending reconciliation")

