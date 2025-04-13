import json
import frappe
import requests
from frappe import get_fullname
from hms_tz.nhif.doctype.nhif_response_log.nhif_response_log import add_log



def get_payload(doc):
    payload = {
        "FacilityCode": doc.facility_code,
        "ClaimYear": doc.claim_year,
        "ClaimMonth": doc.claim_month,
        "FolioNo": doc.folio_no,
        "CardNo": doc.cardno.strip(),
        "FirstName": doc.first_name,
        "LastName": doc.last_name,
        "Gender": doc.gender,
        "DateOfBirth": str(doc.date_of_birth),
        "TelephoneNo": doc.telephone_no,
        "PatientFileNo": doc.patient_file_no,
        "BillNo": doc.name,
        "ClinicalNotes": doc.clinical_notes,
        "AuthorizationNo": doc.authorization_no,
        "AttendanceDate": str(doc.attendance_date),
        "PatientTypeCode": doc.patient_type_code,
        "AttendingPractitioners": [mct_code for mct_code in doc.practitioner_no.split(",")],
        "LateSubmissionReason": doc.delayreason,
        "AmountClaimed": doc.total_amount,
        "ConfirmationCode": "string", # TODO: add confirmation code functionality,
        "FolioDiseases": diseases,
        "FolioItems": items,
        "DateCreated": str(doc.posting_date),
        "CreatedBy": doc.item_crt_by,
        "LastModified": str(doc.modified),
        "LastModifiedBy": get_fullname(doc.modified_by),
    }
    if doc.patient_type_code == "IN":
        payload["DateAdmitted"] = str(doc.date_admitted) + " " + str(doc.admitted_time)
        payload["DateDischarged"] = str(doc.date_discharge) + " " + str(doc.discharge_time)

    items = []
    diseases = []
    for disease in doc.nhif_patient_claim_disease:
        disease_dict = {
            "DiseaseCode": disease.disease_code,
            "Status": disease.status,
            "Remarks": None,
            "CreatedBy": disease.item_crt_by,
            "DateCreated": str(disease.date_created),
            "LastModified": str(disease.date_created),
            "LastModifiedBy": disease.item_crt_by,
        }
        diseases.append(disease_dict)

    for item in doc.nhif_patient_claim_item:
        item_dict = {
            "ItemCode": item.item_code,
            "ItemName": item.item_name,
            "ItemTypeID": None, # TODO: add item type id functionality
            "ItemQuantity": item.item_quantity,
            "UnitPrice": item.unit_price,
            "AmountClaimed": item.amount_claimed,
            "ApprovalRefNo": item.approval_ref_no or None,
            "CreatedBy": item.item_crt_by,
            "DateCreated": str(item.date_created),
            "LastModifiedBy": item.item_crt_by,
            "LastModified": str(item.date_created),
            "OtherDetails": None,
        }
        items.append(item_dict)

    payload = json.dumps(payload)

    return payload