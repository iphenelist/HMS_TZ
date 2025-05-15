import json
import frappe
import requests
import base64
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

    doc = frappe.get_cached_doc(ref_doctype, ref_docname)

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

        data = json.loads(r.text)

        doc.add_comment(
            comment_type="Comment",
            text=f"Service approval request failed<br><br>Status Code: {r.status_code}<br>NHIF Response: <b>{data.get('message') or r.text}<b>",
        )
        doc.reload()
        frappe.msgprint(
            title="NHIF API Error",
            msg=f"Request Approval Failed<br><br>Status Code: {r.status_code}<br>NHIF Response: <b>{data.get('message') or r.text}<b>",
            indicator="red"
        )
        if r.text:
            return {
                "status": "error",
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

        msg = "Request Approval successful!"
        doc.service_authorization_id = data.get("ServiceAuthorizationID")
        if data.get("ReferenceNo"):
            msg += f"<br>ReferenceNo: <b>{data.get('ReferenceNo')}</b><br>"
            doc.approval_number = data.get("ReferenceNo")
        else:
            msg += "<br>ReferenceNo: <b>Not Provided</b><br> Please ask for <b>'Approval Statues'</b>"
        
        doc.save(ignore_permissions=True)
        
        doc.add_comment(
            comment_type="Comment",
            text=msg
        )
        doc.reload()

        return {
            "status": "success",
            "reference_no": data.get("ReferenceNo")
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
    
    doc = frappe.get_cached_doc(ref_doctype, ref_docname)

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
        # return {
        #     "status": "error",
        #     "message": f"Service approval update failed with status code {r.status_code}",
        #     "data": r.text,
        # }
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
        # return {
        #     "status": "success",
        #     "message": "Service approval update successful",
        #     "data": data,
        # }


@frappe.whitelist()
def issue_approved_service(
    ref_doctype,
    ref_docname,
    service_type,
    service_name,
    fingerprint,
    fpcode,
    biometric_method,
    qty=1
):
    if not ref_doctype or not ref_docname:
        frappe.throw("Document Type and Document Name are required")
    
    doc = frappe.get_cached_doc(ref_doctype, ref_docname)

    fingerprint_data = fingerprint.replace("-", "+").replace("_", "/")
    image_data = base64.b64encode(fingerprint_data.encode('utf-8')).decode('utf-8')
    
    item = frappe.get_cached_value(service_type, service_name, "item")
    item_rate = get_item_rate(
        item,
        doc.company,
        doc.insurance_subscription,
        doc.insurance_company
    )

    payload = {
        "approvalReferenceNo": doc.approval_number,
        "isBiometricVerified": True,
        "biometricMethod": biometric_method,
        "fpCode": fpcode,
        "imageData": image_data,
        "description": service_name,
        "quantity": qty,
        "unitPrice": item_rate or 0,
        "createdBy": doc.practitioner
    }

    payload = json.dumps(payload)

    settings_doc = frappe.get_cached_doc("HMS TZ Settings", doc.company)

    token = settings_doc.get_nhif_token()

    url = f"{settings_doc.nhifservice_url}/api/Approvals/IssueApprovedService"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    r = requests.request("POST", url, headers=headers, data=payload, timeout=120)
    if r.status_code != 200:
        add_log(
            request_type="IssueApprovedService",
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
            request_type="IssueApprovedService",
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
        "dateOfBirth": str(patient_doc.dob),
        "authorizationNo": appointment_info.authorization_number,
        "facilityPatientFileNumber": doc.patient,
        "attendanceDate": str(appointment_info.appointment_date),
        "serviceDate": str(doc.start_date),
        "expiryDate": str(doc.start_date),
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
        "approvalSupportingDocuments": []# TODO: add supporting documents
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
            "dateCreated": str(doc.creation.isoformat())
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
        doc.hms_tz_insurance_coverage_plan,
        "nhif_scheme_id"
    )

    percent_covered = frappe.get_cached_value(
        "NHIF Co-Payment Item", {	
            "itemcode": ref_code,
            "schemeid": scheme_id,
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
        "dateCreated": str(doc.creation.isoformat())
    })

    return items


def get_update_approval_payload(doc, facility_code, service_type, service_name, qty=1):
    patient_doc = frappe.get_cached_doc("Patient", doc.patient)
    appointment_info = get_appointment_details(doc.appointment)
    clinical_notes = frappe.get_cached_value("Patient Encounter", doc.ref_docname, "examination_detail") or ""

    practitioner_no = frappe.get_cached_value("Healthcare Practitioner", doc.practitioner, "tz_mct_code")
    scheme_id = frappe.get_cached_value(
        "Healthcare Insurance Coverage Plan",
        doc.hms_tz_insurance_coverage_plan,
        "nhif_scheme_id"
    )

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
        "NHIF Co-Payment Item", {	
            "itemcode": ref_code,
            "schemeid": scheme_id,
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
        "dateOfBirth": str(patient_doc.dob),
        "schemeID": scheme_id,
        "productCode": "",
        "authorizationNo": appointment_info.authorization_number,
        "facilityPatientFileNumber": doc.patient,
        "yearOfBirth": patient_doc.dob[:-4],
        "attendanceDate": str(appointment_info.appointment_date),
        "serviceDate": str(doc.start_date),
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
        "dateCreated": str(doc.creation.isoformat()),
        "lastModifiedBy": get_fullname(doc.modified_by),
        "lastModified": str(doc.modified.isoformat()),
        "approvalDiseases": [
            {
                "appDiseaseID": "", # TODO: add app disease id
                "serviceAuthorizationID": doc.service_authorization_id,
                "diseaseCode": "string",
                "notes": "string",
                "createdBy": doc.practitioner,
                "dateCreated": str(doc.creation.isoformat()),
                "lastModifiedBy": get_fullname(doc.modified_by), 
                "lastModified": str(doc.modified.isoformat())
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
                "dateCreated": str(doc.creation.isoformat()),
                "lastModifiedBy": get_fullname(doc.modified_by),
                "lastModified": str(doc.modified.isoformat())
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


@frappe.whitelist()
def verify_service_approval_number(
    company,
    approval_number,
    service_type,
    service_name,
    appointment,
    ref_doctype,
    ref_docname
):
    ref_code = get_item_refcode(service_type, service_name)
    appointment_info = get_appointment_details(appointment)

    settings_doc = frappe.get_cached_doc("HMS TZ Settings", company)

    if settings_doc.validate_service_approval_number_on_lrpm_documents == 0:
        frappe.msgprint("Service Approval Number Validation is disabled")
        return

    card_no = appointment_info.coverage_plan_card_number or appointment_info.national_id
    
    url = f"{settings_doc.nhifservice_url}/api/Approvals/GetReferenceNoStatus?cardNo={card_no}&referenceNo={approval_number}&itemCode={ref_code}"

    token = settings_doc.get_nhif_token()
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    r = requests.request("Get", url, headers=headers, timeout=60)
    if r.status_code != 200:
        add_log(
            request_type="GetReferenceNoStatus",
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
        frappe.msgprint(f"Error: <b>{r.text}</b>")
        return False
    else:
        data = json.loads(r.text)
        add_log(
            request_type="GetReferenceNoStatus",
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
        if data["Status"] == "VALID":
            return True
        else:
            frappe.msgprint(
                f"<h4 class='text-center' style='background-color: #D3D3D3; font-weight: bold;'>\
                This ApprovalNumber: <strong>{approval_number}</strong> for CardNo: <strong>{card_no}</strong> and ItemCode: <strong>{ref_code}</strong> is not Valid</h4>"
            )
            return False


@frappe.whitelist()
def get_approval_services(company=None, caller=None):
    if not company:
        settings = frappe.db.get_all("HMS TZ Settings", filters={"enable_nhif_api": 1}, fields=["company"])
        company = settings[0].company

    if not company:
        return
    
    settings_doc = frappe.get_cached_doc("HMS TZ Settings", company)
    token = settings_doc.get_nhif_token()
    url = f"{settings_doc.nhifservice_url}/api/Approvals/GetApprovalServices"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    r = requests.request("Get", url, headers=headers, timeout=60)
    if r.status_code != 200:
        add_log(
            request_type="GetApprovalServices",
            request_url=url,
            request_header=headers,
            request_body="",
            response_data=r.text,
            status_code=r.status_code,
            company=settings_doc.name,
            ref_doctype="NHIF Service Type",
        )
        return

    else:
        data = json.loads(r.text)
        add_log(
            request_type="GetApprovalServices",
            request_url=url,
            request_header=headers,
            request_body="",
            response_data=data,
            status_code=r.status_code,
            company=settings_doc.name,
            ref_doctype="NHIF Service Type",
        )

        for row in data:
            if frappe.db.exists("NHIF Service Type", row["ServiceTypeName"]):
                has_changed = False
                doc = frappe.get_cached_doc("NHIF Service Type", row["ServiceTypeName"])
                if doc.service_type_id != row["ServiceTypeID"]:
                    has_changed = True
                    doc.service_type_id = row["ServiceTypeID"]
                
                if doc.require_nhif_number != row["RequireNhifNumber"]:
                    has_changed = True
                    doc.require_nhif_number = row["RequireNhifNumber"]
                
                if has_changed:
                    doc.save(ignore_permissions=True)
                
                continue
            else:
                doc = frappe.new_doc("NHIF Service Type")
                doc.service_type_id = row["ServiceTypeID"]
                doc.service_type_name = row["ServiceTypeName"]
                doc.require_nhif_number = row["RequireNhifNumber"]

                doc.save(ignore_permissions=True)
        
        if company and caller == 'Front End':
            frappe.msgprint("successfully fetched Service Types", alert=True, indicator="green")
