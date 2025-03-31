import json
import frappe
import requests
from hms_tz.nhif.doctype.nhif_response_log.nhif_response_log import add_log


@frappe.whitelist()
def get_admission_types(company=None, caller=None):
    if not company:
        settings = frappe.db.get_all("HMS TZ Settings", filters={"enable_nhif_api": 1}, fields=["company"])
        company = settings[0].company
    
    if not company:
        return
    
    settings_doc = frappe.get_cached_doc("HMS TZ Settings", company)

    token = settings_doc.get_nhif_token()

    url = f"{settings_doc.nhif_claim_url}/api/Admissions/GetAdmissionTypes"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    r = requests.request("Get", url, headers=headers, timeout=60)
    if r.status_code != 200:
        add_log(
            request_type="GetAdmissionTypes",
            request_url=url,
            request_header=headers,
            request_body="",
            response_data=r.text,
            status_code=r.status_code,
            company=settings_doc.name,
            ref_doctype="Healthcare Admission Type",
        )

    else:
        data = json.loads(r.text)
        add_log(
            request_type="GetAdmissionTypes",
            request_url=url,
            request_header=headers,
            request_body="",
            response_data=data,
            status_code=r.status_code,
            company=settings_doc.name,
            ref_doctype="Healthcare Admission Type",
        )

        if len(data) == 0:
            return
        
        for row in data:
            admission = frappe.db.get_value("Healthcare Admission Type", {"admission_type_name": row["AdmissionTypeName"]}, "name")
            if admission:
                has_changed = False
                doc = frappe.get_doc("Healthcare Admission Type", admission)

                if doc.admission_type_name != row["AdmissionTypeName"]:
                    doc.admission_type_name = row["AdmissionTypeName"]
                    has_changed = True
                
                if doc.alias != row["Alias"]:
                    doc.alias = row["Alias"]
                    has_changed = True
                
                if doc.admission_type_id != row["AdmissionTypeID"]:
                    doc.admission_type_id = row["AdmissionTypeID"]
                    has_changed = True
                
                if has_changed:
                    doc.save(ignore_permissions=True)
                
            else:
                doc = frappe.new_doc("Healthcare Admission Type")
                doc.admission_type_name = row["AdmissionTypeName"]
                doc.alias = row["Alias"]
                doc.admission_type_id = row["AdmissionTypeID"]

                doc.save(ignore_permissions=True)
        
        if company and caller == 'Front End':
            frappe.msgprint("successfully fetched Admission Types", alert=True, indicator="green")


@frappe.whitelist()
def get_discharge_types(company=None, caller=None):
    if not company:
        settings = frappe.db.get_all("HMS TZ Settings", filters={"enable_nhif_api": 1}, fields=["company"])
        company = settings[0].company
    
    if not company:
        return
    
    settings_doc = frappe.get_cached_doc("HMS TZ Settings", company)

    token = settings_doc.get_nhif_token()

    url = f"{settings_doc.nhif_claim_url}/api/Admissions/GetDischargeTypes"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    r = requests.request("Get", url, headers=headers, timeout=60)
    if r.status_code != 200:
        add_log(
            request_type="GetDischargeTypes",
            request_url=url,
            request_header=headers,
            request_body="",
            response_data=r.text,
            status_code=r.status_code,
            company=settings_doc.name,
            ref_doctype="Healthcare Discharge Type",
        )

    else:
        data = json.loads(r.text)
        add_log(
            request_type="GetDischargeTypes",
            request_url=url,
            request_header=headers,
            request_body="",
            response_data=data,
            status_code=r.status_code,
            company=settings_doc.name,
            ref_doctype="Healthcare Discharge Type",
        )

        if len(data) == 0:
            return
        
        for row in data:
            discharge_type = frappe.db.get_value("Healthcare Discharge Type", {"discharge_type_name": row["DischargeTypeName"]}, "name")
            if discharge_type:
                has_changed = False
                doc = frappe.get_doc("Healthcare Discharge Type", discharge_type)

                if doc.discharge_type_name != row["DischargeTypeName"]:
                    doc.discharge_type_name = row["DischargeTypeName"]
                    has_changed = True
                
                if doc.alias != row["Alias"]:
                    doc.alias = row["Alias"]
                    has_changed = True
                
                if doc.discharge_type_id != row["DischargeTypeID"]:
                    doc.discharge_type_id = row["DischargeTypeID"]
                    has_changed = True
                
                if has_changed:
                    doc.save(ignore_permissions=True)
                
            else:
                doc = frappe.new_doc("Healthcare Discharge Type")
                doc.admission_type_name = row["DischargeTypeName"]
                doc.alias = row["Alias"]
                doc.admission_type_id = row["DischargeTypeID"]

                doc.save(ignore_permissions=True)
        
        if company and caller == 'Front End':
            frappe.msgprint("successfully fetched Discharge Types", alert=True, indicator="green")

