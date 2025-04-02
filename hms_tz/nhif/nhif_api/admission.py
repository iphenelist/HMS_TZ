import json
import frappe
import requests
from frappe.utils import get_url_to_form, get_fullname
from hms_tz.nhif.api.healthcare_utils import get_item_rate
from hms_tz.nhif.doctype.nhif_response_log.nhif_response_log import add_log


@frappe.whitelist()
def get_admission_types(company=None, caller=None):
    if not company:
        settings = frappe.db.get_all("HMS TZ Settings", filters={"enable_nhif_api": 1}, fields=["company"])
        company = settings[0].company
    
    if not company:
        return
    
    settings_doc = frappe.get_cached_doc("HMS TZ Settings", company)

    token = settings_doc.get_nhif_token()

    url = f"{settings_doc.nhif_claim_url}/api/Admissions/GetAdmissionTypes"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    r = requests.request("Get", url, headers=headers, timeout=60)
    if r.status_code != 200:
        add_log(
            request_type="GetAdmissionTypes",
            request_url=url,
            request_header=headers,
            request_body="",
            response_data=r.text,
            status_code=r.status_code,
            company=settings_doc.name,
            ref_doctype="Healthcare Admission Type",
        )

    else:
        data = json.loads(r.text)
        add_log(
            request_type="GetAdmissionTypes",
            request_url=url,
            request_header=headers,
            request_body="",
            response_data=data,
            status_code=r.status_code,
            company=settings_doc.name,
            ref_doctype="Healthcare Admission Type",
        )

        if len(data) == 0:
            return
        
        for row in data:
            admission = frappe.db.get_value("Healthcare Admission Type", {"admission_type_name": row["AdmissionTypeName"]}, "name")
            if admission:
                has_changed = False
                doc = frappe.get_doc("Healthcare Admission Type", admission)

                if doc.admission_type_name != row["AdmissionTypeName"]:
                    doc.admission_type_name = row["AdmissionTypeName"]
                    has_changed = True
                
                if doc.alias != row["Alias"]:
                    doc.alias = row["Alias"]
                    has_changed = True
                
                if doc.admission_type_id != row["AdmissionTypeID"]:
                    doc.admission_type_id = row["AdmissionTypeID"]
                    has_changed = True
                
                if has_changed:
                    doc.save(ignore_permissions=True)
                
            else:
                doc = frappe.new_doc("Healthcare Admission Type")
                doc.admission_type_name = row["AdmissionTypeName"]
                doc.alias = row["Alias"]
                doc.admission_type_id = row["AdmissionTypeID"]

                doc.save(ignore_permissions=True)
        
        if company and caller == 'Front End':
            frappe.msgprint("successfully fetched Admission Types", alert=True, indicator="green")


@frappe.whitelist()
def get_discharge_types(company=None, caller=None):
    if not company:
        settings = frappe.db.get_all("HMS TZ Settings", filters={"enable_nhif_api": 1}, fields=["company"])
        company = settings[0].company
    
    if not company:
        return
    
    settings_doc = frappe.get_cached_doc("HMS TZ Settings", company)

    token = settings_doc.get_nhif_token()

    url = f"{settings_doc.nhif_claim_url}/api/Admissions/GetDischargeTypes"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    r = requests.request("Get", url, headers=headers, timeout=60)
    if r.status_code != 200:
        add_log(
            request_type="GetDischargeTypes",
            request_url=url,
            request_header=headers,
            request_body="",
            response_data=r.text,
            status_code=r.status_code,
            company=settings_doc.name,
            ref_doctype="Healthcare Discharge Type",
        )

    else:
        data = json.loads(r.text)
        add_log(
            request_type="GetDischargeTypes",
            request_url=url,
            request_header=headers,
            request_body="",
            response_data=data,
            status_code=r.status_code,
            company=settings_doc.name,
            ref_doctype="Healthcare Discharge Type",
        )

        if len(data) == 0:
            return
        
        for row in data:
            discharge_type = frappe.db.get_value("Healthcare Discharge Type", {"discharge_type_name": row["DischargeTypeName"]}, "name")
            if discharge_type:
                has_changed = False
                doc = frappe.get_doc("Healthcare Discharge Type", discharge_type)

                if doc.discharge_type_name != row["DischargeTypeName"]:
                    doc.discharge_type_name = row["DischargeTypeName"]
                    has_changed = True
                
                if doc.alias != row["Alias"]:
                    doc.alias = row["Alias"]
                    has_changed = True
                
                if doc.discharge_type_id != row["DischargeTypeID"]:
                    doc.discharge_type_id = row["DischargeTypeID"]
                    has_changed = True
                
                if has_changed:
                    doc.save(ignore_permissions=True)
                
            else:
                doc = frappe.new_doc("Healthcare Discharge Type")
                doc.admission_type_name = row["DischargeTypeName"]
                doc.alias = row["Alias"]
                doc.admission_type_id = row["DischargeTypeID"]

                doc.save(ignore_permissions=True)
        
        if company and caller == 'Front End':
            frappe.msgprint("successfully fetched Discharge Types", alert=True, indicator="green")


