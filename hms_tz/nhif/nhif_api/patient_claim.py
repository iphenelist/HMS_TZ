import json

import frappe
import requests
from frappe.utils import flt, get_fullname, now_datetime, get_datetime

from hms_tz.nhif.doctype.nhif_response_log.nhif_response_log import add_log


def submit_folio(doc):
    """
    Submit a patient claim to NHIF
    """

    payload = get_payload(doc)

    settings_doc = frappe.get_cached_doc("HMS TZ Setting", doc.company)

    token = settings_doc.get_nhif_token()

    url = f"{settings_doc.nhif_claim_url}/api/Claims/SubmitFolio"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    r = None
    try:
        r = requests.request("Post", url, data=payload, headers=headers, timeout=300)
        if r.status_code != 200:
            add_log(
                request_type="SubmitFolio",
                request_url=url,
                request_header=headers,
                request_body=payload,
                response_data=(r.text if str(r) else "NO RESPONSE r. Timeout???"),
                status_code=(r.status_code if str(r) else "NO STATUS CODE"),
                company=settings_doc.name,
                ref_doctype=doc.doctype,
                ref_docname=doc.name,
            )
            if str(r) and r.status_code == 500 and "A claim with Similar" in r.text:
                frappe.msgprint(
                    f"This folio was NOT sent. However, since the folio is already existing at NHIF, it has been submitted!<br><b>Message from NHIF:</b><br><br>{r.text}"
                )
            elif (
                str(r) and r.status_code == 406 and f"Folio Number {doc.folio_no} has already been submited." in r.text
            ):
                frappe.msgprint(
                    f"This folio was NOT sent. However, since it is already existing at NHIF, it has been submitted!<br><b>Message from NHIF:</b><br><br>{r.text}"
                )
            else:
                frappe.msgprint(
                    f"NHIF responded with HTTP status code: {str(r.status_code if r.status_code else 'NO STATUS CODE')}"
                )
                frappe.throw(str(r.text) if r.text else str(r))

        else:
            data = json.loads(r.text)
            add_log(
                request_type="SubmitFolio",
                request_url=url,
                request_header=headers,
                request_body=payload,
                response_data=data,
                status_code=r.status_code,
                company=settings_doc.name,
                ref_doctype=doc.doctype,
                ref_docname=doc.name,
            )

            doc.submission_id = data.get("SubmissionID")
            doc.submission_no = data.get("SubmissionNo")
            doc.date_submitted = get_datetime(data.get("DateSubmitted"))
            doc.submission_channel = data.get("SubmissionChannel")
            doc.submission_remarks = data.get("Remarks")
            doc.hashcode = data.get("HashCode")

            frappe.msgprint(str(data.get("Remarks")))
            frappe.msgprint("The claim has been sent successfully", alert=True)

    except Exception:
        add_log(
            request_type="SubmitFolio",
            request_url=url,
            request_header=headers,
            request_body=payload,
            response_data=(r.text if str(r) else "NO RESPONSE r. Timeout???"),
            status_code=(r.status_code if str(r) else "NO STATUS CODE"),
            company=settings_doc.name,
            ref_doctype=doc.doctype,
            ref_docname=doc.name,
        )
        doc.add_comment(
            comment_type="Comment",
            text=r.text if str(r) else "NO RESPONSE",
        )
        frappe.db.commit()

        frappe.throw(
            "This folio was NOT submitted due to the error above!. Please retry after resolving the problem. "
        )


