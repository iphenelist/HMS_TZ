# Copyright (c) 2021, Aakvatech and contributors
# For license information, please see license.txt

import json
import frappe
import itertools
from frappe import bold, _
from frappe.model.document import Document
from frappe.model.workflow import apply_workflow
from frappe.utils import (
    nowdate,
    nowtime,
    flt,
    cint,
    unique,
    get_fullname,
    get_url_to_form,
)
from hms_tz.nhif.api.healthcare_utils import validate_nhif_patient_claim_status


class LRPMTReturns(Document):
    def validate(self):
        set_missing_values(self)
        combine_therapy_info(self.therapy_items)

    def before_insert(self):
        validate_nhif_patient_claim_status(
            "LRPMT Return", self.company, self.appointment
        )
        self.validate_duplicates()

    def before_submit(self):
        if not self.approved_by:
            self.approved_by = get_fullname()

        validate_nhif_patient_claim_status(
            "LRPMT Return", self.company, self.appointment
        )

        self.validate_reason()
        self.validate_drug_row()
        self.cancel_lrp_doc()
        self.cancel_therapy_doc()
        self.return_or_cancel_drugs()

    def on_submit(self):
        self.get_sales_return()

    def validate_reason(self):
        def check_reason(item_table):
            msg = ""
            for entry in item_table:
                if not entry.reason:
                    msg += f"Reason Field is Empty for Item name: {bold(entry.get('item_name') or entry.get('therapy_type'))},\
                             Row: #{bold(entry.idx)}, please fill it to proceed <br>"

            if msg:
                frappe.throw(
                    title="Notification",
                    msg=msg,
                    exc="Frappe.ValidationError",
                )

        if len(self.lrpt_items) > 0:
            check_reason(self.lrpt_items)

        if len(self.therapy_items) > 0:
            check_reason(self.therapy_items)

    def validate_drug_row(self):
        if len(self.drug_items) > 0:
            msg = ""
            for row in self.drug_items:
                msg_print = ""
                if row.quantity_to_return == 0:
                    msg_print += f"Quantity to return can not be Zero for drug name: {bold(row.drug_name)},\
                                Row: #{bold(row.idx)}:<br>"

                if not row.reason:
                    msg_print += "Reason for Return Field can not be Empty for drug name: {bold(row.drug_name)},\
                                Row: #{bold(row.idx)}:<br>"

                if not row.drug_condition:
                    msg_print += "Drug Condition Field can not Empty for drug name: {bold(row.drug_name)},\
                                Row: #{bold(row.idx)}:<br>"

                if not msg_print:
                    continue

                msg += msg_print + "<br>"

            if msg:
                frappe.throw(
                    title="Notification", msg=msg, exc="Frappe.ValidationError"
                )

    def validate_duplicates(self):
        dt = frappe.qb.DocType("LRPMT Returns")
        lrpmts = (
            frappe.qb.from_(dt)
            .select(dt.name.as_("lrpmt_docname"))
            .where(
                (dt.docstatus == 0)
                & (dt.name != self.name)
                & (dt.appointment == self.appointment)
            )
        ).run(as_dict=True)
        if len(lrpmts) > 0:
            frappe.throw(
                title="Duplicate Error",
                exc=frappe.ValidationError,
                msg="draft LRPMT Returns for this appointment: {bold(self.appointment)} already exists,\
                    Please visit <a href='{get_url_to_form('LRPMT Returns', lrpmts[0].lrpmt_docname)}'>{lrpmts[0].lrpmt_docname)}</a> to continue",
            )

    def cancel_lrp_doc(self):
        if len(self.lrpt_items) == 0:
            return

        prescription_lrp = {
            "Lab Test": "Lab Prescription",
            "Radiology Examination": "Radiology Procedure Prescription",
            "Clinical Procedure": "Procedure Prescription",
        }
        for item in self.lrpt_items:
            if not item.reference_docname:
                frappe.db.set_value(
                    prescription_lrp[item.reference_doctype],
                    item.child_name,
                    "is_cancelled",
                    1,
                )
                continue

            doc = frappe.get_doc(item.reference_doctype, item.reference_docname)

            if doc.docstatus < 2:
                try:
                    apply_workflow(doc, "Not Serviced")
                    if doc.meta.get_field("status"):
                        doc.status = "Not Serviced"
                    doc.save(ignore_permissions=True)
                    doc.reload()

                    if (
                        doc.workflow_state == "Not Serviced"
                        or doc.workflow_state == "Submitted but Not Serviced"
                    ):
                        frappe.db.set_value(
                            prescription_lrp[item.reference_doctype],
                            item.child_name,
                            "is_cancelled",
                            1,
                        )
                except Exception:
                    frappe.log_error(frappe.get_traceback(), str(self.doctype))
                    frappe.throw(
                        f"There was an error while cancelling the Item: {bold(item.item_name)} of ReferenceDoctype: {bold(item.reference_doctype)},\
                             ReferenceName: {bold(item.reference_docname)},<br> Check error log for review"
                    )

    def cancel_therapy_doc(self):
        if len(self.therapy_items) == 0:
            return

        therapy_details = combine_therapy_info(self.therapy_items)

        for item in therapy_details:
            total_sessions_prescribed = (
                frappe.get_cached_value(
                    "Therapy Plan Detail",
                    item.get("encounter_child_table_id"),
                    "no_of_sessions",
                )
                or 0
            )
            is_cancelled = 0
            total_sessions_cancelled = item.get("sessions_to_cancel") + item.get(
                "sessions_cancelled"
            )
            delivered_quantity = total_sessions_prescribed - total_sessions_cancelled
            if total_sessions_prescribed <= total_sessions_cancelled:
                is_cancelled = 1

            if not item.get("therapy_plan"):
                frappe.db.set_value(
                    "Therapy Plan Detail",
                    item.get("encounter_child_table_id"),
                    {
                        "is_cancelled": is_cancelled,
                        "delivered_quantity": delivered_quantity,
                        "sessions_cancelled": total_sessions_cancelled,
                    },
                )

            elif item.get("therapy_plan") and len(item.get("therapy_session_ids")) == 0:
                update_therapy_plan(
                    self,
                    item,
                    is_cancelled,
                    delivered_quantity,
                    total_sessions_cancelled,
                )

            elif item.get("therapy_plan") and len(item.get("therapy_session_ids")) > 0:
                update_therapy_session(
                    self,
                    item,
                    is_cancelled,
                    delivered_quantity,
                    total_sessions_cancelled,
                )

    def return_or_cancel_drugs(self):
        if len(self.drug_items) == 0:
            return

        update_drug_prescription_for_uncreated_delivery_note(self)

        unique_draft_delivery_notes = get_unique_delivery_notes(self, "Draft")
        if unique_draft_delivery_notes:
            for draft_delivery_note in unique_draft_delivery_notes:
                update_drug_description_for_draft_delivery_note(
                    self, draft_delivery_note
                )

        unique_submitted_delivery_notes = get_unique_delivery_notes(self, "Submitted")
        if unique_submitted_delivery_notes:
            for dn in unique_submitted_delivery_notes:
                try:
                    source_doc = frappe.get_doc("Delivery Note", dn)
                    target_doc = return_drug_quantity_to_stock(self, source_doc)

                    if target_doc.get("name"):
                        transition_workflow_states(source_doc, target_doc)

                except Exception:
                    frappe.log_error(
                        frappe.get_traceback(),
                        str(f"Error in creating return delivery note for {dn}"),
                    )
                    frappe.throw(
                        f"Error in creating return delivery note against delivery note: {bold(dn)}\
                            <br> Check error log for review"
                    )

        return self.name

    def get_sales_return(self):
        conditions = {
            "patient": self.patient,
            "company": self.company,
            "reference_name": self.name,
            "is_return": 1,
            "docstatus": 1,
        }

        returned_delivery_note_nos = frappe.get_all(
            "Delivery Note", filters=conditions, fields=["name"], pluck="name"
        )

        if returned_delivery_note_nos:
            for dn in returned_delivery_note_nos:
                sales_doc = frappe.get_doc("Delivery Note", dn)

                for item in sales_doc.items:
                    for dd_n in self.drug_items:
                        if item.item_code == dd_n.drug_name:
                            self.append(
                                "sales_items",
                                {
                                    "drug_name": item.item_code,
                                    "quantity_prescribed": dd_n.quantity_prescribed,
                                    "quantity_returned": item.qty - dd_n.qty_returned,
                                    "quantity_serviced": flt(
                                        dd_n.quantity_prescribed + item.qty - dd_n.qty_returned
                                    ),
                                    "delivery_note_no": dn,
                                    "dn_detail": item.name,
                                    "warehouse": item.warehouse,
                                    "reference_doctype": item.reference_doctype,
                                    "reference_name": item.reference_name,
                                },
                            )
            self.save(ignore_permissions=True)
            self.reload()

        return self.name

