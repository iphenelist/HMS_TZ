import json
import frappe
import base64
import requests
from hms_tz.nhif.doctype.nhif_scheme.nhif_scheme import add_scheme
from hms_tz.nhif.doctype.nhif_product.nhif_product import add_product
from hms_tz.nhif.doctype.nhif_response_log.nhif_response_log import add_log
from hms_tz.nhif.api.patient_appointment import update_insurance_subscription


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
            status_code=r.status_code,
            company=settings_doc.name,
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
            company=settings_doc.name,
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
            status_code=r.status_code,
            company=settings_doc.name,
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
            company=settings_doc.name,
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
            company=settings_doc.name,
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
            company=settings_doc.name,
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
            company=settings_doc.name,
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
            company=settings_doc.name,
            ref_doctype=ref_doctype,
            ref_docname=ref_docname,
            card_no=national_id
        )
        response = ""
        if r.text:
            data = json.loads(r.text)
            response = data.get('message')

        frappe.msgprint(
            title="NHIF API Error",
            msg=f"Failed to Fetch card details<br><br>Status Code: {r.status_code}<br>Response: <b>{response}<b>",
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
            company=settings_doc.name,
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
            company=settings_doc.name,
            ref_doctype=ref_doctype,
            ref_docname=ref_docname,
            card_no=card_no
        )
        return None


@frappe.whitelist()
def get_patient_detail(card_no, company, ref_doctype, ref_docname=None, settings_doc=None):
    if not settings_doc:
        settings_doc = frappe.get_cached_doc("HMS TZ Settings", company)

    if not settings_doc.enable_nhif_api:
        frappe.msgprint("Please Enable NHIF API to proceed..")
        return;
    
    if not card_no:
        return;
    
    url = f"{settings_doc.nhifservice_url}/api/Verification/GetPatientDetails?CardNo={card_no}"

    token = settings_doc.get_nhif_token()
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    r = requests.request("Get", url, headers=headers, timeout=60)
    if r.status_code == 200:
        data = json.loads(r.text)
        add_log(
            request_type="GetPatientDetails",
            request_url=url,
            request_header=headers,
            request_body="",
            response_data=data,
            status_code=r.status_code,
            company=settings_doc.name,
            ref_doctype=ref_doctype,
            ref_docname=ref_docname,
            card_no=card_no
        )

        return data
    else:
        add_log(
            request_type="GetPatientDetails",
            request_url=url,
            request_header=headers,
            request_body="",
            response_data=r.text,
            status_code=r.status_code,
            company=settings_doc.name,
            ref_doctype=ref_doctype,
            ref_docname=ref_docname,
            card_no=card_no
        )
        return None


@frappe.whitelist()
def authorize_patient(
    insurance_subscription,
    appointment_type,
    company,
    card_no,
    national_id,
    fingerprint,
    fpcode,
    biometric_method,
    practitioner,
    referral_no="",
    remarks="",
    settings_doc=None,
    ref_doctype='Patient Appointment',
    ref_docname=None
):
    if not settings_doc:
        settings_doc = frappe.get_cached_doc("HMS TZ Settings", company)
    
    if not settings_doc.enable_nhif_api:
        frappe.msgprint("Please Enable NHIF API to proceed..")
        return

    if not card_no and not national_id:
        frappe.msgprint(f"Please set Card No or National ID in Healthcare Insurance Subscription {insurance_subscription}")
        return
    
    fingerprint_data = fingerprint.replace("-", "+").replace("_", "/")
    image_data = base64.b64encode(fingerprint_data.encode('utf-8')).decode('utf-8')
    
    visit_type_id = frappe.get_cached_value("Appointment Type", appointment_type, "visit_type_id")

    url = ""
    payload = {}
    request_type = ""
    card_type_info = frappe.get_cached_value(
        "Healthcare Insurance Subscription", insurance_subscription, 
        ['verifier_id', 'card_type_id', 'card_type_name'],
        as_dict=True
    )
    
    if (
        card_type_info and (
            not card_type_info.verifier_id or
            card_type_info.verifier_id == 'NHIF'
        )
    ):
        request_type = 'AuthorizeCard'
        url = f"{settings_doc.nhifservice_url}/api/Verification/AuthorizeCard"
        payload.update({
            "cardNo": card_no,
            "biometricMethod": biometric_method,
            "nationalID": national_id,
            "fpCode": fpcode,
            "imageData": image_data,
            "visitTypeID": visit_type_id,
            "referralNo": referral_no,
            "remarks": remarks
        })

    elif (
        card_type_info and
        card_type_info.verifier_id in ('WCF', 'ZHSF')
    ):
        request_type = 'VerifyCard'
        url = f"{settings_doc.nhifservice_url}/api/Verification/VerifyCard"
        payload.update({
            "cardNo": card_no,
            "verifierID": card_type_info.verifier_id,
            "cardTypeID": card_type_info.card_type_id,
            "biometricMethod": biometric_method,
            "fpCode": fpcode,
            "imageData": image_data,
            "visitTypeID": visit_type_id,
            "referralNo": referral_no,
            "remarks": remarks
        })

    payload = json.dumps(payload)
    
    token = settings_doc.get_nhif_token()

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    r = requests.request("Post", url, headers=headers, data=payload, timeout=60)
    if r.status_code == 200:
        auth_data = json.loads(r.text)
        add_log(
            request_type=request_type,
            request_url=url,
            request_header=headers,
            request_body=payload,
            response_data=auth_data,
            status_code=r.status_code,
            company=settings_doc.name,
            ref_doctype=ref_doctype,
            ref_docname=ref_docname,
            card_no=card_no or national_id
        )

        if auth_data.get("AuthorizationStatus") != "ACCEPTED":
            frappe.throw(title=auth_data.get("AuthorizationStatus"), msg=auth_data["Remarks"])
        
        frappe.msgprint(auth_data["Remarks"], alert=True)
        add_scheme(auth_data.get("SchemeID"), auth_data.get("SchemeName"))
        add_product(company, auth_data.get("ProductCode"), auth_data.get("ProductName"))
        update_insurance_subscription(insurance_subscription, auth_data, company)

        reference_data = get_poc_reference_no(
            "Registration",
            practitioner,
            image_data,
            fpcode,
            biometric_method,
            company,
            card_no or national_id,
            appointment_id=ref_docname,
            authorization_no=auth_data.get("AuthorizationNo"),
            settings_doc=settings_doc,
            ref_doctype=ref_doctype,
            ref_docname=ref_docname
        )

        auth_data.update(reference_data)
        return auth_data
    else:
        auth_data = json.loads(r.text)
        add_log(
            request_type=request_type,
            request_url=url,
            request_header=headers,
            request_body=payload,
            response_data=auth_data,
            status_code=r.status_code,
            company=settings_doc.name,
            ref_doctype=ref_doctype,
            ref_docname=ref_docname,
            card_no=card_no or national_id
        )
        frappe.msgprint(
            title="NHIF API Error",
            msg=f"Failed to AuthorizePatient<br><br>Status Code: {r.status_code}<br>Response: <b>{data.get('errors') or data.get('message')}<b>",
            indicator="red"
        )
        return 'Error'


