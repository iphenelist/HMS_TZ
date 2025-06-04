import json
import frappe
from hms_tz.nhif.nhif_api.verification import get_poc_reference_no
from hms_tz.nhif.nhif_api.approval import issue_approved_service


@frappe.whitelist()
def is_issuance_biometric_verification_enabled(doc_type, company, field):
    return frappe.get_cached_value("HMS TZ Setting", company, field)


@frappe.whitelist()
def issue_nhif_service(
    ref_doctype,
    ref_docname,
    point_of_care,
    service_type,
    service_name,
    fingerprint,
    fpcode,
    qty=1,
    biometric_method="NONE"
):
    doc = frappe.get_cached_doc(ref_doctype, ref_docname)
    settings_doc = frappe.get_cached_doc("HMS TZ Setting", doc.company)

    poc_reference = get_poc_reference_no(
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

    if doc.doctype != "Delivery Note":
        if doc.is_restricted == 1 and doc.approval_number:
            issue_approved_service(
                doc,
                service_type,
                service_name,
                fingerprint,
                fpcode,
                qty=1,
                settings_doc=settings_doc,
                biometric_method=biometric_method
            )

    else:
        for row in doc.items:
            if (
                row.is_resctricted == 0 or
                not row.approval_number
            ):
                continue
            
            issue_approved_service(
                doc,
                service_type,
                row.item_code,
                fingerprint,
                fpcode,
                qty=row.qty,
                rate=row.rate,
                settings_doc=settings_doc,
                biometric_method=biometric_method
            )

    return poc_reference