def combine_therapy_info(therapy_items):
    therapy_detail_map = []

    for key, group in itertools.groupby(
        therapy_items,
        lambda x: {
            "therapy_type": x.therapy_type,
            "encounter_no": x.encounter_no,
            "therapy_plan": x.therapy_plan,
            "plan_child_table_id": x.plan_child_table_id,
            "encounter_child_table_id": x.encounter_child_table_id,
        },
    ):
        sessions_prescribed = 0
        sessions_to_cancel = 0
        sessions_cancelled = 0
        therapy_session_ids = []
        for item in list(group):
            sessions_prescribed += cint(item.sessions_prescribed)
            sessions_to_cancel += cint(item.sessions_to_cancel)
            sessions_cancelled += cint(item.sessions_cancelled)
            if item.therapy_session:
                therapy_session_ids.append(item.therapy_session)

        key.update(
            {
                "sessions_prescribed": sessions_prescribed,
                "sessions_to_cancel": sessions_to_cancel,
                "sessions_cancelled": sessions_cancelled,
                "therapy_session_ids": therapy_session_ids,
            }
        )
        therapy_detail_map.append(key)

    return therapy_detail_map


def update_therapy_plan(
    self,
    row,
    is_cancelled,
    delivered_quantity,
    total_sessions_cancelled,
    session_docstatus=0,
):
    plan_doc = frappe.get_cached_doc("Therapy Plan", row.get("therapy_plan"))
    try:
        for d in plan_doc.therapy_plan_details:
            if d.name == row.get("plan_child_table_id") and d.therapy_type == row.get(
                "therapy_type"
            ):
                d.sessions_cancelled += row.get("sessions_to_cancel")
                d.no_of_sessions -= row.get("sessions_to_cancel")
                if session_docstatus == 1:
                    d.sessions_completed -= 1

        plan_doc.save(ignore_permissions=True)
        plan_doc.add_comment(
            text=f"LRPMT Returns: <a href='{self.get_url()}'>{bold(self.name)}</a> is submitted"
        )

        frappe.db.set_value(
            "Therapy Plan Detail",
            row.get("encounter_child_table_id"),
            {
                "is_cancelled": is_cancelled,
                "delivered_quantity": delivered_quantity,
                "sessions_cancelled": total_sessions_cancelled,
            },
        )
    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            str(f"{self.doctype}/{plan_doc.doctype}"),
        )
        frappe.throw(
            f"There was an error while cancelling the Therapy Plan: {bold(plan_doc.name)}\
                <br> Check error log for review"
        )


