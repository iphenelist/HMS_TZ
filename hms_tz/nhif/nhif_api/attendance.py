import json
import base64
import frappe
import requests
from frappe.utils import nowdate
from hms_tz.nhif.doctype.nhif_response_log.nhif_response_log import add_log


@frappe.whitelist()
def login_practitioner(
    fingerprint,
    fpcode,
    settings_doc=None
):
    fingerprint_data = fingerprint.replace("-", "+").replace("_", "/")
    image_data = base64.b64encode(fingerprint_data.encode('utf-8')).decode('utf-8')

    practitioner = frappe.get_cached_value(
        "Healthcare Practitioner", 
        {'user_id': frappe.session.user}, 
        ["tz_mct_code", "national_id", "hms_tz_company", "name"],
        as_dict=True
    )
    if not practitioner:
        frappe.throw(f"No healthcare practitioner found for user id: {frappe.session.user}, Please set user id to healthcare practitioner")
        
    if not practitioner.national_id:
        frappe.throw(f"Please set National ID for a practitioner: <b>{practitioner.name}</b>")
    
    payload = {
        "nationalID": practitioner.national_id,
        "practitionerNo": practitioner.tz_mct_code,
        "biometricMethod": "Fingerprint",
        "fpCode": fpcode,
        "imageData": image_data
    }

    payload = json.dumps(payload)

    if not settings_doc:
        settings_doc = frappe.get_cached_doc("HMS TZ Settings", practitioner.hms_tz_company)
    
    url = f"{settings_doc.nhifservice_url}/api/Attendance/LoginPractitioner"
    
    token = settings_doc.get_nhif_token()

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    r = requests.request("Post", url, headers=headers, data=payload, timeout=60)
    data = json.loads(r.text)

    if r.status_code == 200:
        add_log(
            request_type='LoginPractitioner',
            request_url=url,
            request_header=headers,
            request_body=payload,
            response_data=data,
            status_code=r.status_code,
            ref_doctype='Healthcare Practitioner',
            ref_docname=practitioner.name,
            card_no=practitioner.national_id
        )
        frappe.set_value(
            "Healthcare Practitioner",
            practitioner.name,
            "date_loggedin_to_nhif",
            nowdate(),
            update_modified=False
        )
        return data

    else:
        add_log(
            request_type='LoginPractitioner',
            request_url=url,
            request_header=headers,
            request_body=payload,
            response_data=data,
            status_code=r.status_code,
            ref_doctype='Healthcare Practitioner',
            ref_docname=practitioner.name,
            card_no=practitioner.national_id
        )
        frappe.msgprint(
            title="NHIF API Error",
            msg=f"Failed to LoginPractitioner<br><br>Status Code: {r.status_code}<br>Response: <b>{data.get('errors') or data.get('message')}<b>",
            indicator="red"
        )
        return 'Error'
    

@frappe.whitelist()
def logout_practitioner(settings_doc=None):
    practitioner = frappe.get_cached_value(
        "Healthcare Practitioner", 
        {'user_id': frappe.session.user}, 
        ["tz_mct_code", "national_id", "hms_tz_company", "name"],
        as_dict=True
    )
    if not practitioner:
        frappe.throw(f"No healthcare practitioner found for user id: {frappe.session.user}, Please set user id to healthcare practitioner")
    
    if not settings_doc:
        settings_doc = frappe.get_cached_doc("HMS TZ Settings", practitioner.hms_tz_company)
    
    payload = {
        "practitionerNo": practitioner.tz_mct_code,
        "facilityCode": settings_doc.facility_code
    }

    payload = json.dumps(payload)
    
    url = f"{settings_doc.nhifservice_url}/api/Attendance/LogoutPractitioner"
    
    token = settings_doc.get_nhif_token()

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    r = requests.request("Post", url, headers=headers, data=payload, timeout=60)
    data = json.loads(r.text)

    if r.status_code == 200:
        add_log(
            request_type='LogoutPractitioner',
            request_url=url,
            request_header=headers,
            request_body=payload,
            response_data=data,
            status_code=r.status_code,
            ref_doctype='Healthcare Practitioner',
            ref_docname=practitioner.name,
            # card_no=practitioner.national_id
        )
        frappe.set_value(
            "Healthcare Practitioner",
            practitioner.name,
            "date_loggedin_to_nhif",
            "",
            update_modified=False
        )
        return data

    else:
        add_log(
            request_type='LogoutPractitioner',
            request_url=url,
            request_header=headers,
            request_body=payload,
            response_data=data,
            status_code=r.status_code,
            ref_doctype='Healthcare Practitioner',
            ref_docname=practitioner.name,
            # card_no=practitioner.national_id
        )
        frappe.msgprint(
            title="NHIF API Error",
            msg=f"Failed to LogoutPractitioner<br><br>Status Code: {r.status_code}<br>Response: <b>{data.get('errors') or data.get('message')}<b>",
            indicator="red"
        )
        return 'Error'
    


