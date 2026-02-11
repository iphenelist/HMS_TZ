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

    # 3. hms_tz-specific setup
    # setup_hms_tz_test_data()

    frappe.db.commit()


def setup_hms_tz_test_data():
    """Create any additional master data specific to hms_tz tests."""
    return