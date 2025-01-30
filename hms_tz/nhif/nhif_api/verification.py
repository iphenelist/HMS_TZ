import json
import frappe
import requests
from hms_tz.nhif.doctype.nhif_response_log.nhif_response_log import add_log


@frappe.whitelist()
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

    r = requests.request("Get", url, headers=headers, timeout=5)
    r.raise_for_status()

    data = json.loads(r.text)

    if data:
        add_log(
            request_type="VisitTypes",
            request_url=url,
            request_header=headers,
            request_body="",
            response_data=data,
            status_code=r.status_code
        )

        for visit in data:
            try:
                if frappe.db.exists("Appointment Type", str(visit.get("VisitTypeName")), cache=True):
                    appointment_type_doc = frappe.get_cached_doc("Appointment Type", visit.get("VisitTypeName"))

                    if appointment_type_doc.visit_type_id != visit.get("VisitTypeID"):
                        appointment_type_doc.visit_type_id = visit.get("VisitTypeID")

                    if appointment_type_doc.required_input != visit.get("RequiredInput"):
                        appointment_type_doc.required_input = visit.get("RequiredInput")
                        
                    if appointment_type_doc.visit_type_name_alias != visit.get("Alias"):
                        appointment_type_doc.visit_type_name_alias = visit.get("Alias")
                        
                    if appointment_type_doc.requires_remarks != visit.get("RequiresRemarks"):
                        appointment_type_doc.requires_remarks = visit.get("RequiresRemarks")
                        
                    if appointment_type_doc.requires_referral_no != visit.get("RequiresReferralNo"):
                        appointment_type_doc.requires_referral_no = visit.get("RequiresReferralNo")

                    if appointment_type_doc.maximum_visit_per_month != visit.get("MaximumVisitPerMonth"):
                        appointment_type_doc.maximum_visit_per_month = visit.get("MaximumVisitPerMonth")

                    if appointment_type_doc.description != visit.get("Description"):
                        appointment_type_doc.description = visit.get("Description")
                    
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
