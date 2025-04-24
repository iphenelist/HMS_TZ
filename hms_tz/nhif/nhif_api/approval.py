import json
import frappe
import requests
from hms_tz.nhif.nhif_api.referral import get_disease_code
from frappe.utils import get_datetime, nowdate, get_fullname
from hms_tz.nhif.doctype.nhif_response_log.nhif_response_log import add_log
from hms_tz.hms_tz.doctype.healthcare_service_request.healthcare_service_request import (
    get_item_refcode, get_item_rate
)


@frappe.whitelist()
def get_service_approval(
    ref_doctype,
    ref_docname,
    service_type,
    service_name,
    qty=1
):
    if not ref_doctype or not ref_docname:
        frappe.throw("Document Type and Document Name are required")

    doc = frappe.get_doc(ref_doctype, ref_docname)

    settings_doc = frappe.get_cached_doc("HMS TZ Settings", doc.company)

    payload = get_request_approval_payload(
        doc,
        settings_doc.facility_code,
        service_type,
        service_name,
        qty
    )

    payload = json.dumps(payload)

    token = settings_doc.get_nhif_token()

    url = f"{settings_doc.nhifservice_url}/api/Approvals/RequestApproval"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    r = requests.request("POST", url, headers=headers, data=payload, timeout=120)

    if r.status_code != 200:
        add_log(
            request_type="RequestApproval",
            request_url=url,
            request_header=headers,
            request_body=payload,
            response_data=r.text,
            status_code=r.status_code,
            company=settings_doc.name,
            ref_doctype=ref_doctype,
            ref_docname=ref_docname,
        )

        return {
            "status": "error",
            "message": f"Service approval request failed with status code {r.status_code}",
            "data": r.text,
        }
    
    else:
        data = json.loads(r.text)

        add_log(
            request_type="RequestApproval",
            request_url=url,
            request_header=headers,
            request_body=payload,
            response_data=data,
            status_code=r.status_code,
            company=settings_doc.name,
            ref_doctype=ref_doctype,
            ref_docname=ref_docname,
        )

        return {
            "status": "success",
            "message": "Service approval request successful",
            "data": data,
        }


@frappe.whitelist()
def update_service_approval(
    ref_doctype,
    ref_docname,
    service_type,
    service_name,
    qty=1
):
    if not ref_doctype or not ref_docname:
        frappe.throw("Document Type and Document Name are required")
    
    doc = frappe.get_doc(ref_doctype, ref_docname)

    settings_doc = frappe.get_cached_doc("HMS TZ Settings", doc.company)

    payload = get_update_approval_payload(
        doc,
        settings_doc.facility_code,
        service_type,
        service_name,
        qty
    )

    payload = json.dumps(payload)

    token = settings_doc.get_nhif_token()

    url = f"{settings_doc.nhifservice_url}/api/Approvals/UpdateApprovalRequest"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    r = requests.request("POST", url, headers=headers, data=payload, timeout=120)

    if r.status_code != 200:
        add_log(
            request_type="UpdateApprovalRequest",
            request_url=url,
            request_header=headers,
            request_body=payload,
            response_data=r.text,
            status_code=r.status_code,
            company=settings_doc.name,
            ref_doctype=ref_doctype,
            ref_docname=ref_docname,
        )
        return {
            "status": "error",
            "message": f"Service approval update failed with status code {r.status_code}",
            "data": r.text,
        }
    else:
        data = json.loads(r.text)
        add_log(
            request_type="UpdateApprovalRequest",
            request_url=url,
            request_header=headers,
            request_body=payload,
            response_data=data,
            status_code=r.status_code,
            company=settings_doc.name,
            ref_doctype=ref_doctype,
            ref_docname=ref_docname,
        )
        return {
            "status": "success",
            "message": "Service approval update successful",
            "data": data,
        }


