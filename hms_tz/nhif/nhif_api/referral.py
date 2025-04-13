import json
import frappe
import requests
from frappe.utils import get_fullname
from hms_tz.nhif.doctype.nhif_response_log.nhif_response_log import add_log


def create_referral(doc):
    """
    Creates a referral to NHIF based on the type of referral.
    """

    if doc.referral_type == "Form 2C/2E":
        return create_service_referral(doc)
    elif doc.referral_type == "Treatment": 
        return create_treatment_referral(doc)
    else:
        frappe.throw("Invalid Referral Type")


def create_treatment_referral(doc):
    payload = {
        "cardNo": doc.card_no or doc.national_id,
        "authorizationNo": doc.authorization_no,
        "fullName": doc.patient_name,
        "gender": doc.gender,
        "referralDate": doc.referral_date,
        "practitionerNo": doc.practitioner_no,
        "practitionersRemarks": doc.reason_for_referral,
        "fromFacilityCode": doc.source_facility_code,
        "toFacilityCode": doc.referrer_facility_code,
        "diagnosis": doc.referring_diagnosis,
        "createdBy": get_fullname(frappe.session.user),
    }

    payload = json.dumps(payload)

    settings_doc = frappe.get_cached_doc("HMS TZ Settings", doc.source_facility)

    token = settings_doc.get_nhif_token()

    url = f"{settings_doc.nhifservice_url}/api/Referrals/CreateTreatmentReferral"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    r = requests.request("Post", url, data=payload, headers=headers, timeout=60)
    if r.status_code != 200:
        add_log(
            request_type="CreateTreatmentReferral",
            request_url=url,
            request_header=headers,
            request_body=payload,
            response_data=r.text,
            status_code=r.status_code,
            company=settings_doc.name,
            ref_doctype=doc.doctype,
            ref_docname=doc.name
        )

    else:
        data = json.loads(r.text)
        add_log(
            request_type="CreateTreatmentReferral",
            request_url=url,
            request_header=headers,
            request_body=payload,
            response_data=data,
            status_code=r.status_code,
            company=settings_doc.name,
            ref_doctype=doc.doctype,
            ref_docname=doc.name
        )

        # TODO: update response values to Healthcare Referral doc
        
        doc.save(ignore_permissions=True)
        if doc.docstatus == 0:
            doc.submit()
        
        doc.reload()

        return True

def create_service_referral(doc):
    diseases = []
    services = []
    for disease in doc.diagnosis:
        diseases.append({
            "diseaseCode": get_disease_code(disease.disease_code),
            "status": disease.status
        })
    
    for service in doc.services:
          services.append({
            "itemCode": service.item_code,
            "itemQuantity": service.quantity,
            "approvalRefNo": service.approval_ref_no,
            "notes": service.notes
        })
          
    payload = {
        "authorizationNo": doc.authorization_no,
        "firstName": doc.first_name,
        "lastName": doc.last_name,
        "gender": doc.gender,
        "dateOfBirth": doc.dob,
        "telephoneNo": doc.mobile_no,
        "patientFileNo": doc.patient,
        "practitionerNo": doc.practitioner_no,
        "attendanceDate": doc.attendance_date,
        "patientTypeCode": doc.patient_type_code,
        "facilityCode": doc.referrer_facility_code,
        "createdBy": get_fullname(frappe.session.user),
        "diseases": diseases,
        "services": services,
    }

    payload = json.dumps(payload)

    settings_doc = frappe.get_cached_doc("HMS TZ Settings", doc.source_facility)

    token = settings_doc.get_nhif_token()

    url = f"{settings_doc.nhifservice_url}/api/Referrals/CreateServiceReferral"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    r = requests.request("Post", url, data=payload, headers=headers, timeout=60)
    if r.status_code != 200:
        add_log(
            request_type="CreateServiceReferral",
            request_url=url,
            request_header=headers,
            request_body=payload,
            response_data=r.text,
            status_code=r.status_code,
            company=settings_doc.name,
            ref_doctype=doc.doctype,
            ref_docname=doc.name
        )

    else:
        data = json.loads(r.text)
        add_log(
            request_type="CreateServiceReferral",
            request_url=url,
            request_header=headers,
            request_body=payload,
            response_data=data,
            status_code=r.status_code,
            company=settings_doc.name,
            ref_doctype=doc.doctype,
            ref_docname=doc.name
        )

        # TODO: update response values to Healthcare Referral doc
        
        doc.save(ignore_permissions=True)
        if doc.docstatus == 0:
            doc.submit()
        
        doc.reload()

        return True


def get_disease_code(code):
	# Convert the ICD code of CDC to NHIF
	disease_code = None
	if code and len(code) > 3 and "." not in code:
		disease_code = code[:3] + "." + (code[3:4] or "0")
	elif code and len(code) <= 5 and "." in code:
		disease_code = code
	else:
		disease_code = code[:3]
    
	return disease_code
