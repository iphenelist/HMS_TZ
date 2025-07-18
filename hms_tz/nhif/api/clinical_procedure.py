# -*- coding: utf-8 -*-
# Copyright (c) 2020, Aakvatech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import frappe
from frappe import _
from frappe.query_builder import DocType
from frappe.utils import get_fullname, nowdate
from hms_tz.nhif.utils import validate_point_of_care

from hms_tz.nhif.api.lab_test import check_cash_payments_from_encounter
from hms_tz.nhif.api.healthcare_utils import create_delivery_note_from_LRPT
from hms_tz.hms_tz.doctype.hospital_revenue_entry.hospital_revenue_entry import (
    create_revenue_entry,
    update_revenue_entry,
)


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
    update_procedure_prescription(doc)
    update_revenue_entry(
        "Clinical Procedure",
        doc.name,
        "Procedure Prescription",
        doc.hms_tz_ref_childname,
        lrpmt_status="Submitted",
    )


def before_submit(doc, method):
    if doc.is_restricted and not doc.approval_number:
        frappe.throw(
            _(f"Approval number is required for <b>{doc.procedure_template}</b>. Please set the Approval Number.")
        )

    validate_point_of_care(doc)

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
