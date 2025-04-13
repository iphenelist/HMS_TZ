# Copyright (c) 2022, Aakvatech and contributors
# For license information, please see license.txt

import frappe
import json
import requests
from frappe.utils import nowdate, flt
from frappe.model.document import Document
from hms_tz.nhif.nhif_api.patient_claim import get_submitted_claims

class NHIFClaimReconciliation(Document):
	def before_save(self):
		self.posting_date = nowdate()
		
	def validate_reqd_fields(self):
		for fieldname in ["company", "claim_year", "claim_month"]:
			if not self.get(fieldname):
				frappe.throw(frappe.bold(f"{fieldname} is required"))
	
	def before_submit(self):
		self.posting_date = nowdate()
		get_submitted_claims(self)
	

