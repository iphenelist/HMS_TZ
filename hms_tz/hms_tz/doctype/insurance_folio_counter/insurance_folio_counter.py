# Copyright (c) 2025, Aakvatech and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import cint, now_datetime


class InsuranceFolioCounter(Document):
    pass


def get_or_create_folio_counter(doc, insurance_provider: str) -> int:
    """Get the next folio number for an insurance claim.

    Queries Insurance Folio Counter filtered by company, claim_year,
    claim_month, and insurance_provider. Creates a new counter record
    if none exists, otherwise increments the existing one using
    frappe.db.set_value to avoid race conditions from a full doc save.

    Args:
        doc: The parent claim document (must have company, claim_year,
             claim_month attributes).
        insurance_provider: One of 'NHIF', 'Jubilee', 'Strategies',
                            'Assembly'.

    Returns:
        int: The next folio number to assign to the claim.
    """
    folio_counter = frappe.db.get_all(
        "Insurance Folio Counter",
        filters={
            "company": doc.company,
            "claim_year": doc.claim_year,
            "claim_month": doc.claim_month,
            "insurance_provider": insurance_provider,
        },
        fields=["name", "folio_no"],
        page_length=1,
    )

    folio_no = 1
    if not folio_counter:
        frappe.get_doc(
            {
                "doctype": "Insurance Folio Counter",
                "company": doc.company,
                "claim_year": doc.claim_year,
                "claim_month": doc.claim_month,
                "posting_date": now_datetime(),
                "insurance_provider": insurance_provider,
                "folio_no": folio_no,
            }
        ).insert(ignore_permissions=True)
    else:
        folio_no = cint(folio_counter[0].folio_no) + 1
        frappe.db.set_value(
            "Insurance Folio Counter",
            folio_counter[0].name,
            {
                "folio_no": folio_no,
                "posting_date": now_datetime(),
            },
        )

    return folio_no