def update_therapy_session(
    self,
    item,
    is_cancelled,
    delivered_quantity,
    total_sessions_cancelled,
):
    for session_id in item.get("therapy_session_ids"):
        session_doc = frappe.get_doc("Therapy Session", session_id)
        if session_doc.docstatus < 2:
            try:
                apply_workflow(session_doc, "Not Serviced")
                session_doc.save(ignore_permissions=True)
                session_doc.add_comment(
                    text=f"LRPMT Return: <a href='{self.get_url()}'>{bold(self.name)}</a> is submitted"
                )
                session_doc.reload()

                if session_doc.workflow_state in [
                    "Not Serviced",
                    "Submitted but Not Serviced",
                ]:
                    update_therapy_plan(
                        self,
                        item,
                        is_cancelled,
                        delivered_quantity,
                        total_sessions_cancelled,
                        session_doc.docstatus,
                    )

            except Exception:
                frappe.log_error(
                    frappe.get_traceback(),
                    str(f"{self.doctype}/{session_doc.doctype}"),
                )
                frappe.throw(
                    f"There was an error while cancelling the Therapy Session: {bold(session_doc.name)}\
                        <br> Check error log for review"
                )


def update_drug_prescription_for_uncreated_delivery_note(self):
    for item in self.drug_items:
        if item.child_name and not (
            item.dn_detail and item.delivery_note_no and item.status
        ):
            frappe.db.set_value(
                "Drug Prescription",
                item.child_name,
                {
                    "is_cancelled": 1,
                    "quantity_returned": item.quantity_to_return + item.qty_returned,
                    "delivered_quantity": item.quantity_prescribed
                    - (item.quantity_to_return + item.qty_returned),
                },
            )


