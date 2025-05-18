import frappe
from frappe.utils import getdate, nowdate


@frappe.whitelist()
def get_nhif_practitioner_login_status():
    date_loggedin = frappe.get_cached_value(
        "Healthcare Practitioner",
        {"user_id": frappe.session.user},
        "date_loggedin_to_nhif",
    )

    if not date_loggedin or (getdate(date_loggedin) != getdate(nowdate())):
        return False

    return True
