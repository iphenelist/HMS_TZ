import json
import frappe
from frappe.utils import get_url_to_form
from hms_tz.nhif.nhif_api.verification import get_poc_reference_no
from hms_tz.nhif.nhif_api.approval import issue_approved_service


@frappe.whitelist()
def get_poc_reference_no_for_lrpmt(
    ref_doctype,
    ref_docname,
    service_type,
    service_name,
    fingerprint=None,
    fpcode=None,
    biometric_method="NONE",
):
    """
    Get POC reference number for a given document.
    """

    doc = frappe.get_cached_doc(ref_doctype, ref_docname)

    point_of_care = get_patient_care_name(service_type, service_name)

    data = get_poc_reference_no(
        point_of_care=point_of_care,
        practitioner=doc.get("practitioner") or doc.get("healthcare_practitioner"),
        fingerprint=fingerprint,
        fpcode=fpcode,
        biometric_method=biometric_method.upper(),
        company=doc.company,
        appointment_id=doc.get("appointment") or doc.get("hms_tz_appointment_no"),
        authorization_no=doc.get("authorization_number") or "",
        ref_doctype=ref_doctype,
        ref_docname=ref_docname,
    )

    if data:
        doc.db_set("poc_reference_no", data.get("ReferenceNo"))
        doc.add_comment(
            "Comment",
            text=f"POC Reference No: <strong>{data.get('ReferenceNo')}</strong> for {point_of_care} is successfully created."
        )

        records = frappe.db.get_all(
            doc.doctype,
            filters={
                "ref_docname": doc.ref_docname,
                "ref_doctype": doc.ref_doctype,
                "name": ["!=", doc.name],
            },
        )

        for record in records:
            record_doc = frappe.get_cached_doc(doc.doctype, record.name)
            if (
                not record_doc.get("insurance_company") and
                not record_doc.get("coverage_plan_name")
            ):
                continue

            record_doc.db_set("poc_reference_no", data.get("ReferenceNo"))
            record_doc.add_comment(
                "Comment",
                text=f"POC Reference No: <strong>{data.get('ReferenceNo')}</strong> for {point_of_care} is successfully created."
            )

        return True


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
            if row.is_restricted == 1:
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
                create_issued_service_log(d)

    else:
        if not doc.approval_number:
            frappe.throw(
                f"Approval Number is not set for this document, Please get Approval Number from NHIF."
            )
        
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
            create_issued_service_log(doc)

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


def validate_point_of_care(doc, field):
    """
    Validate that the point of care is set for the given document.
    """

    insurance_field = "insurance_company"
    if doc.doctype == "Delivery Note":
        insurance_field = "customer"

    if not doc.get(insurance_field) or "NHIF" not in doc.get(insurance_field, ""):
        return
    
    if not frappe.get_cached_value(
        "HMS TZ Setting",
        doc.company,
        "enable_nhif_api"
    ):
        return
    
    if not doc.get("poc_reference_no"):
        if frappe.get_cached_value(
            "HMS TZ Setting",
            doc.company,
            field
        ):
            frappe.throw(
                f"<b>POC reference</b> no is not set for this document, Please get POC reference no from NHIF."
            )


def create_issued_service_log(
    doc
):
    """
    Create a log entry for issued NHIF services.
    """

    log_doc = frappe.get_doc({
        "doctype": "Issued Service Log",
        "ref_doctype": doc.doctype,
        "ref_docname": doc.name,
        "approval_number": doc.approval_number,
    })

    log_doc.insert(ignore_permissions=True)


def validate_issued_services(
    ref_doctype,
    ref_docname,
    is_restricted=False
):
    """
    Validate if there are issued services for the given document.
    """

    if not is_restricted:
        return

    issued_services = frappe.db.get_all(
        "Issued Service Log",
        filters={
            "ref_doctype": ref_doctype,
            "ref_docname": ref_docname,
        },
    )

    if len(issued_services) == 0:
        frappe.throw(
            f"No issued services found. Please issue NHIF services before proceeding."
        )