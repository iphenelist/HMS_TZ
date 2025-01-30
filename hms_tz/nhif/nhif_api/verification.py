import json
import frappe
import requests
from hms_tz.nhif.doctype.nhif_response_log.nhif_response_log import add_log


def get_visit_types():
    settings = frappe.db.get_all("HMS TZ Settings", filters={"enable_nhif_api": 1}, fields=["company"])
    if len(settings) == 0:
        return
    
    setting_doc = frappe.get_cached_doc("HMS TZ Settings", settings[0].company)

    token = setting_doc.get_nhif_token()

    url = f"{setting_doc.nhifservice_url}/api/Verification/GetVisitTypes"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    r = requests.request("Get", url, headers=headers, timeout=60)
    if r.status_code == 200:
        data = json.loads(r.text)
        add_log(
            request_type="GetVisitTypes",
            request_url=url,
            request_header=headers,
            request_body="",
            response_data=data,
            status_code=r.status_code
        )

        for visit in data:
            try:
                if frappe.db.exists("Appointment Type", visit.get("VisitTypeName"), cache=True):
                    has_changed = False
                    appointment_type_doc = frappe.get_cached_doc("Appointment Type", visit.get("VisitTypeName"))

                    if appointment_type_doc.visit_type_id != visit.get("VisitTypeID"):
                        has_changed = True
                        appointment_type_doc.visit_type_id = visit.get("VisitTypeID")

                    if appointment_type_doc.required_input != visit.get("RequiredInput"):
                        has_changed = True
                        appointment_type_doc.required_input = visit.get("RequiredInput")
                        
                    if appointment_type_doc.visit_type_name_alias != visit.get("Alias"):
                        has_changed = True
                        appointment_type_doc.visit_type_name_alias = visit.get("Alias")
                        
                    if appointment_type_doc.requires_remarks != visit.get("RequiresRemarks"):
                        has_changed = True
                        appointment_type_doc.requires_remarks = visit.get("RequiresRemarks")
                        
                    if appointment_type_doc.requires_referral_no != visit.get("RequiresReferralNo"):
                        has_changed = True
                        appointment_type_doc.requires_referral_no = visit.get("RequiresReferralNo")

                    if appointment_type_doc.maximum_visit_per_month != visit.get("MaximumVisitPerMonth"):
                        has_changed = True
                        appointment_type_doc.maximum_visit_per_month = visit.get("MaximumVisitPerMonth")

                    if appointment_type_doc.description != visit.get("Description"):
                        has_changed = True
                        appointment_type_doc.description = visit.get("Description")
                    
                    if has_changed:
                        appointment_type_doc.save(ignore_permissions=True)
                
                else:
                    appointment_type_doc = frappe.new_doc("Appointment Type")
                    appointment_type_doc.appointment_type = visit.get("VisitTypeName")
                    if "Referral" in visit.get("VisitTypeName"):
                        appointment_type_doc.source = "External Referral" 
                    else:
                        appointment_type_doc.source = "Direct"
                    
                    appointment_type_doc.visit_type_id = visit.get("VisitTypeID")
                    appointment_type_doc.required_input = visit.get("RequiredInput")
                    appointment_type_doc.visit_type_name_alias = visit.get("Alias")
                    appointment_type_doc.requires_remarks = visit.get("RequiresRemarks")
                    appointment_type_doc.requires_referral_no = visit.get("RequiresReferralNo")
                    appointment_type_doc.maximum_visit_per_month = visit.get("MaximumVisitPerMonth")
                    appointment_type_doc.description = visit.get("Description")
                    appointment_type_doc.save(ignore_permissions=True)
                    frappe.db.commit()

            except:
                traceback = frappe.get_traceback()
                frappe.log_error(
                    title="GetVisitTypes",
                    message=traceback
                )
    else:
        add_log(
            request_type="GetVisitTypes",
            request_url=url,
            request_header=headers,
            request_body="",
            response_data=r.text,
            status_code=r.status_code,
        )


def get_card_verifier():
    settings = frappe.db.get_all("HMS TZ Settings", filters={"enable_nhif_api": 1}, fields=["company"])
    if len(settings) == 0:
        return
    
    setting_doc = frappe.get_cached_doc("HMS TZ Settings", settings[0].company)

    token = setting_doc.get_nhif_token()

    url = f"{setting_doc.nhifservice_url}/api/Verification/GetCardVerifiers"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    r = requests.request("Get", url, headers=headers, timeout=60)

    if r.status_code == 200:
        data = json.loads(r.text)
        add_log(
            request_type="GetCardVerifiers",
            request_url=url,
            request_header=headers,
            request_body="",
            response_data=data,
            status_code=r.status_code
        )
        for record in data:
            try:
                if frappe.db.exists("Healthcare Card Verifier", str(record.get("verifierName")), cache=True):
                    has_changed = False
                    hcv_doc = frappe.get_cached_doc("Healthcare Card Verifier", record.get("verifierName"))
                    
                    if hcv_doc.verifier_id != record.get("verifierID"):
                        has_changed = True
                        hcv_doc.verifier_id = record.get("verifierID")
                    
                    hcv_doc.card_types = []
                    
                    for row in record.get("cardTypes"):
                        has_changed = True
                        hcv_doc.append("card_types", {
                            "card_type_id": row.get("cardTypeID"),
                            "card_type_name": row.get("cardTypeName")
                        })
                    
                    if has_changed:
                        hcv_doc.save(ignore_permissions=True)
                
                else:
                    hcv_doc = frappe.new_doc("Healthcare Card Verifier")
                    hcv_doc.verifier_name = record.get("verifierName")
                    hcv_doc.verifier_id = record.get("verifierID")
                    
                    for row in record.get("cardTypes"):
                        hcv_doc.append("card_types", {
                            "card_type_id": row.get("cardTypeID"),
                            "card_type_name": row.get("cardTypeName")
                        })
                    
                    hcv_doc.save(ignore_permissions=True)
                    hcv_doc.reload()
            except:
                traceback = frappe.get_traceback()
                frappe.log_error(
                    title="CardVerifiers",
                    message=traceback
                )
    else:
        add_log(
            request_type="GetCardVerifiers",
            request_url=url,
            request_header=headers,
            request_body="",
            response_data=r.text,
            status_code=r.status_code,
        )