def update_drug_description_for_draft_delivery_note(self, delivey_note):
    try:
        dn_doc = frappe.get_doc("Delivery Note", delivey_note)

        if dn_doc.workflow_state != "Not Serviced":
            apply_workflow(dn_doc, "Not Serviced")

        if dn_doc.workflow_state == "Not Serviced":
            for item in self.drug_items:
                if item.delivery_note_no == delivey_note and item.status == "Draft":
                    frappe.db.set_value(
                        "Drug Prescription",
                        item.child_name,
                        {
                            "is_cancelled": 1,
                            "quantity_returned": item.quantity_to_return
                            + item.qty_returned,
                            "delivered_quantity": item.quantity_prescribed
                            - (item.quantity_to_return + item.qty_returned),
                        },
                    )

    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            str(f"Apply workflow error for Delivery Note {bold(delivey_note)}"),
        )
        frappe.throw(
            str(
                f"Apply workflow error, for delivery note: {bold(delivey_note)}, check error log for more details"
            )
        )

    frappe.db.commit()


def update_drug_prescription_for_submitted_delivery_note(item):
    item_cancelled = 0
    if item.quantity_prescribed <= (item.quantity_to_return + item.qty_returned):
        item_cancelled = 1

    frappe.db.set_value(
        "Drug Prescription",
        item.child_name,
        {
            "quantity_returned": item.quantity_to_return + item.qty_returned,
            "delivered_quantity": item.quantity_prescribed
            - (item.quantity_to_return + item.qty_returned),
            "is_cancelled": item_cancelled,
        },
    )


def return_drug_quantity_to_stock(self, source_doc):
    target_doc = frappe.new_doc("Delivery Note")
    target_doc.customer = source_doc.customer
    if source_doc.medical_department:
        target_doc.medical_department = source_doc.medical_department
    target_doc.healthcare_service_unit = source_doc.healthcare_service_unit
    target_doc.patient = source_doc.patient
    target_doc.patient_name = source_doc.patient_name
    target_doc.hms_tz_phone_no = source_doc.hms_tz_phone_no
    if source_doc.coverage_plan_name:
        target_doc.coverage_plan_name = source_doc.coverage_plan_name
    target_doc.hms_tz_appointment_no = source_doc.hms_tz_appointment_no
    target_doc.company = source_doc.company
    target_doc.posting_date = nowdate()
    target_doc.posting_time = nowtime()
    if source_doc.form_sales_invoice:
        target_doc.form_sales_invoice = source_doc.form_sales_invoice
    target_doc.is_return = 1
    target_doc.return_against = source_doc.name
    target_doc.reference_doctype = "LRPMT Returns"
    target_doc.reference_name = self.name
    target_doc.currency = source_doc.currency
    target_doc.conversion_rate = source_doc.conversion_rate
    target_doc.selling_price_list = source_doc.selling_price_list
    target_doc.price_list_currency = source_doc.price_list_currency
    target_doc.plc_conversion_rate = source_doc.plc_conversion_rate
    target_doc.ignore_pricing_rule = 1
    if source_doc.healthcare_practitioner:
        target_doc.healthcare_practitioner = source_doc.healthcare_practitioner

    for item in self.drug_items:
        if source_doc.name == item.delivery_note_no and item.status == "Submitted":
            update_drug_prescription_for_submitted_delivery_note(item)
            for dni in source_doc.items:
                if (item.dn_detail == dni.name) and (item.drug_name == dni.item_code):
                    target_doc.append(
                        "items",
                        {
                            "item_code": item.drug_name,
                            "item_name": item.drug_name,
                            "description": dni.description,
                            "qty": -1 * flt(item.quantity_to_return or 0),
                            "stock_uom": dni.stock_uom,
                            "uom": dni.uom,
                            "rate": dni.rate,
                            "conversion_factor": dni.conversion_factor,
                            "warehouse": dni.warehouse,
                            "target_warehouse": dni.target_warehouse or "",
                            "dn_detail": dni.name,
                            "healthcare_service_unit": dni.healthcare_service_unit
                            or "",
                            "healthcare_practitioner": dni.healthcare_practitioner
                            or "",
                            "department": dni.department,
                            "cost_center": dni.cost_center,
                            "reference_doctype": dni.reference_doctype,
                            "reference_name": dni.reference_name,
                        },
                    )
    target_doc.save(ignore_permissions=True)
    target_doc.reload()

    return target_doc


