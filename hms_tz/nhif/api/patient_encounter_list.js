frappe.listview_settings["Patient Encounter"] = {
    filters: [
        ["docstatus", "!=", "2"], ["duplicated", "==", "0"], ["finalized", "==", 0]
    ],
}