def get_payload(doc):
    items = []
    diseases = []
    attendance_datetime = get_datetime(f"{doc.attendance_date} {doc.attendance_time}")

    for disease in doc.nhif_patient_claim_disease:
        created_date = get_datetime(disease.date_created)

        disease_dict = {
            "DiseaseCode": disease.disease_code,
            "Status": disease.status,
            "Remarks": None,
            "CreatedBy": disease.item_crt_by,
            "DateCreated": created_date.isoformat(),
            "LastModified": created_date.isoformat(),
            "LastModifiedBy": disease.item_crt_by,
        }
        diseases.append(disease_dict)

    for item in doc.nhif_patient_claim_item:
        created_date = get_datetime(item.date_created)
        item_dict = {
            "ItemCode": item.item_code,
            "ItemName": item.item_name,
            "ItemTypeID": frappe.get_cached_value("NHIF Item", {"itemcode": item.item_code}, "itemtypeid"),
            "ItemQuantity": item.item_quantity,
            "UnitPrice": item.unit_price,
            "AmountClaimed": item.amount_claimed,
            "ApprovalRefNo": item.approval_ref_no or None,
            "CreatedBy": item.item_crt_by,
            "DateCreated": created_date.isoformat(),
            "LastModifiedBy": item.item_crt_by,
            "LastModified": created_date.isoformat(),
            "OtherDetails": "",
        }
        items.append(item_dict)

    Signatures = [{
        "Signatory": "Patient",
        "SignatoryID": doc.cardno.strip(),
        "SignatureData": doc.patient_signature,
        "DateCreated": str(doc.posting_date),
        "CreatedBy": doc.item_crt_by,
        "LastModified": get_datetime(doc.modified).isoformat(),
        "LastModifiedBy": get_fullname(doc.modified_by),
    }]

    for d in doc.practitioners:
        if d.mct_code:
            Signatures.append({
                "Signatory": "MCT",
                "SignatoryID": d.mct_code,
                "SignatureData": frappe.get_cached_value("Healthcare Practitioner", d.practitioner, "doctors_signature"),
                "DateCreated": str(doc.posting_date),
                "CreatedBy": doc.item_crt_by,
                "LastModified": get_datetime(doc.modified).isoformat(),
                "LastModifiedBy": get_fullname(doc.modified_by),
            })

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
        "AttendanceDate": attendance_datetime.isoformat(),
        "PatientTypeCode": doc.patient_type_code,
        "AttendingPractitioners": [d.mct_code for d in doc.practitioners if d.mct_code],
        "LateSubmissionReason": doc.delayreason,
        "AmountClaimed": doc.total_amount,
        "ConfirmationCode": doc.confirmation_code or "",
        "FolioDiseases": diseases,
        "FolioItems": items,
        "Signatures": Signatures,
        "DateCreated": str(doc.posting_date),
        "CreatedBy": doc.item_crt_by,
        "LastModified": get_datetime(doc.modified).isoformat(),
        "LastModifiedBy": get_fullname(doc.modified_by),
    }
    if doc.patient_type_code == "IN":
        admission_datetime = get_datetime(f"{doc.date_admitted} {doc.admitted_time}")
        discharge_datetime = get_datetime(f"{doc.date_discharge} {doc.discharge_time}")

        payload["DateAdmitted"] = admission_datetime.isoformat()
        payload["DateDischarged"] = discharge_datetime.isoformat()

    payload = json.dumps(payload)

    return payload


def get_submitted_claims(doc):
    """Get submitted claims from NHIF"""

    settings_doc = frappe.get_cached_doc("HMS TZ Setting", doc.company)

    token = settings_doc.get_nhif_token()

    url = f"{settings_doc.nhif_claim_url}/api/Claims/GetSubmittedClaims?facilityCode={settings_doc.facility_code}&claimYear={doc.claim_year}&claimMonth={doc.claim_month}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    r = requests.request("Get", url, headers=headers, timeout=120)
    if r.status_code != 200:
        add_log(
            request_type="GetSubmittedClaims",
            request_url=url,
            request_header=headers,
            request_body="",
            response_data=r.text,
            status_code=r.status_code,
            company=settings_doc.name,
            ref_doctype=doc.doctype,
            ref_docname=doc.name,
        )

        frappe.throw(
            f"NHIF responded with HTTP status code: {str(r.status_code if r.status_code else 'NO STATUS CODE')}\
                <br><br><b>Message from NHIF:</b><br>{r.text}"
        )

    else:
        data = json.loads(r.text)
        add_log(
            request_type="GetSubmittedClaims",
            request_url=url,
            request_header=headers,
            request_body="",
            response_data=data,
            status_code=r.status_code,
            company=settings_doc.name,
            ref_doctype=doc.doctype,
            ref_docname=doc.name,
        )

        if len(data) == 0:
            frappe.throw(
                f"No record found for facility: {frappe.bold(doc.company)}, claim year: {frappe.bold(doc.claim_year)} and claim month: {frappe.bold(doc.claim_month)}"
            )

        return update_reconciliation_detail(doc, data)


def update_reconciliation_detail(doc, records):
    total_amount = 0
    doc.status = "Successful"
    doc.number_of_submitted_claims = len(records)

    doc.claim_details = []
    for record in records:
        total_amount += flt(record["AmountClaimed"])
        doc.append(
            "claim_details",
            {
                "foliono": record["FolioNo"],
                "billno": record["BillNo"],
                "datesubmitted": record["DateSubmitted"],
                "cardno": record["CardNo"],
                "authorizationno": record["AuthorizationNo"],
                "amountclaimed": flt(record["AmountClaimed"]),
                "submissionid": record["SubmissionID"],
                "submissionno": record["SubmissionNo"],
                "remarks": record["Remarks"],
            },
        )

    doc.total_amount_claimed = total_amount
    return True


