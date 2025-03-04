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


@frappe.whitelist()
def create_service_request(doc):
	services = []

	doc = frappe._dict(json.loads(doc))
	
	if doc.doctype == "Patient Encounter":
		services += get_encounter_services(doc)
	
	if len(services) > 0:
		hsr = frappe.new_doc("Healthcare Service Request")
		hsr.patient = doc.patient
		hsr.appointment = doc.appointment,
		hsr.company = doc.company,
		hsr.practitioner = doc.practitioner
		hsr.source_doctype = doc.doctype
		hsr.source_docname = doc.name
		hsr.payment_type = 'Cash' if not doc.insurance_subscription else 'Insurance'

		if doc.insurance_subscription:
			hsr.insurance_subscription = doc.insurance_subscription
			hsr.insurance_company = doc.insurance_company
		
		for d in services:
			hsr.append("services", d)

		hsr.insert(ignore_permissions=True)
		

def get_encounter_services(doc):
	services = []
	for item in doc.lab_test_prescription:
		item = frappe._dict(item)
		if (
			item.prescribe == 1
			or item.is_cancelled == 1
			or item.is_not_available_inhouse == 1
		):
			continue

		row = {
			"service_type": "Lab Test Template",
			"service_name": item.lab_test_code,
			"qty": 1,
			"ref_doctype": item.doctype,
			"ref_docname": item.name
		}

		new_row = set_service_amounts(
			row,
			doc.company,
			doc.insurance_company,
			doc.insurance_subscription
		)
		services.append(new_row)

	for item in doc.radiology_procedure_prescription:
		if (
			item.prescribe == 1
			or item.is_cancelled == 1
			or item.is_not_available_inhouse == 1
		):
			continue
		
		row = {
			"service_type": "Radiology Examination Template",
			"service_name": item.radiology_examination_template,
			"qty": 1,
			"ref_doctype": item.doctype,
			"ref_docname": item.name
		}
		new_row = set_service_amounts(
			row,
			doc.company,
			doc.insurance_company,
			doc.insurance_subscription
		)
		services.append(new_row)

	for item in doc.procedure_prescription:
		if (
			item.prescribe == 1
			or item.is_cancelled == 1
			or item.is_not_available_inhouse == 1
		):
			continue
		
		row = {
			"service_type": "Clinical Procedure Template",
			"service_name": item.procedure,
			"qty": 1,
			"ref_doctype": item.doctype,
			"ref_docname": item.name
		}
		new_row = set_service_amounts(
			row,
			doc.company,
			doc.insurance_company,
			doc.insurance_subscription
		)
		services.append(new_row)

	for item in doc.drug_prescription:
		if (
			item.prescribe == 1
			or item.is_cancelled == 1
			or item.is_not_available_inhouse == 1
		):
			continue
		
		row = {
			"service_type": "Medication",
			"service_name": item.drug_code,
			"qty": item.quantity,
			"ref_doctype": item.doctype,
			"ref_docname": item.name
		}
		new_row = set_service_amounts(
			row,
			doc.company,
			doc.insurance_company,
			doc.insurance_subscription
		)
		services.append(new_row)

	for item in doc.therapies:
		if (
			item.prescribe == 1
			or item.is_cancelled == 1
			or item.is_not_available_inhouse == 1
		):
			continue
		
		row = {
			"service_type": "Therapy Type",
			"service_name": item.therapy_type,
			"qty": 1,
			"ref_doctype": item.doctype,
			"ref_docname": item.name
		}
		new_row = set_service_amounts(
			row,
			doc.company,
			doc.insurance_company,
			doc.insurance_subscription
		)
		services.append(new_row)
	
	return services


def set_service_amounts(
	row,
	company,
	insurance_company,
	insurance_subscription
):
    # apply discount if it is available on Heathcare Insurance Company
	discount_percent = 0
	if insurance_company and "NHIF" not in insurance_company:
		discount_percent = get_discount_percent(insurance_company)

	item_rate = 0
	item_code = frappe.get_cached_value(
		row.get("service_type"), row.get("service_name"), "item"
	)
	if not item_code:
		frappe.throw(f"Item code for {row.get('service_type')}: {row.get('service_name')} was not found.<br>Please set the item code to proceed...")

	item_price_rate, price_list = get_item_rate(
		item_code,
		company,
		insurance_subscription,
		insurance_company,
		for_service_request=True
	)

	item_rate = item_price_rate - (
		item_price_rate * (discount_percent / 100)
	)

	if discount_percent > 0:
		row["discount_applied"] = 1

	row["rate"] = item_rate
	row["amount"] = row.get("qty") * item_rate
	row["price_list"] = price_list

	return row