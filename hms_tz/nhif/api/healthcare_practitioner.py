import frappe
from erpnext import get_default_company
from frappe.utils import getdate, nowdate


@frappe.whitelist()
def get_nhif_practitioner_login_status(company=None):
    if not company:
        company = get_default_company()

        if not company:
            company = frappe.get_cached_value(
                "Healthcare Practitioner",
                {"user_id": frappe.session.user},
                "hms_tz_company",
            )

    validate_nhif_attandance = frappe.get_cached_value(
        "HMS TZ Setting",
        company,
        "validate_nhif_practitioner_attendance",
    )

    if not validate_nhif_attandance:
        return {"show_login": False, "show_logout": False}
    
    date_loggedin = frappe.get_cached_value(
        "Healthcare Practitioner",
        {"hms_tz_company": company, "user_id": frappe.session.user},
        "date_loggedin_to_nhif",
    )

    if (
        not date_loggedin or (getdate(date_loggedin) != getdate(nowdate()))
    ):
        return {"show_login": True, "show_logout": False}
    
    elif date_loggedin and (getdate(date_loggedin) == getdate(nowdate())):
        return {"show_login": False, "show_logout": True}
