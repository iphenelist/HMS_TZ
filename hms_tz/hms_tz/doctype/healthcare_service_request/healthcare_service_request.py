# Copyright (c) 2025, Aakvatech and contributors
# For license information, please see license.txt
import json
import frappe
from frappe.query_builder import DocType
from frappe.model.document import Document
from hms_tz.nhif.api.healthcare_utils import get_item_rate
from hms_tz.nhif.api.patient_appointment import get_discount_percent


hsr = DocType("Healthcare Service Request")

class HealthcareServiceRequest(Document):
	def validate(self):
		self.validate_duplicate()

	def validate_duplicate(self):
		if not self.source_doctype and not self.source_docname:
			return
		
		hsr_dupl = (
			frappe.qb.from_(hsr)
			.select(hsr.name)
			.where(
				(hsr.name != self.name)
				& (hsr.source_doctype == self.source_doctype)
				& (hsr.source_docname == self.source_docname)
			)
		).run(as_dict=True)

		if len(hsr_dupl) > 1:
			url = get_link_to_form(self.doctype, hsr_dupl[0].name)
			frappe.throw(
				f"Another Healthcare Service Request with the same Source Docname: <b>{self.source_docname}</b> already exists: <a href='{url}'><b>{hsr_dupl[0].name}</b></a>"
			)