def get_request_approval_payload(
    doc,
    facility_code,
    service_type,
    service_name,
    qty=1
):
    patient_doc = frappe.get_cached_doc("Patient", doc.patient)
    appointment_info = get_appointment_details(doc.appointment)

    clinical_notes = frappe.get_cached_value("Patient Encounter", doc.ref_docname, "examination_detail") or ""

    practitioner_no = frappe.get_cached_value("Healthcare Practitioner", doc.practitioner, "tz_mct_code")

    payload = {
        "firstName": patient_doc.first_name,
        "lastName": patient_doc.last_name,
        "gender": doc.get("hms_tz_patient_sex") or patient_doc.sex,
        "telephoneNo": patient_doc.mobile,
        "clinicalNotes": clinical_notes,
        "dateOfBirth": patient_doc.dob,
        "authorizationNo": appointment_info.authorization_number,
        "facilityPatientFileNumber": doc.patient,
        "attendanceDate": appointment_info.appointment_date,
        "serviceDate": nowdate(),
        "expiryDate": "",
        "sourceFacilityCode": facility_code,
        "practitionerNo": practitioner_no,
        "prescribedBy": doc.practitioner,
        "requestedBy": doc.practitioner,
        "createdBy": doc.practitioner,
        "approvalDiseases": get_approval_diseases(doc),
        "authorizedItems": get_authorized_items(
            doc,
            service_type,
            service_name, 
            appointment_info.years_of_insurance,
            qty=qty
        ),
        "approvalSupportingDocuments": [] # TODO: add supporting documents
    }

    #   "approvalSupportingDocuments": [
    #     {
    #       "documentTypeID": 0,
    #       "documentDetails": "string",
    #       "filePath": "string",
    #       "documentData": "string",
    #       "fileType": "string"
    #     }
    #   ]

    return payload


def get_approval_diseases(doc):
    diseases = []
    
    encounter_doc = frappe.get_cached_doc("Patient Encounter", doc.ref_docname)

    for d in encounter_doc.patient_encounter_preliminary_diagnosis:
        diseases.append({
            "diseaseCode": get_disease_code(d.code),
            "notes": d.description,
            "createdBy": doc.practitioner,
            "dateCreated": str(doc.creation)
        })

    return diseases


def get_authorized_items(
    doc,
    service_type, 
    service_name,
    years_of_insurance,
    qty=1
):
    items = []

    item = frappe.get_cached_value(service_type, service_name, "item")
    ref_code = get_item_refcode(service_type, service_name)
    item_rate = get_item_rate(
        item,
        doc.company,
        doc.insurance_subscription,
        doc.insurance_company
    )

    service_type_id = frappe.get_cached_value(
        "NHIF Item", {"itemcode": ref_code}, "servicetypeid"
    )

    scheme_id = frappe.get_cached_value(
        "Healthcare Insurance Coverage Plan",
        doc.healthcare_insurance_coverage_plan,
        "nhif_scheme_id"
    )

    product_code = frappe.get_cached_value(
        "NHIF Product", {
            "schemeid": scheme_id,
            "company": doc.company,
            "healthcare_insurance_coverage_plan": doc.hms_tz_insurance_coverage_plan
        }, "nhif_product_code"
    )

    if not product_code:
        frappe.throw(f"NHIF Product Code for {doc.healthcare_insurance_coverage_plan} not found")

    percent_covered = frappe.get_cached_value(
        "NHIF Cost Sharing", {	
            "itemcode": ref_code,
            "productcode": product_code,
            "yearno": years_of_insurance
        }, "percentcovered"
    )

    items.append({
        "serviceTypeID": service_type_id,
        "itemCode": ref_code,
        "description": service_name,
        "quantityRequested": qty,
        "unitPrice": item_rate or 0,
        "percentCovered": percent_covered,
        "createdBy": doc.practitioner,
        "dateCreated": str(doc.creation)
    })

    return items


