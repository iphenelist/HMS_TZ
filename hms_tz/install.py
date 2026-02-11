import frappe


def before_tests():
    """Setup required master data before running tests.

    ERPNext's setup wizard normally creates certain records (like Warehouse Types)
    that are needed when Company test records are inserted. Since the wizard doesn't
    run in CI, we ensure these records exist here.
    """
    create_warehouse_types()


def create_warehouse_types():
    warehouse_types = ["Transit"]
    for wt in warehouse_types:
        if not frappe.db.exists("Warehouse Type", wt):
            frappe.get_doc({"doctype": "Warehouse Type", "name": wt}).insert(
                ignore_permissions=True
            )