def transition_workflow_states(source_doc, target_doc):
    try:
        if target_doc.workflow_state != "Is Return":
            apply_workflow(target_doc, "Return")
        if (
            target_doc.workflow_state == "Is Return"
            and source_doc.workflow_state != "Return Issued"
        ):
            try:
                apply_workflow(source_doc, "Issue Returns")
            except Exception:
                frappe.log_error(
                    frappe.get_traceback(),
                    str(
                        f"Apply workflow error for Delivery Note {bold(source_doc.name)}"
                    ),
                )
    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            str(f"Apply workflow error for Delivery Note {bold(target_doc.name)}"),
        )
        frappe.throw(
            str(
                f"Apply workflow error, for delivery note: {bold(target_doc.name)}, check error log for more details"
            )
        )


def get_unique_delivery_notes(self, status):
    return unique([d.delivery_note_no for d in self.drug_items if d.status == status])


@frappe.whitelist()
def get_lrp_item_list(patient, appointment, company):
    item_list = []
    child_list = get_lrp_map()

    encounter_list = get_patient_encounters(patient, appointment, company)

    for child in child_list:
        items = frappe.get_all(
            child["doctype"],
            filters={
                "parent": ["in", encounter_list],
                "is_not_available_inhouse": 0,
                "is_cancelled": 0,
            },
            fields=child["fields"],
        )

        for item in items:
            if item.lab_test_code:
                lab_status = "Submitted"
                if not item.lab_test:
                    name = get_refdoc(
                        "Lab Prescription", item.name, item.lab_test_code, item.parent
                    )
                    if name:
                        lab_status = "Draft"
                    else:
                        lab_status = ""

                item_list.append(
                    {
                        "child_name": item.name,
                        "item_name": item.lab_test_code,
                        "quantity": 1,
                        "encounter_no": item.parent,
                        "reference_doctype": "Lab Test",
                        "reference_docname": item.lab_test or name,
                        "status": lab_status,
                    }
                )

            if item.radiology_examination_template:
                radiology_status = "Submitted"
                if not item.radiology_examination:
                    name = get_refdoc(
                        "Radiology Procedure Prescription",
                        item.name,
                        item.radiology_examination_template,
                        item.parent,
                    )
                    if name:
                        radiology_status = "Draft"
                    else:
                        radiology_status = ""

                item_list.append(
                    {
                        "child_name": item.name,
                        "item_name": item.radiology_examination_template,
                        "quantity": 1,
                        "encounter_no": item.parent,
                        "reference_doctype": "Radiology Examination",
                        "reference_docname": item.radiology_examination or name,
                        "status": radiology_status,
                    }
                )

            if item.procedure:
                procedure_status = "Submitted"
                if not item.clinical_procedure:
                    name = get_refdoc(
                        "Procedure Prescription", item.name, item.procedure, item.parent
                    )
                    if name:
                        procedure_status = "Draft"
                    else:
                        procedure_status = ""

                item_list.append(
                    {
                        "child_name": item.name,
                        "item_name": item.procedure,
                        "quantity": 1,
                        "encounter_no": item.parent,
                        "reference_doctype": "Clinical Procedure",
                        "reference_docname": item.clinical_procedure or name,
                        "status": procedure_status,
                    }
                )

    return item_list


def get_lrp_map():
    child_map = [
        {
            "doctype": "Lab Prescription",
            "fields": ["name", "lab_test_code", "lab_test_name", "lab_test", "parent"],
        },
        {
            "doctype": "Radiology Procedure Prescription",
            "fields": [
                "name",
                "radiology_examination_template",
                "radiology_procedure_name",
                "radiology_examination",
                "parent",
            ],
        },
        {
            "doctype": "Procedure Prescription",
            "fields": [
                "name",
                "procedure",
                "procedure_name",
                "clinical_procedure",
                "parent",
            ],
        },
    ]
    return child_map