def get_update_approval_payload(doc, facility_code, service_type, service_name, qty=1):
    patient_doc = frappe.get_cached_doc("Patient", doc.patient)
    appointment_info = get_appointment_details(doc.appointment)
    clinical_notes = frappe.get_cached_value("Patient Encounter", doc.ref_docname, "examination_detail") or ""

    practitioner_no = frappe.get_cached_value("Healthcare Practitioner", doc.practitioner, "tz_mct_code")
    scheme_id = frappe.get_cached_value(
        "Healthcare Insurance Coverage Plan",
        doc.healthcare_insurance_coverage_plan,
        "nhif_scheme_id"
    )

    product_code = frappe.get_cached_value(
        "NHIF Product", {
            "schemeid": scheme_id,
            "company": doc.company,
            "healthcare_insurance_coverage_plan": doc.hms_tz_insurance_coverage_plan
        }, "nhif_product_code"
    )
    if not product_code:
        frappe.throw(f"NHIF Product Code for {doc.healthcare_insurance_coverage_plan} not found")

    service_type_id = get_service_type_id("hfvbhfvfdjvf")
    ref_code = get_item_refcode(service_type, service_name)
    item = frappe.get_cached_value(service_type, service_name, "item")
    item_rate = get_item_rate(
        item,
        doc.company,
        doc.insurance_subscription,
        doc.insurance_company
    )
    
    percent_covered = frappe.get_cached_value(
        "NHIF Cost Sharing", {	
            "itemcode": ref_code,
            "productcode": product_code,
            "yearno": appointment_info.years_of_insurance
        }, "percentcovered"
    )

    payload = {
        "serviceAuthorizationID": doc.service_authorization_id,
        "serviceTypeID": service_type_id,
        "cardNo": appointment_info.coverage_plan_card_number or appointment_info.national_id,
        "cardExistence": "",
        "firstName": patient_doc.first_name,
        "lastName": patient_doc.last_name,
        "gender": doc.get("hms_tz_patient_sex") or patient_doc.sex,
        "telephoneNo": patient_doc.mobile,
        "clinicalNotes": clinical_notes,
        "dateOfBirth": patient_doc.dob,
        "schemeID": scheme_id,
        "productCode": product_code,
        "authorizationNo": appointment_info.authorization_number,
        "facilityPatientFileNumber": doc.patient,
        "yearOfBirth": patient_doc.dob[:-4],
        "attendanceDate": appointment_info.appointment_date,
        "serviceDate": nowdate(),
        "expiryDate": "",
        "sourceFacilityCode": facility_code,
        "approvalStatusID": 0,
        "practitionerNo": practitioner_no,
        "prescribedBy": doc.practitioner,
        "qualificationID": 0,
        "issuingFacilityCode": facility_code,
        "approvalIssuingFacilityCode": facility_code,
        "officeCode": "",
        "referenceNo": doc.approval_number,
        "serviceState": "",
        "requestedBy": "", # TODO: add requested by
        "approvedBy": "", # TODO: add approved by
        "approvedDate": "", # TODO: add approved date
        "createdBy": doc.practitioner,
        "dateCreated": str(doc.creation),
        "lastModifiedBy": get_fullname(doc.modified_by),
        "lastModified": str(doc.modified),
        "approvalDiseases": [
            {
                "appDiseaseID": "", # TODO: add app disease id
                "serviceAuthorizationID": doc.service_authorization_id,
                "diseaseCode": "string",
                "notes": "string",
                "createdBy": doc.practitioner,
                "dateCreated": str(doc.creation),
                "lastModifiedBy": get_fullname(doc.modified_by), 
                "lastModified": str(doc.modified)
            }
        ],
        "authorizedItems": [
            {
                "authorizedItemID": doc.item_authorization_id,
                "serviceAuthorizationID": doc.service_authorization_id,
                "serviceTypeID": service_type_id,
                "itemCode": ref_code,
                "description": service_name,
                "quantity": qty,
                "quantityRequested": qty,
                "unitPrice": item_rate or 0,
                "percentCovered": percent_covered,
                "createdBy": doc.practitioner,
                "dateCreated": str(doc.creation),
                "lastModifiedBy": get_fullname(doc.modified_by),
                "lastModified": str(doc.modified)
            }
        ],
        "approvalSupportingDocuments": [] # TODO: add supporting documents
    }
    # {
    #     "supportingDocumentID": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    #     "serviceAuthorizationID": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    #     "documentTypeID": 0,
    #     "documentDetails": "string",
    #     "filePath": "string",
    #     "documentData": "string",
    #     "fileType": "string"
    # }
    return payload


def get_appointment_details(appointment):
    appointment_info = frappe.get_cached_value(
        "Patient Appointment", appointment, 
        ["authorization_number", "appointment_date", "years_of_insurance", "coverage_plan_card_number", "national_id"],
        as_dict=True
    )

    return appointment_info


def get_service_type_id(ref_code):
    service_type_id = frappe.get_cached_value(
        "NHIF Item", {"itemcode": ref_code}, "servicetypeid"
    )
    return service_type_id