@frappe.whitelist()
def get_ward_types(company=None, caller=None):
    if not company:
        settings = frappe.db.get_all("HMS TZ Settings", filters={"enable_nhif_api": 1}, fields=["company"])
        company = settings[0].company
    
    if not company:
        return
    
    settings_doc = frappe.get_cached_doc("HMS TZ Settings", company)

    token = settings_doc.get_nhif_token()

    url = f"{settings_doc.nhif_claim_url}/api/Admissions/GetWardTypes"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    r = requests.request("Get", url, headers=headers, timeout=60)
    if r.status_code != 200:
        add_log(
            request_type="GetWardTypes",
            request_url=url,
            request_header=headers,
            request_body="",
            response_data=r.text,
            status_code=r.status_code,
            company=settings_doc.name,
            ref_doctype="Healthcare Ward Type",
        )

    else:
        data = json.loads(r.text)
        add_log(
            request_type="GetWardTypes",
            request_url=url,
            request_header=headers,
            request_body="",
            response_data=data,
            status_code=r.status_code,
            company=settings_doc.name,
            ref_doctype="Healthcare Ward Type",
        )

        if len(data) == 0:
            return
        
        for row in data:
            ward_type = frappe.db.get_value("Healthcare Ward Type", {"ward_type_name": row["WardTypeName"]}, "name")
            if ward_type:
                has_changed = False
                doc = frappe.get_doc("Healthcare Ward Type", ward_type)

                if doc.ward_type_name != row["WardTypeName"]:
                    doc.ward_type_name = row["WardTypeName"]
                    has_changed = True
                
                if doc.alias != row["Alias"]:
                    doc.alias = row["Alias"]
                    has_changed = True
                
                if doc.ward_type_id != row["WardTypeID"]:
                    doc.ward_type_id = row["WardTypeID"]
                    has_changed = True
                
                if doc.notification_required_after != row["NotificationRequiredAfter"]:
                    doc.notification_required_after = row["NotificationRequiredAfter"]
                    has_changed = True
                
                if doc.item_code != row["ItemCode"]:
                    doc.item_code = row["ItemCode"]
                    has_changed = True
                
                if has_changed:
                    doc.save(ignore_permissions=True)
                
            else:
                doc = frappe.new_doc("Healthcare Ward Type")
                doc.ward_type_name = row["WardTypeName"]
                doc.alias = row["Alias"]
                doc.ward_type_id = row["WardTypeID"]
                doc.notification_required_after = row["NotificationRequiredAfter"]
                doc.item_code = row["ItemCode"]

                doc.save(ignore_permissions=True)
        
        if company and caller == 'Front End':
            frappe.msgprint("successfully fetched Ward Types", alert=True, indicator="green")


@frappe.whitelist()
def get_room_types(company=None, caller=None):
    if not company:
        settings = frappe.db.get_all("HMS TZ Settings", filters={"enable_nhif_api": 1}, fields=["company"])
        company = settings[0].company
    
    if not company:
        return
    
    settings_doc = frappe.get_cached_doc("HMS TZ Settings", company)

    token = settings_doc.get_nhif_token()

    url = f"{settings_doc.nhif_claim_url}/api/Admissions/GetRoomTypes"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    r = requests.request("Get", url, headers=headers, timeout=60)
    if r.status_code != 200:
        add_log(
            request_type="GetRoomTypes",
            request_url=url,
            request_header=headers,
            request_body="",
            response_data=r.text,
            status_code=r.status_code,
            company=settings_doc.name,
            ref_doctype="Healthcare Room Type",
        )

    else:
        data = json.loads(r.text)
        add_log(
            request_type="GetRoomTypes",
            request_url=url,
            request_header=headers,
            request_body="",
            response_data=data,
            status_code=r.status_code,
            company=settings_doc.name,
            ref_doctype="Healthcare Room Type",
        )

        if len(data) == 0:
            return
        
        for row in data:
            room_type = frappe.db.get_value("Healthcare Room Type", {"room_type_name": row["RoomTypeName"]}, "name")
            if ward_type:
                has_changed = False
                doc = frappe.get_doc("Healthcare Room Type", ward_type)

                if doc.room_type_name != row["RoomTypeName"]:
                    doc.room_type_name = row["RoomTypeName"]
                    has_changed = True
                
                if doc.alias != row["Alias"]:
                    doc.alias = row["Alias"]
                    has_changed = True
                
                if doc.room_type_id != row["RoomTypeID"]:
                    doc.room_type_id = row["RoomTypeID"]
                    has_changed = True
                
                if has_changed:
                    doc.save(ignore_permissions=True)
                
            else:
                doc = frappe.new_doc("Healthcare Room Type")
                doc.room_type_name = row["RoomTypeName"]
                doc.alias = row["Alias"]
                doc.room_type_id = row["RoomTypeID"]

                doc.save(ignore_permissions=True)
        
        if company and caller == 'Front End':
            frappe.msgprint("successfully fetched Room Types", alert=True, indicator="green")


