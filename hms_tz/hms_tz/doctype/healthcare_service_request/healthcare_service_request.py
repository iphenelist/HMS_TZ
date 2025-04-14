# Copyright (c) 2025, Aakvatech and contributors
# For license information, please see license.txt
import json
import frappe
from frappe import _
from frappe.query_builder import DocType
from frappe.utils import get_link_to_form
from frappe.model.document import Document
from hms_tz.nhif.api.healthcare_utils import get_item_rate, get_item_price
from hms_tz.nhif.api.patient_appointment import get_discount_percent


hsr = DocType("Healthcare Service Request")

class HealthcareServiceRequest(Document):
	def before_save(self):
		self.set_request_id()
		self.get_percent_covered()
		self.set_service_price_rate()

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

		if len(hsr_dupl) > 0:
			url = get_link_to_form(self.doctype, hsr_dupl[0].name)
			frappe.throw(
				f"Another Healthcare Service Request with the same Source Docname: <b>{self.source_docname}</b> already exists: <a href='{url}'><b>{hsr_dupl[0].name}</b></a>"
			)
	
	def set_request_id(self):
		for row in self.services:
			for d in self.payments:
				if (
					row.service_name == d.service_name and
					row.name != d.request_id
				):
					d.request_id = row.name
	
	@frappe.whitelist()
	def get_services(self):
		return set([d.service_name for d in self.services])
	
	def set_service_price_rate(self):
		for row in self.payments:
			if not row.service_name:
				continue

			if not row.price_list:
				frappe.throw("Please select price list on payment table, row: {row.idx}")
			
			item_rate_details = self.get_service_rate(row)

			row.rate = item_rate_details.get("item_rate")
			row.discount_applied = 1 if item_rate_details.get("discount_percent") > 0 else 0
			row.amount = (row.percent_covered / 100 * row.rate) * row.qty if row.percent_covered else row.rate * row.qty

	@frappe.whitelist()
	def get_service_rate(self, row_obj):
		row = None
		if isinstance(row_obj, str):
			row = frappe._dict(json.loads(row_obj))
		else:
			row = row_obj

		service_type = self.get_service_type(self, row)
		if not service_type:
			return {"item_rate": 0, "discount_percent": 0}
		
		item = frappe.get_cached_value(service_type, row.service_name, "item")
		if not item:
			frappe.throw(f"Item code for {service_type}: {row.service_name} was not found.<br>Please set the item code to proceed...")
		
		item_rate = 0
		discount_percent = 0

		if row.payment_type == 'Cash' and row.price_list:
			item_rate = get_item_price(
				item,
				row.price_list,
				self.company
			)

		elif row.payment_type == 'Insurance':
			if not row.insurance_subscription:
				frappe.throw("Insurance Subscription is required to get the item rate")

			if row.price_list:
				item_price_rate = get_item_price(
					item,
					row.price_list,
					self.company
				)
			else:
				item_price_rate = get_item_rate(
					item,
					self.company,
					row.insurance_subscription,
					row.insurance_company
				)

			# apply discount if it is available on Heathcare Insurance Company
			if row.insurance_company and "NHIF" not in row.insurance_company:
				discount_percent = get_discount_percent(row.insurance_company)
			
			item_rate = item_price_rate - (
				item_price_rate * (discount_percent / 100)
			)

		return {"item_rate": item_rate, "discount_percent": discount_percent}

	@frappe.whitelist()
	def get_coverage_plan(self, insurance_subscription):
		plan = frappe.get_cached_value("Healthcare Insurance Subscription", insurance_subscription, "healthcare_insurance_coverage_plan")
		if not plan:
			frappe.throw(f"Insurance Coverage Plan is not set for Insurance Subscription: {insurance_subscription}")
		
		return plan

	@frappe.whitelist()
	def get_percent_covered(self, item_obj=None):
		if item_obj:
			item = None
			if isinstance(item_obj, str):
				item = frappe._dict(json.loads(item_obj))
			else:
				item = item_obj
			
			if not item.service_name:
				return
			
			if "NHIF" not in item.insurance_company:
				return

			service_type = self.get_service_type(item)
			product_code = self.get_product_code(item)
			ref_code = get_item_refcode(service_type, item.service_name)

			percent_covered = frappe.get_cached_value(
				"NHIF Cost Sharing", {	
					"itemcode": ref_code,
					"productcode": product_code,
					"yearno": self.years_of_insurance
				}, "percentcovered"
			)

			return percent_covered
		
		else:
			for item in self.payments:
				if not item.service_name:
					return
				
				if "NHIF" not in item.insurance_company:
					continue
				
				service_type = self.get_service_type(item)
				product_code = self.get_product_code(item)
				ref_code = get_item_refcode(service_type, item.service_name)

				percent_covered = frappe.get_cached_value(
					"NHIF Cost Sharing", {	
						"itemcode": ref_code,
						"productcode": product_code,
						"yearno": self.years_of_insurance
					}, "percentcovered"
				)

				item.percent_covered = percent_covered

	def get_service_type(self, item):
		service_type = ''
		if item.request_id:
			service_type = frappe.get_cached_value("Healthcare Service Request Item", item.request_id, "service_type")

		else:
			for d in self.services:
				if item.service_name == d.service_name:
					service_type = d.service_type
					break
		
		return service_type
	
	def get_product_code(self, item):
		scheme_id = frappe.get_cached_value(
			"Healthcare Insurance Coverage Plan",
			item.payor_plan,
			"nhif_scheme_id"
		)
		product_code = frappe.get_cached_value(
			"NHIF Product", {
				"schemeid": scheme_id,
				"company": self.company,
				"healthcare_insurance_coverage_plan": item.payor_plan
			}, "nhif_product_code"
		)

		return product_code
		

