# -*- coding: utf-8 -*-
# Copyright (c) 2020, Aakvatech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.query_builder import DocType
from hms_tz.nhif.api.healthcare_utils import (
    create_delivery_note_from_LRPT,
    get_restricted_LRPT,
)
from frappe.utils import getdate, get_fullname, nowdate
from hms_tz.nhif.api.lab_test import check_cash_payments_from_encounter

def onload(doc, method):
    check_cash_payments_from_encounter(
    doc=doc,
    ref_doctype="ref_doctype",
    ref_docname_field="ref_docname",
    prescription_field="procedure_prescription",
    item_name_field="procedure_name",
    item_descriptor="Clinical Procedures"
)

def on_submit(doc, methd):
    update_procedure_prescription(doc)
    # create_delivery_note(doc)


def before_submit(doc, method):
    if doc.is_restricted and not doc.approval_number:
        frappe.throw(
            _(
                f"Approval number is required for <b>{doc.procedure_template}</b>. Please set the Approval Number."
            )
        )

    doc.hms_tz_submitted_by = get_fullname(frappe.session.user)
    doc.hms_tz_user_id = frappe.session.user
    doc.hms_tz_submitted_date = nowdate()

    # 2023-07-13
    # stop this validation for now
    return
    if doc.approval_number and doc.approval_status != "Verified":
        frappe.throw(
            _(
                f"Approval number: <b>{doc.approval_number}</b> for item: <b>{doc.procedure_template}</b> is not verified.>br>\
                    Please verify the Approval Number."
            )
        )


def create_delivery_note(doc):
    if doc.ref_doctype and doc.ref_docname and doc.ref_doctype == "Patient Encounter":
        patient_encounter_doc = frappe.get_doc(doc.ref_doctype, doc.ref_docname)
        create_delivery_note_from_LRPT(doc, patient_encounter_doc)


def update_procedure_prescription(doc):
    if doc.ref_doctype == "Patient Encounter":
        frappe.db.set_value(
            "Procedure Prescription",
            doc.hms_tz_ref_childname,
            {"clinical_procedure": doc.name, "delivered_quantity": 1},
        )

        hsrp = DocType("Healthcare Service Request Payment")
        (
            frappe.qb.update(hsrp)
            .set(hsrp.lrpmt_doctype, doc.doctype)
            .set(hsrp.lrpmt_docname, doc.name)
            .where((hsrp.ref_docname == doc.hms_tz_ref_childname))
        ).run()