def get_refdoc(doctype, childname, template, encounter):
    ref_docs = [
        {"ref_d": "Lab Test", "table": "Lab Prescription", "field": "template"},
        {
            "ref_d": "Radiology Examination",
            "table": "Radiology Procedure Prescription",
            "field": "radiology_examination_template",
        },
        {
            "ref_d": "Clinical Procedure",
            "table": "Procedure Prescription",
            "field": "procedure_template",
        },
    ]

    for refd in ref_docs:
        if refd.get("table") == doctype:
            docname = frappe.get_value(
                refd.get("ref_d"),
                {
                    "ref_doctype": "Patient Encounter",
                    "ref_docname": encounter,
                    "hms_tz_ref_childname": childname,
                    refd.get("field"): template,
                },
                ["name"],
            )
            return docname or ""


def set_missing_values(doc):
    if not doc.requested_by:
        doc.requested_by = get_fullname()

    appointment_list = frappe.get_all(
        "Patient Appointment",
        filters={"patient": doc.patient, "status": "Closed"},
        fields=["name", "company"],
        order_by="appointment_date desc",
        page_length=1,
    )

    if appointment_list:
        if not doc.appointment:
            doc.appointment = appointment_list[0]["name"]
        doc.company = appointment_list[0]["company"]

        record = frappe.get_all(
            "Inpatient Record",
            filters={
                "patient": doc.patient,
                "patient_appointment": appointment_list[0]["name"],
                "status": "Admitted",
            },
            fields=["name", "status", "admitted_datetime"],
            page_length=1,
        )
        if record:
            if (
                record[0]["name"]
                and record[0]["status"]
                and record[0]["admitted_datetime"]
            ):
                doc.inpatient_record = record[0]["name"]
                doc.status = record[0]["status"]
                doc.admitted_datetime = record[0]["admitted_datetime"]
            else:
                pass
    else:
        frappe.throw(
            title="Notification",
            msg="No any Appointment found for this Patient: {0}-{1}".format(
                frappe.bold(doc.patient), frappe.bold(doc.patient_name)
            ),
        )


def get_patient_encounters(patient, appointment, company):
    if patient and appointment and company:
        conditions = {
            "patient": patient,
            "appointment": appointment,
            "company": company,
            "docstatus": 1,
        }

        patient_encounter_List = frappe.get_all(
            "Patient Encounter",
            filters=conditions,
            fields=["name"],
            pluck="name",
            order_by="encounter_date desc",
        )
        return patient_encounter_List


@frappe.whitelist()
def set_checked_lrp_items(doc, checked_items):
    doc = frappe.get_doc(json.loads(doc))
    checked_items = json.loads(checked_items)

    doc.lrpt_items = []

    for checked_item in checked_items:
        item_row = doc.append("lrpt_items", {})
        item_row.item_name = checked_item["item"]
        item_row.quantity = checked_item["quantity"]
        item_row.encounter_no = checked_item["encounter"]
        item_row.reference_doctype = checked_item["reference_doctype"] or ""
        item_row.reference_docname = checked_item["reference_docname"] or ""
        item_row.child_name = checked_item["child_name"]
    doc.save()
    return doc.name


