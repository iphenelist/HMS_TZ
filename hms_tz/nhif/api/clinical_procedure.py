# -*- coding: utf-8 -*-
# Copyright (c) 2020, Aakvatech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import frappe
from frappe import _
from frappe.query_builder import DocType
from frappe.utils import get_fullname, nowdate

from hms_tz.hms_tz.doctype.hospital_revenue_entry.hospital_revenue_entry import (
    create_revenue_entry,
    update_revenue_entry,
)
from hms_tz.nhif.api.healthcare_utils import create_delivery_note_from_LRPT
from hms_tz.nhif.api.lab_test import check_cash_payments_from_encounter
from hms_tz.nhif.utils import validate_issued_services, validate_point_of_care


def after_insert(doc, method):
    create_revenue_entry(doc)


def onload(doc, method):
    check_cash_payments_from_encounter(
        doc=doc,
        ref_doctype="ref_doctype",
        ref_docname_field="ref_docname",
        prescription_field="procedure_prescription",
        item_name_field="procedure_name",
        item_descriptor="Clinical Procedures",
    )


def on_submit(doc, methd):
    validate_swab_count(doc)
    update_procedure_prescription(doc)
    update_revenue_entry(
        "Clinical Procedure",
        doc.name,
        "Procedure Prescription",
        doc.hms_tz_ref_childname,
        lrpmt_status="Submitted",
    )


def before_submit(doc, method):
    if not doc.procedure_notes:
        frappe.throw(
            title= _("<b style='color: red; font-size: 16px; font-weight: bold;'>Procedure Notes Missing</b>"),
            msg=_(
                """<div style='border-left: 4px solid #ffc107; background-color: #fff3cd; padding: 15px; border-radius: 10px; box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1); margin: 10px;'>
                    <p style='font-size: 16px;'>Procedure notes are required. Please write the Procedure Notes.</p>
                </div>"""
            )
        )

    if doc.is_restricted and not doc.approval_number:
        frappe.throw(
            _(f"Approval number is required for <b>{doc.procedure_template}</b>. Please set the Approval Number.")
        )

    validate_point_of_care(doc, "validate_poc_at_procedure")
    validate_issued_services(doc.doctype, doc.name, is_restricted=doc.is_restricted, company=doc.company)

    doc.hms_tz_submitted_by = get_fullname(frappe.session.user)
    doc.hms_tz_user_id = frappe.session.user
    doc.hms_tz_submitted_date = nowdate()


def create_delivery_note(doc):
    if doc.ref_doctype and doc.ref_docname and doc.ref_doctype == "Patient Encounter":
        patient_encounter_doc = frappe.get_cached_doc(doc.ref_doctype, doc.ref_docname)
        create_delivery_note_from_LRPT(doc, patient_encounter_doc)


def update_procedure_prescription(doc):
    if doc.ref_doctype == "Patient Encounter":
        hsrp = DocType("Healthcare Service Request Payment")
        (
            frappe.qb.update(hsrp)
            .set(hsrp.lrpmt_status, "Submitted")
            .where((hsrp.ref_docname == doc.hms_tz_ref_childname))
        ).run()


def validate_swab_count(doc):
    """Validate swab and instrument counts match before/after surgery.

    Called from on_submit of Clinical Procedure.
    """
    # Only validate if counts have been entered
    if not doc.get("swab_count_before") and not doc.get("instrument_count_before"):
        return

    errors = []

    swab_before = doc.get("swab_count_before") or 0
    swab_after = doc.get("swab_count_after") or 0
    instrument_before = doc.get("instrument_count_before") or 0
    instrument_after = doc.get("instrument_count_after") or 0

    if swab_before and swab_before != swab_after:
        errors.append(
            _("Swab count mismatch: Before ({0}) ≠ After ({1})").format(
                swab_before, swab_after
            )
        )

    if instrument_before and instrument_before != instrument_after:
        errors.append(
            _("Instrument count mismatch: Before ({0}) ≠ After ({1})").format(
                instrument_before, instrument_after
            )
        )

    if errors and not doc.get("count_verified"):
        frappe.throw(
            _("Count verification failed:<br>{0}<br><br>"
              "Please verify counts are correct and check 'Count Verified' to proceed.").format(
                "<br>".join(errors)
            )
        )

