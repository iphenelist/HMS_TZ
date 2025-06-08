import json
import frappe
from frappe.utils import get_url_to_form
from hms_tz.nhif.nhif_api.verification import get_poc_reference_no
from hms_tz.nhif.nhif_api.approval import issue_approved_service


@frappe.whitelist()
def is_issuance_biometric_verification_enabled(doc_type, company, field):
    return frappe.get_cached_value("HMS TZ Setting", company, field)


@frappe.whitelist()
def issue_nhif_service(
    ref_doctype,
    ref_docname,
    service_type,
    service_name,
    fingerprint,
    fpcode,
    qty=1,
    biometric_method="NONE"
):
    doc = frappe.get_cached_doc(ref_doctype, ref_docname)

    settings_doc = frappe.get_cached_doc("HMS TZ Setting", doc.company)

    data = {}

    if doc.doctype == "Delivery Note":
        approval_items = []
        for row in doc.items:
            if row.is_resctricted == 1:
                if row.approval_number:
                    approval_items.append(row)
                else:
                    frappe.throw(f"Item: {row.item_code} require Approval Number to issue this Item")

        for d in approval_items:
            service_data = issue_approved_service(
                doc,
                d.approval_number,
                service_type,
                d.item_code,
                fingerprint,
                fpcode,
                qty=d.qty,
                rate=d.rate,
                settings_doc=settings_doc,
                biometric_method=biometric_method
            )

            if service_data:
                data.update(service_data)

    else:
        if doc.is_restricted == 1 and doc.approval_number:
            service_data = issue_approved_service(
                doc,
                doc.approval_number,
                service_type,
                service_name,
                fingerprint,
                fpcode,
                qty=1,
                settings_doc=settings_doc,
                biometric_method=biometric_method
            )

            if service_data:
                data.update(service_data)

    point_of_care = get_patient_care_name(service_type, service_name)
    
    if not doc.poc_reference_no:
        service_data = get_poc_reference_no(
            point_of_care=point_of_care,
            practitioner=doc.get("practitioner") or doc.get("healthcare_practitioner"),
            fingerprint=fingerprint,
            fpcode=fpcode,
            biometric_method=biometric_method,
            company=doc.company,
            appointment_id=doc.get("appointment") or doc.get("hms_tz_appointment_no"),
            authorization_no=doc.get("authorization_number") or "",
            settings_doc=settings_doc,
            ref_doctype=doc.doctype,
            ref_docname=doc.name,
        )
        if service_data:
            data.update(service_data)
    
    return data


def get_patient_care_name(service_type, service_name):
    """
    Get the name of the point of care based on service type and service name.
    """
    if not service_type:
        return None
    
    if not service_name and service_type == "Medication":
        return 'Pharmacy'

    points_of_care = frappe.get_cached_value(
        service_type,
        service_name,
        "points_of_care"
    )

    if not points_of_care:
        url = get_url_to_form(service_type, service_name)
        frappe.throw(
            f"Point of care is not set for <a href='{url}'>{frappe.bold(service_name)}</a>, Please set it first."
        )

    return points_of_care