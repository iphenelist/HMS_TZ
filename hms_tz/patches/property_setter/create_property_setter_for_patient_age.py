import frappe
from frappe.custom.doctype.property_setter.property_setter import make_property_setter

def execute():
    properties = [
        {
            "doctype": "Patient Encounter", 
            "value": "appointment.patient_age",
        },
        {
            "doctype": "Lab Test", 
            "value": "ref_docname.patient_age",
        },
        {
            "doctype": "Clinical Procedure", 
            "value": "ref_docname.patient_age",
        },
        {
            "doctype": "Therapy Session", 
            "value": "appointment.patient_age",
        },
    ]

    for property in properties:
        make_property_setter(
            property.get("doctype"),
            "patient_age",
            "fetch_from",
            property.get("value"),
            "Small Text",
            "DocField",
            "False"
        )
    
    frappe.db.commit()