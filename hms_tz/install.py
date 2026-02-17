import os

import frappe
from erpnext.setup.utils import before_tests as erpnext_before_tests
from healthcare.healthcare.utils import before_tests as healthcare_before_tests

from hms_tz.patches.custom_fields.create_custom_fields import execute as create_custom_fields
from hms_tz.patches.property_setter.create_property_setters import execute as create_property_setters


def after_install():
    """Hook called after hms_tz app installation on a site."""
    create_accounting_dimensions()
    frappe.db.commit()


def create_accounting_dimensions():
    """Create Accounting Dimensions for Healthcare Practitioner and Healthcare Service Unit.

    These dimensions add corresponding custom fields on all applicable
    accounting doctypes (Sales Invoice, Purchase Invoice, Journal Entry, etc.).
    hms_tz code relies on these fields existing on transaction line items.
    """
    dimensions = [
        {
            "document_type": "Healthcare Practitioner",
            "label": "Healthcare Practitioner",
        },
        {
            "document_type": "Healthcare Service Unit",
            "label": "Healthcare Service Unit",
        },
    ]

    for dimension_data in dimensions:
        document_type = dimension_data["document_type"]

        if frappe.db.exists("Accounting Dimension", {"document_type": document_type}):
            continue

        try:
            doc = frappe.new_doc("Accounting Dimension")
            doc.document_type = document_type
            doc.label = dimension_data["label"]
            doc.disabled = 0
            doc.save(ignore_permissions=True)
            frappe.db.commit()
        except Exception:
            frappe.log_error(
                title=f"Error creating Accounting Dimension for '{document_type}'",
                message=frappe.get_traceback(),
            )
            frappe.db.rollback()


def before_tests():
    """Setup required master data before running tests.

    When ``bench run-tests --app hms_tz`` is executed, Frappe's test runner
    only invokes ``before_tests`` hooks registered by *hms_tz* (because it
    passes ``app_name="hms_tz"`` to ``frappe.get_hooks``).  ERPNext's and
    Healthcare's ``before_tests`` hooks — which bootstrap the full setup
    wizard, fixture records, healthcare master data, etc. — are **not**
    called automatically.

    This function therefore delegates to the upstream apps first,
    ensuring the test database has all required master data (Company,
    Chart of Accounts, Warehouse Types, Genders, Medical Departments,
    Item Groups, etc.) before hms_tz's own test records are created.
    """

    # 1. ERPNext: runs setup_complete() → install_fixtures (Warehouse Types,
    #    Genders, Item Groups, Territories, etc.), creates Company, Fiscal Year,
    #    enables all roles for Administrator, sets selling/stock defaults.
    erpnext_before_tests()

    # 2. Healthcare: creates Frappe Care LLC (if needed), Medical Departments,
    #    Antibiotics, Lab Test UOMs, Dosages, Prescription Durations,
    #    Healthcare Item Groups, Sensitivities, Healthcare Service Units, etc.
    healthcare_before_tests()

    # 3. hms_tz accounting dimensions (Healthcare Practitioner, Healthcare Service Unit)
    create_accounting_dimensions()

    # 4. hms_tz master data required by tests (lookup records for mandatory fields)
    create_test_master_data()

    # 5. hms_tz-specific setup: custom fields, property setters, etc.
    setup_hms_tz_test_data()

    frappe.db.commit()


def setup_hms_tz_test_data():
    """Create all hms_tz custom fields and property setters.

    The test runner does not trigger migrations or after_migrate hooks,
    so we must apply all custom fields and property setters explicitly.

    Ordering is critical:
    1. Custom fields must be created FIRST (both Python patches and JSON).
    2. Property setters run AFTER, because some set doctype-level properties
       like ``image_field`` to a custom fieldname. If that fieldname doesn't
       exist yet, Frappe's field validation fails on the next custom field
       insert for that doctype.
    """
    patches_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "patches.txt"
    )

    with open(patches_file) as f:
        patches = f.read().splitlines()

    custom_field_patches = []
    property_setter_patches = []

    for patch_path in patches:
        patch_path = patch_path.strip()
        if not patch_path or patch_path.startswith("[") or patch_path.startswith("#"):
            continue

        if ".custom_fields." in patch_path:
            custom_field_patches.append(patch_path)
        elif ".property_setter." in patch_path:
            property_setter_patches.append(patch_path)

    # Phase 1: Create all custom fields (Python patches then JSON-based)
    for patch_path in custom_field_patches:
        try:
            frappe.get_attr(patch_path + ".execute")()
        except Exception as e:
            frappe.log_error(
                title=f"hms_tz before_tests: patch failed - {patch_path}",
                message=str(e),
            )

    create_custom_fields()

    # Phase 2: Apply all property setters (Python patches then JSON-based)
    for patch_path in property_setter_patches:
        try:
            frappe.get_attr(patch_path + ".execute")()
        except Exception as e:
            frappe.log_error(
                title=f"hms_tz before_tests: patch failed - {patch_path}",
                message=str(e),
            )

    create_property_setters()


def create_test_master_data():
    """Create lookup records needed by mandatory custom fields on Patient, etc.

    These are hms_tz doctypes whose records must exist before test Patient
    documents can be saved (the custom fields are reqd=1).
    """
    master_records = [
        {"doctype": "Occupation", "occupation": "Secretary"},
        {"doctype": "Ethnicity", "ethnicity": "African"},
        {"doctype": "Demography", "demography": "City Centre"},
        {"doctype": "Healthcare Ward Type", "ward_type_name": "General Ward"},
        {"doctype": "Healthcare Points of Care", "point_of_care_name": "Phisiotherapy"},
    ]

    # Campaign is a Frappe/CRM doctype used by how_did_you_hear_about_us
    if not frappe.db.exists("Campaign", "I know you"):
        try:
            frappe.get_doc({"doctype": "Campaign", "campaign_name": "I know you"}).insert(
                ignore_permissions=True
            )
        except Exception:
            pass

    for record in master_records:
        dt = record["doctype"]
        # The name is derived from the naming field; use the first non-doctype value
        name_value = list(record.values())[1]
        if not frappe.db.exists(dt, name_value):
            try:
                frappe.get_doc(record).insert(ignore_permissions=True)
            except Exception:
                frappe.log_error(
                    title=f"hms_tz before_tests: failed to create {dt} '{name_value}'",
                    message=frappe.get_traceback(),
                )