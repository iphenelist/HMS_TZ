import json
import frappe
import requests


@frappe.whitelist()
def get_service_preapproval(
    encounter_doc,
    authorization_no=None,
    settings_doc=None, 
    ref_doctype=None, 
    ref_docname=None,
    card_no=None
):
    services, service_refs = get_encounter_services(encounter_doc)
    if len(services) == 0:
        frappe.msgprint("No servuce(s) to request an Pre-Approvals")

    if not settings_doc:
        settings_doc = frappe.get_cached_doc("HMS TZ Settings", encounter_doc.company)
    
    first_name, last_name, dob = frappe.get_cached_value(
        "Patient",
        encounter_doc.patient,
        ["first_name", "last_name", "dob"]
    )
    mct_code, mobile = frappe.get_cached_value(
            "Healthcare Practitioner",
            encounter_doc.practitioner,
            ["tz_mct_code", "mobile_phone"]
        ),
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
        "dateOfBirth": dob,
        "patientFileNo": encounter_doc.patient,
        "clinicalNotes": encounter_doc.examination_detail,
        "practitionerNo": mct_code,
        "practitionersRemarks": "",
        "telephoneNo": mobile,
        "diseases": get_preliminary_diseases(encounter_doc),
        "requestedServices": services
    }
    payload = json.dumps(payload)

    url = f"{settings_doc.nhifservice_url}/api/PreApprovals/RequestServices"

    token = settings_doc.get_nhif_token()
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    r = requests.request("Post", url, data=payload, headers=headers, timeout=60)
    if r.status_code == 200:
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
            card_no=card_no
        )

        return {"service_refs": service_refs, "data": data}
    else:
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
            card_no=card_no
        )
        return None


@frappe.whitelist()
def cancel_preapproval(
    request_no,
    remarks,
    settings_doc=None,
    ref_doctype=None, 
    ref_docname=None,
    ref_child_doctype=None,
    ref_child_docnmae=None,
    card_no=None
):
    if not settings_doc:
        settings_doc = frappe.get_cached_doc("HMS TZ Settings", encounter_doc.company)
    
    url = f"{settings_doc.nhifservice_url}/api/PreApprovals/CancelRequest?requestNo={request_no}&remarks={remarks}"

    token = settings_doc.get_nhif_token()
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    r = requests.request("Post", url, headers=headers, timeout=60)
    if r.status_code == 200:
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
            card_no=card_no
        )
        # TODO: update the canceled response on encounter's child doc or service request's child doc

    else:
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
            card_no=card_no
        )
        return None


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


def get_encounter_services(doc):
    services = []
    service_refs = []

    for child in get_field_map():
        for row in doc.get(child.get("table")):
            if (
                row.prescribe
                or row.is_not_available_inhouse
                or row.is_cancelled,
                # TODO: remember to excluded services that already been asked for approval
            ):
                continue

            item_code = frappe.get_cached_value(
                child.get("doctype"), row.get(child.get("item")), "item"
            )
            if not item_code:
                frappe.throw(
                    _(
                        f"Item code for {row.get(child.get('item'))} set in row {row.idx} was not found.<br>Please set the item code in {child.get('doctype')}."
                    )
                )
            
            ref_code = frappe.db.get_cached("Item Customer Detail", {"parent": item_code, "customer_name": "NHIF"}, "ref_code")

            services.append({
                "itemCode": ref_code,
                "usage": "",
                "effectiveDate": doc.encounter_date,
                "endDate": "",
                "quantityRequested": row.get("quantity") or 1,
                "remarks": ""
            })
            
            service_refs.append({
                "ref_doctype": row.doctype,
                "ref_docname": row.name,
                "service_name": row.get(child.get("item")),
                "ref_code": ref_code
            })
        
    return services, service_refs


def get_field_map():
    childs_map = [
        {
            "table": "lab_test_prescription",
            "doctype": "Lab Test Template",
            "item": "lab_test_code",
        },
        {
            "table": "radiology_procedure_prescription",
            "doctype": "Radiology Examination Template",
            "item": "radiology_examination_template",
        },
        {
            "table": "procedure_prescription",
            "doctype": "Clinical Procedure Template",
            "item": "procedure",
        },
        {
            "table": "drug_prescription",
            "doctype": "Medication",
            "item": "drug_code",
        },
        {
            "table": "therapies",
            "doctype": "Therapy Type",
            "item": "therapy_type",
        },
    ]
    return childs_map