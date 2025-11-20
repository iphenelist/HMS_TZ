import frappe
from frappe.utils import getdate, nowdate


@frappe.whitelist()
def get_nhif_practitioner_login_status(company):
    date_loggedin = frappe.get_cached_value(
        "Healthcare Practitioner",
        {"user_id": frappe.session.user},
        "date_loggedin_to_nhif",
    )

    validate_nhif_attandance = frappe.get_cached_value(
        "HMS TZ Setting",
        company,
        "validate_nhif_practitioner_attendance",
    )
    if (
        validate_nhif_attandance and 
        (
            not date_loggedin or (getdate(date_loggedin) != getdate(nowdate()))
        )
    ):
        return False

    return True
