import frappe
from frappe.query_builder import DocType


@frappe.whitelist()
def create_appointment(appointment_data):
    """
    Create a new appointment with the provided data.
    """
    
    # frappe.throw(str(appointment_data))
    appointment_doc = frappe.new_doc("Patient Appointment")
    appointment_doc.update(appointment_data)

    if appointment_data.get("payment_mode") == "Cash":
        mode_of_payment = get_mode_of_payment()
        appointment_doc.mode_of_payment = mode_of_payment
    
    appointment_doc.save(ignore_permissions=True)
    appointment_doc.reload()

    return appointment_doc.reload()


def get_mode_of_payment():
    """
    Fetch mode of payment using user id from user permission
    """

    user = frappe.session.user
    mp = DocType("Mode of Payment")
    up = DocType("User Permission")

    mp_data = (
        frappe.qb.from_(mp)
        .inner_join(up)
        .on(up.for_value == mp.name)
        .select(mp.name.as_("mode_of_payment"), mp.type.as_("type"))
        .where(
            (up.user == user) 
            & (up.allow == "Mode of Payment")
            & (mp.type == "Cash")
        )
    ).run(as_dict=True)

    if len(mp_data) == 0:
        frappe.throw(f"No mode of payment found for user: {user}")

    return mp_data[0].get("mode_of_payment", "")


@frappe.whitelist()
def get_user_roles():
    """
    Fetch user roles.
    """
    
    user = frappe.session.user
    roles = frappe.get_roles(user)
    
    if not roles:
        frappe.throw(f"No roles found for user: {user}")
    
    return roles