from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    fields = {
        "Patient Appointment": [
            {
                "fieldname": "apply_fasttrack_charge",
                "fieldtype": "Check",
                "label": "Apply Fasttrack Charge",
                "insert_after": "column_break_49",
            },
        ],
        "Appointment Type": [
            {
                "fieldname": "source_sec",
                "fieldtype": "Section Break",
                "insert_after": "items",
            },
            {
                "fieldname": "fasttrack_cb",
                "fieldtype": "Column Break",
                "insert_after": "visit_type_id",
            },
            {
                "fieldname": "follow_up_item",
                "fieldtype": "Link",
                "options": "Item",
                "label": "Follow Up Item",
                "insert_after": "fasttrack_cb",
            },
            {
                "fieldname": "gp_fasttrack_item",
                "fieldtype": "Link",
                "options": "Item",
                "label": "GP Fasttrack Item",
                "insert_after": "follow_up_item",
            },
            {
                "fieldname": "specialist_fasttrack_item",
                "fieldtype": "Link",
                "options": "Item",
                "label": "Specialist Fasttrack Item",
                "insert_after": "gp_fasttrack_item",
            },
            {
                "fieldname": "super_specialist_fasttrack_item",
                "fieldtype": "Link",
                "options": "Item",
                "label": "Super Specialist Fasttrack Item",
                "insert_after": "specialist_fasttrack_item",
            },
        ],
    }

    create_custom_fields(fields, update=True)