@frappe.whitelist()
def admit_patient(
    admission_type,
    service_unit,
    date_admitted,
    ref_doctype,
    ref_docname
):
    inpatient_doc = frappe.get_cached_doc("Inpatient Record", ref_docname)
    mct_code = frappe.get_cached_value(
        "Healthcare Practitioner",
        inpatient_doc.admission_practitioner,
        ["tz_mct_code"]
    ),

    authorization_no = frappe.get_cached_value(
        "Patient Appointment",
        inpatient_doc.patient_appointment,
        "authorization_number"
    )

    admission_type_id = frappe.get_cached_value(
        "Healthcare Admission Type",
        admission_type,
        "admission_type_id"
    )

    service_unit_type = inpatient_doc.admission_service_unit_type
    ward_type, item_code = frappe.get_cached_value(
        "Healthcare Service Unit Type",
        service_unit_type,
        ["ward_type", "item_code"]
    )
    if not ward_type:
        url = get_url_to_form("Healthcare Service Unit Type", service_unit_type)
        frappe.throw(
            f"Please select 'Ward Type' on Service Unit Type: <a href='{url}'><b>{service_unit_type}</b></a>"
        )
    
    ward_type_id = frappe.get_cached_value("Healthcare Ward Type", ward_type, "ward_type_id")

    room_type = frappe.get_cached_value("Healthcare Service Unit", service_unit, "room_type")
    if not room_type:
        url = get_url_to_form("Healthcare Service Unit", service_unit)
        frappe.throw(f"Please select 'Room Type' for Service Unit: <a href='{url}'><b>{service_unit}</b></a>")
    
    room_type_id = frappe.get_cached_value("Healthcare Room Type", room_type, "room_type_id")

    bed_charge = get_item_rate(item_code, inpatient_doc.company, npatient_doc.insurance_subscription)
    payload = {
        "authorizationNo": authorization_no,
        "fullName": inpatient_doc.patient_name,
        "gender": inpatient_doc.gender,
        "dateOfBirth": inpatient_doc.dob,
        "admissionTypeID": admission_type_id,
        "wardTypeID": ward_type_id,
        "roomTypeID": room_type_id,
        "chargesPerDay": bed_charge,
        "practitionerNo": mct_code,
        "diagnosisAtAdmission": "",
        "practitionersRemarks": inpatient_doc.admission_instruction or "",
        "dateAdmitted": date_admitted,
        "createdBy": get_fullname(inpatient_doc.owner)
    }

    payload = json.dumps(payload)

    settings_doc = frappe.get_cached_doc("HMS TZ Settings", inpatient_doc.company)

    token = settings_doc.get_nhif_token()

    url = f"{settings_doc.nhifservice_url}/api/Admissions/AdmitPatient"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    r = requests.request("Get", url, data=payload, headers=headers, timeout=60)
    if r.status_code != 200:
        add_log(
            request_type="AdmitPatient",
            request_url=url,
            request_header=headers,
            request_body=payload,
            response_data=r.text,
            status_code=r.status_code,
            company=settings_doc.name,
            ref_doctype=ref_doctype,
            ref_docname=ref_docname
        )

    else:
        data = json.loads(r.text)
        add_log(
            request_type="AdmitPatient",
            request_url=url,
            request_header=headers,
            request_body=payload,
            response_data=data,
            status_code=r.status_code,
            company=settings_doc.name,
            ref_doctype=ref_doctype,
            ref_docname=ref_docname
        )

        return data