def submit_monthly_claim(doc):
    """
    Submit a monthly claim to NHIF
    """

    settings_doc = frappe.get_cached_doc("HMS TZ Setting", doc.company)

    payload = {
        "FacilityCode": settings_doc.facility_code,
        "ClaimYear": doc.claim_year,
        "ClaimMonth": doc.claim_month,
        "FoliosSubmitted": doc.folio_submitted,
        "TotalAmountClaimed": doc.total_amount_claimed,
        "SubmissionRemarks": doc.submission_remarks,
    }
    payload = json.dumps(payload)

    url = f"{settings_doc.nhif_claim_url}/api/Claims/SubmitMonthlyClaim"

    token = settings_doc.get_nhif_token()

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    r = requests.request("Post", url, data=payload, headers=headers, timeout=120)
    if r.status_code != 200:
        add_log(
            request_type="SubmitMonthlyClaim",
            request_url=url,
            request_header=headers,
            request_body=payload,
            response_data=r.text,
            status_code=r.status_code,
            company=settings_doc.name,
            ref_doctype=doc.doctype,
            ref_docname=doc.name,
        )

        frappe.throw(
            f"NHIF responded with HTTP status code: {str(r.status_code if r.status_code else 'NO STATUS CODE')}\
                <br><br><b>Message from NHIF:</b><br>{r.text}"
        )

    else:
        data = json.loads(r.text)
        add_log(
            request_type="SubmitMonthlyClaim",
            request_url=url,
            request_header=headers,
            request_body=payload,
            response_data=data,
            status_code=r.status_code,
            company=settings_doc.name,
            ref_doctype=doc.doctype,
            ref_docname=doc.name,
        )

        doc.status = "Successful"
        doc.acknowledgement_no = data.get("AcknowledgementNo")
        doc.date_submitted = get_datetime(data.get("DateSubmitted"))

        return True



@frappe.whitelist()
def send_confirmation_code(ref_doctype, ref_docname):
    """
    Send confirmation code to Patient
    """

    doc = frappe.get_cached_doc(ref_doctype, ref_docname)

    attendance_datetime = get_datetime(f"{doc.attendance_date} {doc.attendance_time}")
    payload = {
        "FacilityCode": doc.facility_code,
        "CardNo": doc.cardno.strip(),
        "AuthorizationNo": doc.authorization_no,
        "AttendanceDate": attendance_datetime.isoformat(),
        "TotalAmount": doc.total_amount,
    }
    payload = json.dumps(payload)

    settings_doc = frappe.get_cached_doc("HMS TZ Setting", doc.company)

    token = settings_doc.get_nhif_token()

    url = f"{settings_doc.nhif_claim_url}/api/Claims/SendConfirmationCode"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }
    r = requests.request("Post", url, data=payload, headers=headers, timeout=120)
    if r.status_code != 200:
        add_log(
            request_type="SendConfirmationCode",
            request_url=url,
            request_header=headers,
            request_body=payload,
            response_data=r.text,
            status_code=r.status_code,
            company=settings_doc.name,
            ref_doctype=doc.doctype,
            ref_docname=doc.name,
        )

        frappe.throw(
            f"NHIF responded with HTTP status code: {str(r.status_code if r.status_code else 'NO STATUS CODE')}\
                <br><br><b>Message from NHIF:</b><br>{r.text}"
        )
    else:
        data = json.loads(r.text)
        add_log(
            request_type="SendConfirmationCode",
            request_url=url,
            request_header=headers,
            request_body=payload,
            response_data=data,
            status_code=r.status_code,
            company=settings_doc.name,
            ref_doctype=doc.doctype,
            ref_docname=doc.name,
        )

        frappe.db.set_value(doc.doctype, doc.name, "confirmation_code_sent", 1)
        doc.reload()

        doc.add_comment(
            comment_type="Comment",
            text=f"Confirmation code sent successfully!<br><br><b>Message from NHIF:</b><br>{data.get('Message')}",
        )
        return True


@frappe.whitelist()
def get_receipt(ref_doctype, ref_docname):
    """
    Get receipt from NHIF
    """

    doc = frappe.get_cached_doc(ref_doctype, ref_docname)

    settings_doc = frappe.get_cached_doc("HMS TZ Setting", doc.company)

    token = settings_doc.get_nhif_token()

    url = f"{settings_doc.nhif_claim_url}/api/Claims/GetReceipt?facilityCode={doc.facility_code}&claimYear={doc.claim_year}&claimMonth={doc.claim_month}&folioNo={doc.folio_no}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }
    r = requests.request("Get", url, headers=headers, timeout=120)
    if r.status_code != 200:
        add_log(
            request_type="GetReceipt",
            request_url=url,
            request_header=headers,
            request_body="",
            response_data=r.text,
            status_code=r.status_code,
            company=settings_doc.name,
            ref_doctype=doc.doctype,
            ref_docname=doc.name,
        )
        doc.add_comment(
            comment_type="Comment",
            text=f"Failed to retrieve receipt!<br><br><b>Message from NHIF:</b><br>{r.text}",
        )
        frappe.db.commit()

        frappe.throw(
            f"NHIF responded with HTTP status code: {str(r.status_code if r.status_code else 'NO STATUS CODE')}\
                <br><br><b>Message from NHIF:</b><br>{r.text}"
        )
    else:
        data = json.loads(r.text)
        add_log(
            request_type="GetReceipt",
            request_url=url,
            request_header=headers,
            request_body="",
            response_data=data,
            status_code=r.status_code,
            company=settings_doc.name,
            ref_doctype=doc.doctype,
            ref_docname=doc.name,
        )

        doc.receipt_no = data.get("ReceiptNo")
        doc.save(ignore_permissions=True)
        doc.reload()

        doc.add_comment(
            comment_type="Comment",
            text=f"Receipt retrieved successfully!<br><br><b>Message from NHIF:</b><br>{data.get('Message')}",
        )
        return True
