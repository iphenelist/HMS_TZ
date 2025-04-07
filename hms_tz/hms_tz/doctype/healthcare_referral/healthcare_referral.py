# Copyright (c) 2025, Aakvatech and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import now_datetime
from frappe.model.document import Document
from hms_tz.hms_tz.doctype.healthcare_service_request.healthcare_service_request import get_item_refcode


class HealthcareReferral(Document):
	def before_save(self):
		self.posting_date = now_datetime()
		self.patient_type_code = "IN" if frappe.get_cached_value("Patient", self.patient, "inpatient_record") else "OUT"


	def before_submit(self):
		self.posting_date = now_datetime()


	@frappe.whitelist()
	def get_diagnosis(self):
		"""Get diagnosis from encounter"""
		
		if not self.encounter:
			return
		
		diagnosis = []
		unique_diagnosis = []
		encounter_doc = frappe.get_doc("Patient Encounter", self.encounter)
		for d in encounter_doc.patient_encounter_final_diagnosis:
			diagnosis.append({
				"status": "Final",
				"disease_code": d.code,
				"description": d.description
			})
			unique_diagnosis.append(d.code)
		
		for d in encounter_doc.patient_encounter_preliminary_diagnosis:
			if d.code not in unique_diagnosis:
				diagnosis.append({
					"status": "Provisional",
					"disease_code": d.code,
					"description": d.description
				})
				unique_diagnosis.append(d.code)

		return reversed(diagnosis)

