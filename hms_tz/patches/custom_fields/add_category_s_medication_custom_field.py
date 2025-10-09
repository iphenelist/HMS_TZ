import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def execute():
    fields = {
        "Company": [
            {
                "fieldname": "validate_category_s_medication",
                "label": "Validate Category S Medication",
                "fieldtype": "Check",
                "insert_after": "hms_tz_minimum_cash_limit_percent",
                "default": 1,
                "search_index": 1,
                "description": "If ticked, validation for Category S Medication will be done at encounter level for NHIF Patients and General Practitioners (GP)",
            }
        ]
    }

    create_custom_fields(fields, update=True)