@frappe.whitelist()
def get_drug_item_list(patient, appointment, company):
    drug_list = []
    delivery_note_items = []

    item_list, name_list = get_drugs(patient, appointment, company)
    if len(item_list) == 0:
        return []

    if name_list:
        delivery_note_items += frappe.get_all(
            "Delivery Note Item",
            filters={
                "reference_name": ["in", name_list],
                "reference_doctype": "Drug Prescription",
                "docstatus": ["!=", 2],
            },
            fields=[
                "name",
                "parent",
                "item_code",
                "docstatus",
                "reference_name",
                "si_detail",
            ],
        )

        si_parent = frappe.get_all(
            "Sales Invoice Item",
            filters={
                "reference_dn": ["in", name_list],
                "reference_dt": "Drug Prescription",
            },
            fields=["parent"],
            pluck="parent",
        )
        if si_parent:
            delivery_note_items += frappe.get_all(
                "Delivery Note Item",
                filters={
                    "against_sales_invoice": ["in", si_parent],
                    "docstatus": ["!=", 2],
                },
                fields=[
                    "name",
                    "parent",
                    "item_code",
                    "docstatus",
                    "reference_name",
                    "si_detail",
                ],
            )

    avoid_duplicate_list = []
    for item in item_list:
        for delivery_note in delivery_note_items:
            if delivery_note.docstatus == 0:
                status = "Draft"
            else:
                status = "Submitted"

            if (
                item.dn_detail
                and item.drug_prescription_created == 1
                and item.dn_detail == delivery_note.name
                and delivery_note.docstatus == 1
            ):
                if item.name not in avoid_duplicate_list:
                    drug_list.append(
                        {
                            "child_name": item.name,
                            "item_name": item.drug_code,
                            "qty_prescribed": item.quantity,  # - item.quantity_returned,
                            "qty_returned": item.quantity_returned or "",
                            "encounter_no": item.parent,
                            "delivery_note": delivery_note.parent,
                            "dn_detail": item.dn_detail,
                            "status": status,
                        }
                    )
                    avoid_duplicate_list.append(item.name)

            if (
                delivery_note.reference_name
                and item.name == delivery_note.reference_name
                and item.drug_prescription_created == 1
                and delivery_note.docstatus == 0
                and not item.dn_detail
                and not delivery_note.si_detail
            ):
                if item.name not in avoid_duplicate_list:
                    drug_list.append(
                        {
                            "child_name": item.name,
                            "item_name": item.drug_code,
                            "qty_prescribed": item.quantity,  # - item.quantity_returned,
                            "qty_returned": item.quantity_returned or "",
                            "encounter_no": item.parent,
                            "delivery_note": delivery_note.parent,
                            "dn_detail": item.dn_detail or "",
                            "status": status,
                        }
                    )
                    avoid_duplicate_list.append(item.name)

            if (
                not item.dn_detail
                and not delivery_note.reference_name
                and item.drug_prescription_created == 1
                and delivery_note.si_detail
                and delivery_note.docstatus == 0
            ):
                if item.name not in avoid_duplicate_list:
                    drug_list.append(
                        {
                            "child_name": item.name,
                            "item_name": item.drug_code,
                            "qty_prescribed": item.quantity,  # - item.quantity_returned,
                            "qty_returned": item.quantity_returned or "",
                            "encounter_no": item.parent,
                            "delivery_note": delivery_note.parent,
                            "dn_detail": item.dn_detail or "",
                            "status": status,
                        }
                    )
                    avoid_duplicate_list.append(item.name)

        if item.name not in avoid_duplicate_list:
            drug_list.append(
                {
                    "child_name": item.name,
                    "item_name": item.drug_code,
                    "qty_prescribed": item.quantity,  # - item.quantity_returned,
                    "qty_returned": item.quantity_returned or "",
                    "encounter_no": item.parent,
                    "delivery_note": "",
                    "dn_detail": "",
                    "status": "",
                }
            )

    return drug_list


def get_drugs(patient, appointment, company):
    item_list = []
    name_list = []

    encounter_list = get_patient_encounters(patient, appointment, company)
    drugs = frappe.get_all(
        "Drug Prescription",
        filters={
            "parent": ["in", encounter_list],
            "is_not_available_inhouse": 0,
            "is_cancelled": 0,
        },
        fields=[
            "name",
            "drug_code",
            "quantity",
            "quantity_returned",
            "drug_prescription_created",
            "parent",
            "dn_detail",
        ],
    )

    for drug in drugs:
        drug.update(
            {
                "drug_code": frappe.get_cached_value(
                    "Medication", drug.drug_code, "item"
                ),
            }
        )

        item_list.append(drug)
        name_list.append(drug.name)
    return item_list, name_list


@frappe.whitelist()
def set_checked_drug_items(doc, checked_items):
    doc = frappe.get_doc(json.loads(doc))
    checked_items = json.loads(checked_items)

    doc.drug_items = []

    for checked_item in checked_items:
        item_row = doc.append("drug_items", {})
        item_row.drug_name = checked_item["item_name"]
        item_row.quantity_prescribed = cint(checked_item["qty_prescribed"])
        item_row.qty_returned = cint(checked_item["qty_returned"])
        item_row.encounter_no = checked_item["encounter_no"]
        item_row.delivery_note_no = checked_item["delivery_note"] or ""
        item_row.status = checked_item["status"] or ""
        item_row.dn_detail = checked_item["dn_detail"] or ""
        item_row.child_name = checked_item["child_name"]

    doc.save()
    return doc.name


