import json
import frappe
import requests
from frappe.utils import add_days
from hms_tz.nhif.nhif_api.referral import get_disease_code
from hms_tz.nhif.doctype.nhif_response_log.nhif_response_log import add_log
from hms_tz.hms_tz.doctype.healthcare_service_request.healthcare_service_request import (
    get_item_refcode, get_childs_map
)


@frappe.whitelist()
def get_service_preapproval(
    ref_doctype, 
    ref_docname,
    authorization_no=None,
    settings_doc=None, 
):
    encounter_doc = frappe.get_doc(ref_doctype, ref_docname)

    services, service_map, diseases = get_encounter_services(encounter_doc)
    if len(services) == 0:
        frappe.msgprint("No servuce(s) to request an Pre-Approvals")
        return False

    first_name, last_name, dob = frappe.get_cached_value(
        "Patient",
        encounter_doc.patient,
        ["first_name", "last_name", "dob"]
    )
    mct_code, mobile = frappe.get_cached_value(
        "Healthcare Practitioner",
        encounter_doc.practitioner,
        ["tz_mct_code", "mobile_phone"]
    )
    if not authorization_no:
        authorization_no = frappe.get_cached_value(
            "Patient Appointment", 
            encounter_doc.appointment,
            "authorization_number"
        )
    
    payload = {
        "authorizationNo": authorization_no,
        "firstName": first_name,
        "lastName": last_name,
        "gender": encounter_doc.patient_sex,
        "dateOfBirth": str(dob),
        "patientFileNo": encounter_doc.patient,
        "clinicalNotes": encounter_doc.examination_detail,
        "practitionerNo": mct_code,
        "practitionersRemarks": "",
        "telephoneNo": mobile,
        "diseases": diseases,
        "requestedServices": services
    }
    payload = json.dumps(payload)

    if not settings_doc:
        settings_doc = frappe.get_cached_doc("HMS TZ Settings", encounter_doc.company)

    url = f"{settings_doc.nhifservice_url}/api/PreApprovals/RequestServices"

    token = settings_doc.get_nhif_token()
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    r = requests.request("Post", url, data=payload, headers=headers, timeout=60)
    if r.status_code != 200:
        add_log(
            request_type="RequestServices",
            request_url=url,
            request_header=headers,
            request_body=payload,
            response_data=r.text,
            status_code=r.status_code,
            company=settings_doc.name,
            ref_doctype=ref_doctype,
            ref_docname=ref_docname,
        )
        frappe.throw(
            title="NHIF API Error",
            msg=f"Pre-approval failed<br><br>Status Code: {r.status_code}<br>Response: <b>{r.text}<b>",
            indicator="red"
        )
    else:
        data = json.loads(r.text)
        add_log(
            request_type="RequestServices",
            request_url=url,
            request_header=headers,
            request_body=payload,
            response_data=data,
            status_code=r.status_code,
            company=settings_doc.name,
            ref_doctype=ref_doctype,
            ref_docname=ref_docname,
        )

        rejected_count = 0
        msg = "Pre-Approval request were rejected for the following services:<hr>\
            <table class='table table-condensed table-bordered'><tr><th>Service Type</th><th>Service</th><th>Status</th><th>Reason</th></tr>"
    
        for child in get_childs_map():
            for row in encounter_doc.get(child.get("table")):
                ref_code = service_map.get((row.doctype, row.name, row.get(child.get("item"))))
                if not ref_code:
                    continue

                for d in data.get("services"):
                    if d.get("itemCode") == ref_code:
                        row.preapproval_status = d.get("status")
                        row.preapproval_no = data.get("requestNo")
                        row.rejection_reason_code = d.get("rejectionReasonCode")
                        row.rejection_details = d.get("rejectionDetails")
                        row.preapproval_cancel_remarks = ""
                        row.db_update()
                        row.reload()

                        if d.get("status") == "REJECTED":
                            rejected_count += 1
                            msg += f"<tr>\
                                <td>{row.doctype.split(' ')[0]}</td>\
                                <td>{row.get(child.get('item'))}</td>\
                                <td style='color: red'>{d.get('status')}</td>\
                                <td>{d.get('rejectionDetails')}</td>\
                            </tr>"
                        
        encounter_doc.has_preapproval = 1
        encounter_doc.db_update()
        encounter_doc.db_update_all()
        encounter_doc.reload()

        encounter_doc.add_comment(
            comment_type="Comment",
            text=f"Pre-approval request sent successful!<br>RequestID: <b>{data.get('requestID')}</b><br>"
        )
        if rejected_count > 0:
            msg += "</table>"
            frappe.msgprint(msg, title="Pre-Approval Status", indicator="red")
        else:
            frappe.msgprint("<b>Pre-Approval request were successful for all services</b>", title="Pre-Approval Status", indicator="green")

        return True


