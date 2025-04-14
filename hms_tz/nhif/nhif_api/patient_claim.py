import json
import frappe
import requests
from frappe.utils import now_datetime, get_fullname, flt
from hms_tz.nhif.doctype.nhif_response_log.nhif_response_log import add_log


def submit_folio(doc):
    """
    Submit a patient claim to NHIF
    """

    payload = get_payload(doc)

    settings_doc = frappe.get_cached_doc("HMS TZ Settings", doc.company)

    token = settings_doc.get_nhif_token()

    url = f"{settings_doc.nhif_claim_url}/api/Claims/SubmitFolio"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    r = None
    try:
        r = requests.request("Post", url, data=payload, headers=headers, timeout=300)
        if r.status_code != 200:
            if (
                str(r) and 
                r.status_code == 500 and
                "A claim with Similar" in r.text
            ):
                    frappe.msgprint(
                        f"This folio was NOT sent. However, since the folio is already existing at NHIF, it has been submitted!<br><b>Message from NHIF:</b><br><br>{r.text}"
                        + str(now_datetime())
                    )
            elif (
                str(r)
                and r.status_code == 406
                and f"Folio Number {doc.folio_no} has already been submited." in r.text
            ):
                frappe.msgprint(
                    f"This folio was NOT sent. However, since it is already existing at NHIF, it has been submitted!<br><b>Message from NHIF:</b><br><br>{r.text}"
                    + str(now_datetime())
                )
            else:
                frappe.msgprint(
                    f"NHIF Server responded with HTTP status code: {str(r.status_code if r.status_code else 'NO STATUS CODE')}"
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
                ref_docname=doc.name
            )
            frappe.msgprint(str(r.text))
            frappe.msgprint(_("The claim has been sent successfully"), alert=True)

            # TODO: update response values to Healthcare Referral doc

    except Exception as e:
        add_log(
            request_type="SubmitFolio",
            request_url=url,
            request_header=headers,
            request_body=payload,
            response_data=(r.text if str(r) else "NO RESPONSE r. Timeout???"),
            status_code=(r.status_code if str(r) else "NO STATUS CODE"),
            company=settings_doc.name,
            ref_doctype=doc.doctype,
            ref_docname=doc.name
        )
        doc.add_comment(
            comment_type="Comment",
            text=r.text if str(r) else "NO RESPONSE",
        )
        frappe.db.commit()

        frappe.throw(
            "This folio was NOT submitted due to the error above!. Please retry after resolving the problem. "
            + str(now_datetime())
        )


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


def get_submitted_claims(doc):
    """Get submitted claims from NHIF"""

    settings_doc = frappe.get_cached_doc("HMS TZ Settings", doc.company)

    token = settings_doc.get_nhif_token()

    url = f"{settings_doc.nhif_claim_url}/api/Claims/GetSubmittedClaims?facilityCode={settings_doc.facility_code}&claimYear={doc.claim_year}&claimMonth={doc.claim_month}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
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
            ref_docname=doc.name
        )

        frappe.throw(
            f"NHIF Server responded with HTTP status code: {str(r.status_code if r.status_code else 'NO STATUS CODE')}\
                <br><b>Message from NHIF:</b><br><br>{r.text}"
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
            ref_docname=doc.name
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
		doc.append("claim_details", {
			"foliono": record["FolioNo"],
			"billno": record["BillNo"],
			"datesubmitted": record["DateSubmitted"],
			"cardno": record["CardNo"],
			"authorizationno": record["AuthorizationNo"],
			"amountclaimed": flt(record["AmountClaimed"]),
			"submissionid": record["SubmissionID"],
			"submissionno": record["SubmissionNo"],
			"remarks": record["Remarks"],
		})

	doc.total_amount_claimed = total_amount
	return True


def submit_monthly_claim(doc):
    """
    Submit a monthly claim to NHIF
    """

    settings_doc = frappe.get_cached_doc("HMS TZ Settings", doc.company)

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
        "Authorization": f"Bearer {token}"
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
            ref_docname=doc.name
        )

        frappe.throw(
            f"NHIF Server responded with HTTP status code: {str(r.status_code if r.status_code else 'NO STATUS CODE')}\
                <br><b>Message from NHIF:</b><br><br>{r.text}"
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
            ref_docname=doc.name
        )

        # TODO: update response values to NHIF Monthly Claim doc
        doc.status = "Successful"