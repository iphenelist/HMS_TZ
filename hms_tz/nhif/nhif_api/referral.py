import json
import frappe
import requests
from frappe.utils import get_fullname
from hms_tz.nhif.doctype.nhif_response_log.nhif_response_log import add_log


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
        