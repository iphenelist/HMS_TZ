import json
import frappe
import base64
import requests
from hms_tz.nhif.doctype.nhif_response_log.nhif_response_log import add_log


def get_visit_types():
    settings = frappe.db.get_all("HMS TZ Settings", filters={"enable_nhif_api": 1}, fields=["company"])
    if len(settings) == 0:
        return
    
    settings_doc = frappe.get_cached_doc("HMS TZ Settings", settings[0].company)

    token = settings_doc.get_nhif_token()

    url = f"{settings_doc.nhifservice_url}/api/Verification/GetVisitTypes"
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
    
    settings_doc = frappe.get_cached_doc("HMS TZ Settings", settings[0].company)

    token = settings_doc.get_nhif_token()

    url = f"{settings_doc.nhifservice_url}/api/Verification/GetCardVerifiers"
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


@frappe.whitelist()
def get_card_details_by_card_no(company, card_no, ref_doctype, ref_docname=None, settings_doc=None):
    if not settings_doc:
        settings_doc = frappe.get_cached_doc("HMS TZ Settings", company)

    token = settings_doc.get_nhif_token()

    url = f"{settings_doc.nhifservice_url}/api/Verification/GetCardDetails?cardNo={card_no}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    r = requests.request("Get", url, headers=headers, timeout=60)

    if r.status_code == 200:
        data = json.loads(r.text)
        add_log(
            request_type="GetCardDetails",
            request_url=url,
            request_header=headers,
            request_body="",
            response_data=data,
            status_code=r.status_code,
            ref_doctype=ref_doctype,
            ref_docname=ref_docname,
            card_no=card_no
        )
        member_picture = get_member_picture(company, card_no, ref_doctype, ref_docname, settings_doc)
        data["MemberPicture"] = member_picture
        return data
    else:
        add_log(
            request_type="GetCardDetails",
            request_url=url,
            request_header=headers,
            request_body="",
            response_data=r.text,
            status_code=r.status_code,
            ref_doctype=ref_doctype,
            ref_docname=ref_docname,
            card_no=card_no
        )
        data = json.loads(r.text)
        frappe.msgprint(
            title="NHIF API Error",
            msg=f"Failed to Fetch card details<br><br>Status Code: {r.status_code}<br>Response: <b>{data.get('reasonPhrase')}<b>",
            indicator="red"
        )
        return 'Error'


@frappe.whitelist()
def get_card_details_by_national_id(company, national_id, ref_doctype, ref_docname=None, settings_doc=None):
    if not settings_doc:
        settings_doc = frappe.get_cached_doc("HMS TZ Settings", company)

    token = settings_doc.get_nhif_token()

    url = f"{settings_doc.nhifservice_url}/api/Verification/GetardDetailsByNIN?nationalID={national_id}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    r = requests.request("Get", url, headers=headers, timeout=60)

    if r.status_code == 200:
        data = json.loads(r.text)
        add_log(
            request_type="GetardDetailsByNIN",
            request_url=url,
            request_header=headers,
            request_body="",
            response_data=data,
            status_code=r.status_code,
            ref_doctype=ref_doctype,
            ref_docname=ref_docname,
            card_no=national_id
        )
        member_picture = get_member_picture(company, data.get("CardNo"), ref_doctype, ref_docname, settings_doc)
        data["MemberPicture"] = member_picture
        return data
    else:
        add_log(
            request_type="GetardDetailsByNIN",
            request_url=url,
            request_header=headers,
            request_body="",
            response_data=r.text,
            status_code=r.status_code,
            ref_doctype=ref_doctype,
            ref_docname=ref_docname,
            card_no=national_id
        )
        data = json.loads(r.text)
        frappe.msgprint(
            title="NHIF API Error",
            msg=f"Failed to Fetch card details<br><br>Status Code: {r.status_code}<br>Response: <b>{data.get('message')}<b>",
            indicator="red"
        )
        return 'Error'


@frappe.whitelist()
def get_member_picture(company, card_no, ref_doctype, ref_docname, settings_doc=None):
    if not settings_doc:
        settings_doc = frappe.get_cached_doc("HMS TZ Settings", company)

    token = settings_doc.get_nhif_token()

    url = f"{settings_doc.nhifservice_url}/api/Verification/GetMemberPicture?CardNo={card_no}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    r = requests.request("Get", url, headers=headers, timeout=60)

    if r.status_code == 200:
        add_log(
            request_type="GetMemberPicture",
            request_url=url,
            request_header=headers,
            request_body="",
            response_data=r.text,
            status_code=r.status_code,
            ref_doctype=ref_doctype,
            ref_docname=ref_docname,
            card_no=card_no
        )

        mime_type = None
        base64_image = r.text
        decoded_data = base64.b64decode(base64_image)
    
        if decoded_data.startswith(b'\xFF\xD8\xFF'):
            mime_type = "image/jpeg"  # JPEG
        elif decoded_data.startswith(b'\x89PNG\r\n\x1a\n'):
            mime_type = "image/png"   # PNG
        elif decoded_data.startswith(b'GIF87a') or decoded_data.startswith(b'GIF89a'):
            mime_type = "image/gif"   # GIF
        elif decoded_data.startswith(b'RIFF') and decoded_data[8:12] == b'WEBP':
            mime_type = "image/webp"  # WEBP
        elif decoded_data.startswith(b'\x42\x4D'):
            mime_type = "image/bmp"   # BMP
        else:
            mime_type = "application/octet-stream"

        prefixed_base64 = f"data:{mime_type};base64,{base64_image}"
        return prefixed_base64
    else:
        add_log(
            request_type="GetMemberPicture",
            request_url=url,
            request_header=headers,
            request_body="",
            response_data=r.text,
            status_code=r.status_code,
            ref_doctype=ref_doctype,
            ref_docname=ref_docname,
            card_no=card_no
        )
        return None