@frappe.whitelist()
def cancel_preapproval(
    ref_doctype, 
    ref_docname,
    preapproval_no,
    remarks,
    settings_doc=None,
):
    encounter_doc = frappe.get_doc(ref_doctype, ref_docname)
    services, service_map, diseases = get_encounter_services(encounter_doc, preapproval_no)
    if len(services) == 0:
        frappe.msgprint("No servuce(s) to cancel an Pre-Approvals")
        return False

    if not settings_doc:
        settings_doc = frappe.get_cached_doc("HMS TZ Settings", encounter_doc.company)
    
    url = f"{settings_doc.nhifservice_url}/api/PreApprovals/CancelRequest?requestNo={preapproval_no}&remarks={remarks}"

    token = settings_doc.get_nhif_token()
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    r = requests.request("Post", url, headers=headers, timeout=60)
    if r.status_code != 200:
        add_log(
            request_type="CancelRequest",
            request_url=url,
            request_header=headers,
            request_body="",
            response_data=r.text,
            status_code=r.status_code,
            company=settings_doc.name,
            ref_doctype=ref_doctype,
            ref_docname=ref_docname,
        )
        return False

    else:
        data = json.loads(r.text)
        add_log(
            request_type="CancelRequest",
            request_url=url,
            request_header=headers,
            request_body="",
            response_data=data,
            status_code=r.status_code,
            company=settings_doc.name,
            ref_doctype=ref_doctype,
            ref_docname=ref_docname,
        )

        has_preapproval = False
        for child in get_childs_map():
            for row in encounter_doc.get(child.get("table")):
                if row.preapproval_no == preapproval_no:
                    row.preapproval_status = "Cancelled"
                    row.preapproval_no = ""
                    row.preapproval_cancel_remarks = remarks
                    has_preapproval = False
                    row.db_update()
                    row.reload()
                
                elif row.preapproval_no and not has_preapproval:
                    has_preapproval = True
                    
        encounter_doc.reload()
        encounter_doc.has_preapproval = has_preapproval
        encounter_doc.db_update()
        encounter_doc.db_update_all()
        encounter_doc.reload()

        request_ids = "<ul>"
        for row in data:
            request_ids += f"<li>{row.get('RequestedServiceID')} <br> {row.get('RequestID')}</li>"
        request_ids += "</ul>"

        encounter_doc.add_comment(
            comment_type="Comment",
            text=f"Pre-approval request canceled successfully!<br>Pre-Approval No: <b>{preapproval_no}</b><br>NHIF RequestID(s): {request_ids}"
        )

        return True



def get_preliminary_diseases(doc):
    diseases = []
    for row in doc.patient_encounter_preliminary_diagnosis:
        disease_code = ""

        # Convert the ICD code of CDC to NHIF
        if row.code and len(row.code) > 3 and "." not in row.code:
            disease_code = row.code[:3] + "." + (row.code[3:4] or "0")
        elif row.code and len(row.code) <= 5 and "." in row.code:
            disease_code = row.code
        else:
            disease_code = row.code[:3]
        
        diseases.append({
            "diseaseCode": disease_code,
            "status": ""
        })
    
    return diseases


def get_encounter_services(doc, preapproval_no=None):
    diseases = []
    services = []
    service_map = {}

    for child in get_childs_map():
        for row in doc.get(child.get("table")):
            if not row.get(child.get("item")):
                continue

            if preapproval_no and row.preapproval_no == preapproval_no:
                services.append(row.get(child.get("item")))

                continue
            
            if (
                row.get("prescribe")
                or row.get("is_not_available_inhouse")
                or row.get("is_cancelled")
                or row.get("is_restricted")
                or row.get("preapproval_status") == "Accepted"
            ):
                continue

            ref_code = get_item_refcode(child.get("doctype"), row.get(child.get("item")))
            services.append({
                "itemCode": ref_code,
                "usage": "",
                "effectiveDate": str(doc.encounter_date),
                "endDate":str(add_days(doc.encounter_date, 1)),
                "quantityRequested": row.get("quantity") or 1,
                "remarks": ""
            })
            
            service_map[row.get("doctype"), row.get("name"), row.get(child.get("item"))] = ref_code
            
            medical_code = row.get("medical_code") or ""
            disease_row = {
                "diseaseCode":  get_disease_code(medical_code[6:])
            }
            if child.get("table") in ["lab_test_prescription", "radiology_procedure_prescription"]:
                disease_row["status"] = "Preliminary"
            else:
                disease_row["status"] = "Final"
            
            diseases.append(disease_row)

    return services, service_map, diseases

