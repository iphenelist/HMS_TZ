import frappe
from erpnext.setup.utils import before_tests as erpnext_before_tests
from healthcare.healthcare.utils import before_tests as healthcare_before_tests


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

    # 3. hms_tz-specific setup: custom fields, property setters, etc.
    setup_hms_tz_test_data()

    frappe.db.commit()


def setup_hms_tz_test_data():
    """Create all hms_tz custom fields and property setters.

    The test runner does not trigger migrations or after_migrate hooks,
    so we must apply all custom fields and property setters explicitly.

    This runs:
    1. All individual Python patches from patches.txt that create custom
       fields or property setters (~37 custom field + ~10 property setter
       patches covering ~58 doctypes).
    2. The JSON-based create_custom_fields/create_property_setters used
       by after_migrate hooks (covers ~26 doctypes from exported JSON).

    Together these ensure the full schema that hms_tz code expects.
    """
    import os

    patches_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "patches.txt"
    )

    with open(patches_file) as f:
        patches = f.read().splitlines()

    # Run all custom_fields and property_setter patches from patches.txt
    for patch_path in patches:
        patch_path = patch_path.strip()
        if not patch_path or patch_path.startswith("[") or patch_path.startswith("#"):
            continue

        if ".custom_fields." not in patch_path and ".property_setter." not in patch_path:
            continue

        try:
            frappe.get_attr(patch_path + ".execute")()
        except Exception as e:
            frappe.log_error(
                title=f"hms_tz before_tests: patch failed - {patch_path}",
                message=str(e),
            )

    # Also run the JSON-based after_migrate hooks (covers additional fields
    # exported from a live site that may not be in the Python patches).
    from hms_tz.patches.custom_fields.create_custom_fields import execute as create_custom_fields
    from hms_tz.patches.property_setter.create_property_setters import execute as create_property_setters

    create_custom_fields()
    create_property_setters()