@frappe.whitelist()
def create_service_request(doc_obj=None, data=None):
	doc = None
	services = []

	if not doc_obj and not data:
		frappe.throw("Please provide a valid document object or data")

	if data:
		data = json.loads(data)
		doc = frappe.get_doc(data.get("source_doctype"), data.get("source_docname"))
	else:
		doc = frappe._dict(json.loads(doc_obj))
	
	if doc.doctype == "Patient Encounter":
		services += get_encounter_services(doc)
	
	if len(services) == 0:
		return
	
	hsr = frappe.new_doc("Healthcare Service Request")
	hsr.patient = doc.patient
	hsr.appointment = doc.appointment,
	hsr.company = doc.company,
	hsr.practitioner = doc.practitioner
	hsr.source_doctype = doc.doctype
	hsr.source_docname = doc.name
	payment_type = 'Cash' if not doc.insurance_subscription else 'Insurance'
	hsr.payment_type = payment_type

	if doc.insurance_subscription:
		hsr.insurance_subscription = doc.insurance_subscription
		hsr.insurance_company = doc.insurance_company
	
	authorization_number, years_of_insurance = frappe.get_cached_value("Patient Appointment", doc.appointment, ["authorization_number", "years_of_insurance"])
	for d in services:
		hsr.append("services", d)

		ref_code = get_item_refcode(d.get("service_type"), d.get("service_name"))
		new_row = {
			"item_code": ref_code,
			"rate": d.get("rate"),
			"payment_type": payment_type,
			"price_list": d.get("price_list"),
			"insurance_subscription": doc.insurance_subscription,
			"insurance_company": doc.insurance_company,
			"payor_plan": doc.insurance_coverage_plan,
			"authorization_number": authorization_number,
			"years_of_insurance": years_of_insurance
		}
		
		new_row.update(d.copy())
		hsr.append("payments", new_row)

	hsr.insert(ignore_permissions=True)
	return hsr.name
		

def get_encounter_services(doc):
	services = []
	for item in doc.get("lab_test_prescription"):
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

	for item in doc.get("radiology_procedure_prescription"):
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

	for item in doc.get("procedure_prescription"):
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

	for item in doc.get("drug_prescription"):
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

	for item in doc.get("therapies"):
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
	item = frappe.get_cached_value(
		row.get("service_type"), row.get("service_name"), "item"
	)
	if not item:
		frappe.throw(f"Item code for {row.get('service_type')}: {row.get('service_name')} was not found.<br>Please set the item code to proceed...")

	item_price_rate, price_list = get_item_rate(
		item,
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


def get_item_refcode(service_type, service_name):
	item = frappe.get_cached_value(service_type, service_name, "item")
	
	code_list = frappe.db.get_all(
        "Item Customer Detail",
        filters={"parent": item, "customer_name": "NHIF"},
        fields=["ref_code"],
    )
	if len(code_list) == 0:
		frappe.throw(_(f"Item {item} has not NHIF Code Reference"))
	
	ref_code = code_list[0].ref_code
	if not ref_code:
		frappe.throw(_(f"Item {item} has not NHIF Code Reference"))
	
	return ref_code