@frappe.whitelist()
def get_therapies(patient, appointment, company):
    therapies = []
    plan_child_table_ids = []

    encounter_list = get_patient_encounters(patient, appointment, company)
    if len(encounter_list) == 0:
        return []

    therapy_items = frappe.get_all(
        "Therapy Plan Detail",
        filters={
            "parent": ["in", encounter_list],
            "is_not_available_inhouse": 0,
            "is_cancelled": 0,
        },
        fields=[
            "name",
            "therapy_type",
            "parent",
            "no_of_sessions",
            "sessions_cancelled",
        ],
    )

    for item in therapy_items:
        if item.therapy_type:
            therapy_plan = frappe.get_value(
                "Therapy Plan",
                {"ref_doctype": "Patient Encounter", "ref_docname": item.parent},
                "name",
            )

            plan_child_table_id = frappe.db.get_value(
                "Therapy Plan Detail",
                {
                    "parent": therapy_plan,
                    "parenttype": "Therapy Plan",
                    "hms_tz_ref_childname": item.name,
                    "therapy_type": item.therapy_type,
                    "parentfield": "therapy_plan_details",
                },
                "name",
            )

            if not plan_child_table_id:
                # find plan_child_table_id when hms_tz_ref_childname does not have value, (for old therapies)
                child_table_ids = frappe.db.get_all(
                    "Therapy Plan Detail",
                    {
                        "parent": therapy_plan,
                        "parenttype": "Therapy Plan",
                        "therapy_type": item.therapy_type,
                        "parentfield": "therapy_plan_details",
                    },
                    "name",
                )
                if len(child_table_ids) > 0:
                    for row in child_table_ids:
                        if row.name not in child_table_ids:
                            plan_child_table_id = row.name
                            break

            if plan_child_table_id:
                plan_child_table_ids.append(plan_child_table_id)

            record = {
                "status": "",
                "therapy_session": "",
                "encounter_no": item.parent,
                "sessions": item.no_of_sessions,
                "therapy_type": item.therapy_type,
                "therapy_plan": therapy_plan or "",
                "encounter_child_table_id": item.name,
                "plan_child_table_id": plan_child_table_id,
                "sessions_cancelled": item.sessions_cancelled,
            }

            sessions_info = frappe.get_all(
                "Therapy Session",
                {
                    "patient": patient,
                    "docstatus": ["!=", 2],
                    "appointment": appointment,
                    "therapy_plan": therapy_plan,
                    "therapy_type": item.therapy_type,
                    "workflow_state": [
                        "not in",
                        ["Not Serviced", "Submitted but Not Serviced"],
                    ],
                },
                ["name", "docstatus"],
            )

            if len(sessions_info) == 0:
                therapies.append(record)

            elif item.no_of_sessions > len(sessions_info):
                record.update(
                    {
                        "sessions": item.no_of_sessions - len(sessions_info),
                    }
                )
                therapies.append(record)

                for session in sessions_info:
                    session_dict = record.copy()
                    session_dict.update(
                        {
                            "sessions": 1,
                            "sessions_cancelled": 0,
                            "therapy_session": session.name,
                            "status": (
                                "Draft" if session.docstatus == 0 else "Submitted"
                            ),
                        }
                    )

                    therapies.append(session_dict)

    return therapies


@frappe.whitelist()
def set_checked_therapy_items(doc, checked_items):
    doc = frappe.get_doc(json.loads(doc))
    checked_items = json.loads(checked_items)

    doc.therapy_items = []

    for checked_item in checked_items:
        item_row = doc.append("therapy_items", {})
        item_row.status = checked_item["status"] or ""
        item_row.therapy_type = checked_item["therapy_type"]
        item_row.encounter_no = checked_item["encounter_no"]
        item_row.therapy_plan = checked_item["therapy_plan"] or ""
        item_row.sessions_cancelled = cint(checked_item["sessions_cancelled"])
        item_row.therapy_session = checked_item["therapy_session"] or ""
        item_row.sessions_prescribed = cint(checked_item["sessions_prescribed"])
        item_row.plan_child_table_id = checked_item["plan_child_table_id"]
        item_row.encounter_child_table_id = checked_item["encounter_child_table_id"]

    doc.save()
    return doc.name