@frappe.whitelist()
def get_poc_reference_no(
    point_of_care,
    practitioner,
    fingerprint,
    fpcode,
    biometric_method,
    company,
    card_no=None,
    appointment_id=None,
    authorization_no=None,
    settings_doc=None,
    ref_doctype=None,
    ref_docname=None
):
    if not settings_doc:
        settings_doc = frappe.get_cached_doc("HMS TZ Settings", company)
    
    point_of_care_id = frappe.get_cached_value("Healthcare Points of Care", {'name': ['like', point_of_care]}, "point_of_care_id")
    practitioner_no = frappe.get_cached_value("Healthcare Practitioner", practitioner, 'tz_mct_code')

    appointment_info=None
    if appointment_id:
        appointment_info = frappe.get_cached_value(
            "Patient Appointment", appointment_id, 
            ["authorization_number", "coverage_plan_card_number", "national_id"],
            as_dict=True
        )

    image_data = None
    if ref_doctype != "Patient Appointment":
        fingerprint_data = fingerprint.replace("-", "+").replace("_", "/")
        image_data = base64.b64encode(fingerprint_data.encode('utf-8')).decode('utf-8')
    else:
        image_data = fingerprint

    payload = {
        "pointOfCareID": point_of_care_id,
        "authorizationNo": authorization_no or appointment_info.authorization_number,
        "practitionerNo": practitioner_no,
        "biometricMethod": biometric_method,
        "fpCode": fpcode,
        "imageData": image_data
    }

    payload = json.dumps(payload)
    url = f"{settings_doc.nhifservice_url}/api/Verification/GeneratePOCReferenceNo"

    token = settings_doc.get_nhif_token()

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    r = requests.request("Post", url, headers=headers, data=payload, timeout=60)
    if r.status_code == 200:
        data = json.loads(r.text)
        add_log(
            request_type="GeneratePOCReferenceNo",
            request_url=url,
            request_header=headers,
            request_body=payload,
            response_data=data,
            status_code=r.status_code,
            company=settings_doc.name,
            ref_doctype=ref_doctype,
            ref_docname=ref_docname,
            card_no=card_no or appointment_info.coverage_plan_card_number or appointment_info.national_id
        )
        return data
    else:
        data = json.loads(r.text)
        add_log(
            request_type="GeneratePOCReferenceNo",
            request_url=url,
            request_header=headers,
            request_body=payload,
            response_data=data,
            status_code=r.status_code,
            company=settings_doc.name,
            ref_doctype=ref_doctype,
            ref_docname=ref_docname,
            card_no=card_no or appointment_info.coverage_plan_card_number or appointment_info.national_id
        )
        frappe.throw(
            title="NHIF API Error",
            msg=f"Failed to Fetch POC Reference No<br><br>Status Code: {r.status_code}<br>Response: <b>{data.get('errors') or data.get('message')}<b>",
        )
