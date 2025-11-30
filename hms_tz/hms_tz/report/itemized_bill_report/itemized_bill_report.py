# Copyright (c) 2022, Aakvatech and contributors
# For license information, please see license.txt


import frappe
from erpnext.accounts.utils import get_balance_on
from frappe import _
from frappe.query_builder import DocType
from frappe.query_builder.functions import Coalesce
from frappe.query_builder import functions as fn
from frappe.utils import flt
from pypika.terms import ValueWrapper  # Case, Criterion, , Not


def execute(filters=None):
    if not filters:
        return

    columns = get_columns(filters)

    data = []
    details = frappe.get_all(
        "Patient Appointment",
        filters=[
            ["patient", "=", filters.patient],
            ["name", "=", filters.patient_appointment],
        ],
        fields=[
            "docstatus",
            "status",
        ],
    )
    appointment_date = frappe.get_cached_value("Patient Appointment", filters.patient_appointment, "appointment_date")

    if details[0]["docstatus"] == 0 and details[0]["status"] != "Closed":
        frappe.throw(frappe.bold("This Appointment is not Closed..!!"))

    else:
        admitted_discharge_date = frappe.get_cached_value(
            "Inpatient Record",
            {"patient_appointment": filters.patient_appointment},
            [
                "admitted_datetime as admitted_date",
                "discharge_date",
                "scheduled_date",
            ],
            as_dict=True,
        )

        _date = ""  # Initialize _date with an empty string
        if admitted_discharge_date:
            if admitted_discharge_date.admitted_date:
                _date = admitted_discharge_date.admitted_date.strftime("%Y-%m-%d")
            else:
                _date = admitted_discharge_date.scheduled_date

        if not filters.get("patient_type"):
            appointments_data = get_appointment_consultancy(filters)
            if appointments_data:
                data += appointments_data

            cash_lrpmt_data = get_cash_lrpmt_transaction(filters)
            if cash_lrpmt_data:
                data += cash_lrpmt_data

            insurance_lrpmt_data = get_insurance_lrpmt_transaction(filters)
            if insurance_lrpmt_data:
                data += insurance_lrpmt_data

            ipd_beds = get_ipd_occupancy_transactions(filters)
            if ipd_beds:
                data += ipd_beds

            ipd_cons = get_ipd_consultancy_transactions(filters)
            if ipd_cons:
                data += ipd_cons

            data = sorted(data, key=lambda d: (d["category"], d["date"]))

            if not data:
                frappe.throw(
                    f"No Record found for the filters Patient: {frappe.bold(filters.patient)}, Appointment: {frappe.bold(filters.patient_appointment)},\
                    Patient Type: {frappe.bold(filters.patient_type)} From Date: {frappe.bold(filters.from_date)} and To Date: {frappe.bold(filters.to_date)} you specified..., \
                    Please change your filters and try again..!!")

            total_amount = 0
            for n in range(0, len(data)):
                total_amount += data[n]["amount"]

            last_row = {
                "date": "Total",
                "category": "",
                "description": "",
                "quantity": "",
                "rate": "",
                "amount": total_amount,
                "patient": "",
                "patient_name": "",
                "appointment_type": "",
                "insurance_company": "",
                "coverage_plan_name": "",
                "authorization_number": "",
                "coverage_plan_card_number": "",
                "date_admitted": _date,
                "date_discharge": (admitted_discharge_date.discharge_date if admitted_discharge_date else ""),
                "appointment_date": appointment_date,
            }

            print_person = frappe.get_cached_value("User", frappe.session.user, "full_name")

            last_row["printed_by"] = print_person

            exceeded_items = get_daily_limit_exceeded_items(filters)
            if len(exceeded_items) > 0:
                last_row["limit_exceeded_items"] = exceeded_items
                last_row["total_limit_exceeded_amount"] = sum([d.amount for d in exceeded_items])
            
            data.append(last_row)

            return columns, data

        if filters.get("patient_type") == "Out-Patient":
            appointments_data = get_appointment_consultancy(filters)
            if appointments_data:
                data += appointments_data

            cash_lrpmt_data = get_cash_lrpmt_transaction(filters)
            if cash_lrpmt_data:
                data += cash_lrpmt_data

            insurance_lrpmt_data = get_insurance_lrpmt_transaction(filters)
            if insurance_lrpmt_data:
                data += insurance_lrpmt_data

            data = sorted(data, key=lambda d: (d["category"], d["date"]))

            if not data:
                frappe.throw(
                    f"No Record found for the filters Patient: {frappe.bold(filters.patient)}, Appointment: {frappe.bold(filters.patient_appointment)},\
                    Patient Type: {frappe.bold(filters.patient_type)} From Date: {frappe.bold(filters.from_date)} and To Date: {frappe.bold(filters.to_date)} you specified..., \
                    Please change your filters and try again..!!")

            total_amount = 0
            for n in range(0, len(data)):
                total_amount += data[n]["amount"]

            last_row = {
                "date": "Total",
                "category": "",
                "description": "",
                "quantity": "",
                "rate": "",
                "amount": total_amount,
                "patient": "",
                "patient_name": "",
                "appointment_type": "",
                "insurance_company": "",
                "coverage_plan_name": "",
                "authorization_number": "",
                "coverage_plan_card_number": "",
                "date_admitted": _date,
                "date_discharge": (admitted_discharge_date.discharge_date if admitted_discharge_date else ""),
                "appointment_date": appointment_date,
            }

            print_person = frappe.get_cached_value("User", frappe.session.user, "full_name")

            last_row["printed_by"] = print_person

            exceeded_items = get_daily_limit_exceeded_items(filters)
            if len(exceeded_items) > 0:
                last_row["limit_exceeded_items"] = exceeded_items
                last_row["total_limit_exceeded_amount"] = sum([d.amount for d in exceeded_items])

            data.append(last_row)

            return columns, data

        if filters.get("patient_type") == "In-Patient":
            cash_lrpmt_data = get_cash_lrpmt_transaction(filters)
            if cash_lrpmt_data:
                data += cash_lrpmt_data

            insurance_lrpmt_data = get_insurance_lrpmt_transaction(filters)
            if insurance_lrpmt_data:
                data += insurance_lrpmt_data

            ipd_beds = get_ipd_occupancy_transactions(filters)
            if ipd_beds:
                data += ipd_beds

            ipd_cons = get_ipd_consultancy_transactions(filters)
            if ipd_cons:
                data += ipd_cons

            data = sorted(data, key=lambda d: (d["category"], d["date"]))
            if not data:
                frappe.throw(
                    f"No Record found for the filters Patient: {frappe.bold(filters.patient)}, Appointment: {frappe.bold(filters.patient_appointment)},\
                    Patient Type: {frappe.bold(filters.patient_type)} From Date: {frappe.bold(filters.from_date)} and To Date: {frappe.bold(filters.to_date)} you specified..., \
                    Please change your filters and try again..!!")

            total_amount = 0
            for n in range(0, len(data)):
                total_amount += data[n]["amount"]

            last_row = {
                "date": "Total",
                "category": "",
                "description": "",
                "quantity": "",
                "rate": "",
                "amount": total_amount,
                "patient": "",
                "patient_name": "",
                "appointment_type": "",
                "insurance_company": "",
                "coverage_plan_name": "",
                "authorization_number": "",
                "coverage_plan_card_number": "",
                "date_admitted": _date,
                "date_discharge": (admitted_discharge_date.discharge_date if admitted_discharge_date else ""),
                "appointment_date": appointment_date,
            }

            print_person = frappe.get_cached_value("User", frappe.session.user, "full_name")

            last_row["printed_by"] = print_person

            data.append(last_row)
            # summary_view = get_report_summary(filters, total_amount)

            return columns, data  # , None, None, summary_view


def get_daily_limit_exceeded_items(filters):
    if filters.get("patient_type") == "In-Patient":
        return []

    pe = DocType("Patient Encounter")

    encounters_query = (
        frappe.qb.from_(pe)
        .select("name")
        .where(
            (pe.patient == filters.patient)
            & (pe.appointment == filters.patient_appointment)
            & (pe.inpatient_record.isnull() | pe.inpatient_record == "")
        )
    )

    if filters.get("from_date"):
        encounters_query.where((pe.encounter_date >= filters.from_date))

    if filters.get("to_date"):
        encounters_query.where((pe.encounter_date <= filters.to_date))
    encounters = [d.name for d in encounters_query.run(as_dict=True)]

    if not encounters or len(encounters) == 0:
        return []

    data = get_exceeded_lab_items(encounters)
    data += get_exceeded_radiology_items(encounters)
    data += get_exceeded_procedure_items(encounters)
    data += get_exceeded_drug_items(encounters)
    data += get_exceeded_therapy_items(encounters)
    return data


def get_exceeded_lab_items(encounters):
    lab = DocType("Lab Prescription")
    temp = DocType("Lab Test Template")
    lab_items = (
        frappe.qb.from_(lab)
        .inner_join(temp)
        .on(lab.lab_test_code == temp.name)
        .select(
            fn.Date(lab.creation).as_("date"),
            temp.lab_test_group.as_("category"),
            lab.lab_test_name.as_("description"),
            ValueWrapper(1).as_("quantity"),
            lab.amount.as_("rate"),
            lab.amount.as_("amount"),
        )
        .where((lab.prescribe == 0) & (lab.hms_tz_is_limit_exceeded == 1) & (lab.parent.isin(encounters)))
    ).run(as_dict=True)
    return lab_items


def get_exceeded_radiology_items(encounters):
    rad = DocType("Radiology Procedure Prescription")
    temp = DocType("Radiology Examination Template")
    rad_items = (
        frappe.qb.from_(rad)
        .inner_join(temp)
        .on(rad.radiology_examination_template == temp.name)
        .select(
            fn.Date(rad.creation).as_("date"),
            temp.item_group.as_("category"),
            rad.radiology_procedure_name.as_("description"),
            ValueWrapper(1).as_("quantity"),
            rad.amount.as_("rate"),
            rad.amount.as_("amount"),
        )
        .where((rad.prescribe == 0) & (rad.hms_tz_is_limit_exceeded == 1) & (rad.parent.isin(encounters)))
    ).run(as_dict=True)
    return rad_items


def get_exceeded_procedure_items(encounters):
    proc = DocType("Procedure Prescription")
    temp = DocType("Clinical Procedure Template")
    proc_items = (
        frappe.qb.from_(proc)
        .inner_join(temp)
        .on(proc.procedure == temp.name)
        .select(
            fn.Date(proc.creation).as_("date"),
            temp.item_group.as_("category"),
            proc.procedure_name.as_("description"),
            ValueWrapper(1).as_("quantity"),
            proc.amount.as_("rate"),
            proc.amount.as_("amount"),
        )
        .where((proc.prescribe == 0) & (proc.hms_tz_is_limit_exceeded == 1) & (proc.parent.isin(encounters)))
    ).run(as_dict=True)
    return proc_items


def get_exceeded_drug_items(encounters):
    drug = DocType("Drug Prescription")
    temp = DocType("Medication")
    drug_items = (
        frappe.qb.from_(drug)
        .inner_join(temp)
        .on(drug.drug_code == temp.name)
        .select(
            fn.Date(drug.creation).as_("date"),
            temp.item_group.as_("category"),
            drug.drug_name.as_("description"),
            (drug.quantity - drug.quantity_returned).as_("quantity"),
            drug.amount.as_("rate"),
            ((drug.quantity - drug.quantity_returned) * drug.amount).as_("amount"),
        )
        .where((drug.prescribe == 0) & (drug.hms_tz_is_limit_exceeded == 1) & (drug.parent.isin(encounters)))
    ).run(as_dict=True)
    return drug_items


def get_exceeded_therapy_items(encounters):
    therapy = DocType("Therapy Plan Detail")
    temp = DocType("Therapy Type")
    therapy_items = (
        frappe.qb.from_(therapy)
        .inner_join(temp)
        .on(therapy.therapy_type == temp.name)
        .select(
            fn.Date(therapy.creation).as_("date"),
            temp.item_group.as_("category"),
            therapy.therapy_type.as_("description"),
            (therapy.no_of_sessions - therapy.sessions_cancelled).as_("quantity"),
            therapy.amount.as_("rate"),
            ((therapy.no_of_sessions - therapy.sessions_cancelled) * therapy.amount).as_("amount"),
        )
        .where((therapy.prescribe == 0) & (therapy.hms_tz_is_limit_exceeded == 1) & (therapy.parent.isin(encounters)))
    ).run(as_dict=True)
    return therapy_items


def get_columns(filters):
    columns = [
        {"fieldname": "date", "fieldtype": "date", "label": _("Date")},
        {"fieldname": "category", "fieldtype": "Data", "label": _("Category")},
        {
            "fieldname": "description",
            "fieldtype": "Data",
            "label": _("Description"),
        },
        {"fieldname": "quantity", "fieldtype": "Data", "label": _("Quantity")},
        {"fieldname": "rate", "fieldtype": "Currency", "label": _("Rate")},
        {"fieldname": "amount", "fieldtype": "Currency", "label": _("Amount")},
    ]
    return columns


def get_appointment_consultancy(filters):
    """
    Fetch appointment consultancy data for cash patients.
    Uses frappe.query_builder and pypika methods.
    """
    pa = DocType("Patient Appointment")
    item = DocType("Item")
    ipd_rec = DocType("Inpatient Record")

    # Build the query
    query = (
        frappe.qb.from_(pa)
        .inner_join(item)
        .on(pa.billing_item == item.item_name)
        .left_join(ipd_rec)
        .on(pa.name == ipd_rec.patient_appointment)
        .select(
            pa.appointment_date.as_("date"),
            item.item_group.as_("category"),
            pa.billing_item.as_("description"),
            ValueWrapper(1).as_("quantity"),
            pa.paid_amount.as_("rate"),
            pa.paid_amount.as_("amount"),
            pa.patient.as_("patient"),
            pa.patient_name.as_("patient_name"),
            pa.appointment_type.as_("appointment_type"),
            pa.insurance_company.as_("insurance_company"),
            pa.coverage_plan_name.as_("coverage_plan_name"),
            pa.authorization_number.as_("authorization_number"),
            pa.coverage_plan_card_number.as_("coverage_plan_card_number"),
            fn.Date(ipd_rec.admitted_datetime).as_("admitted_date"),
            ipd_rec.discharge_date.as_("discharge_date"),
        )
        .where(
            (pa.status == "Closed")
            & (pa.follow_up == 0)
        )
    )

    # Apply filters
    if filters.get("patient"):
        query = query.where(pa.patient == filters.patient)

    if filters.get("patient_appointment"):
        query = query.where(pa.name == filters.patient_appointment)

    if filters.get("from_date"):
        query = query.where(pa.appointment_date >= filters.from_date)

    if filters.get("to_date"):
        query = query.where(pa.appointment_date <= filters.to_date)

    data = query.run(as_dict=True)

    return data


def get_ipd_occupancy_transactions(filters):
    """
    Fetch insurance IPD occupancy data from Inpatient Occupancy child table of Inpatient Record.
    Uses frappe.query_builder and pypika methods.
    """
    ipd_occ = DocType("Inpatient Occupancy")
    ipd_rec = DocType("Inpatient Record")
    hsu = DocType("Healthcare Service Unit")
    hsut = DocType("Healthcare Service Unit Type")
    pa = DocType("Patient Appointment")

    # Build the query
    query = (
        frappe.qb.from_(ipd_occ)
        .inner_join(ipd_rec)
        .on(ipd_occ.parent == ipd_rec.name)
        .inner_join(hsu)
        .on(ipd_occ.service_unit == hsu.name)
        .inner_join(hsut)
        .on(hsu.service_unit_type == hsut.name)
        .inner_join(pa)
        .on(ipd_rec.patient_appointment == pa.name)
        .select(
            fn.Date(ipd_occ.check_in).as_("date"),
            hsut.item_group.as_("category"),
            ipd_occ.service_unit.as_("description"),
            ValueWrapper(1).as_("quantity"),
            ipd_occ.amount.as_("rate"),
            ipd_occ.amount.as_("amount"),
            pa.patient.as_("patient"),
            pa.patient_name.as_("patient_name"),
            pa.appointment_type.as_("appointment_type"),
            pa.insurance_company.as_("insurance_company"),
            pa.coverage_plan_name.as_("coverage_plan_name"),
            pa.authorization_number.as_("authorization_number"),
            pa.coverage_plan_card_number.as_("coverage_plan_card_number"),
            fn.Date(ipd_rec.admitted_datetime).as_("admitted_date"),
            ipd_rec.discharge_date.as_("discharge_date"),
        )
        .where(
            (ipd_occ.is_confirmed == 1)
            & (pa.coverage_plan_name.isnotnull())
            & (pa.coverage_plan_name != "")
        )
    )

    # Apply filters
    if filters.get("patient"):
        query = query.where(ipd_rec.patient == filters.patient)

    if filters.get("patient_appointment"):
        query = query.where(ipd_rec.patient_appointment == filters.patient_appointment)

    if filters.get("from_date"):
        query = query.where(fn.Date(ipd_rec.admitted_datetime) >= filters.from_date)

    if filters.get("to_date"):
        query = query.where(fn.Date(ipd_rec.admitted_datetime) <= filters.to_date)

    data = query.run(as_dict=True)

    return data


def get_ipd_consultancy_transactions(filters):
    """
    Fetch insurance IPD consultancy data from Inpatient Consultancy child table of Inpatient Record.
    Uses frappe.query_builder and pypika methods.
    """
    ipd_cons = DocType("Inpatient Consultancy")
    ipd_rec = DocType("Inpatient Record")
    pa = DocType("Patient Appointment")
    item = DocType("Item")

    # Build the query
    query = (
        frappe.qb.from_(ipd_cons)
        .inner_join(ipd_rec)
        .on(ipd_cons.parent == ipd_rec.name)
        .inner_join(pa)
        .on(ipd_rec.patient_appointment == pa.name)
        .inner_join(item)
        .on(ipd_cons.consultation_item == item.item_name)
        .select(
            ipd_cons.date.as_("date"),
            item.item_group.as_("category"),
            ipd_cons.consultation_item.as_("description"),
            ValueWrapper(1).as_("quantity"),
            ipd_cons.rate.as_("rate"),
            ipd_cons.rate.as_("amount"),
            pa.patient.as_("patient"),
            pa.patient_name.as_("patient_name"),
            pa.appointment_type.as_("appointment_type"),
            pa.insurance_company.as_("insurance_company"),
            pa.coverage_plan_name.as_("coverage_plan_name"),
            pa.authorization_number.as_("authorization_number"),
            pa.coverage_plan_card_number.as_("coverage_plan_card_number"),
            fn.Date(ipd_rec.admitted_datetime).as_("admitted_date"),
            ipd_rec.discharge_date.as_("discharge_date"),
        )
        .where(
            (ipd_cons.is_confirmed == 1)
            & (pa.coverage_plan_name.isnotnull())
            & (pa.coverage_plan_name != "")
        )
    )

    # Apply filters
    if filters.get("patient"):
        query = query.where(ipd_rec.patient == filters.patient)

    if filters.get("patient_appointment"):
        query = query.where(ipd_rec.patient_appointment == filters.patient_appointment)

    if filters.get("from_date"):
        query = query.where(fn.Date(ipd_rec.admitted_datetime) >= filters.from_date)

    if filters.get("to_date"):
        query = query.where(fn.Date(ipd_rec.admitted_datetime) <= filters.to_date)

    data = query.run(as_dict=True)

    return data


def get_cash_lrpmt_transaction(filters):
    """
    Fetch cash LRPMT transaction data for cash patients.
    Uses frappe.query_builder and pypika methods.
    Combines Lab, Radiology, Procedure, Drug, and Therapy prescriptions.
    """
    # First, get the list of valid cash encounters
    encounters = get_cash_encounters(filters)
    if not encounters:
        return []

    data = []

    # Lab Prescriptions
    data += get_cash_lab_prescriptions(encounters, filters)

    # Radiology Prescriptions
    data += get_cash_radiology_prescriptions(encounters, filters)

    # Procedure Prescriptions
    data += get_cash_procedure_prescriptions(encounters, filters)

    # Drug Prescriptions
    data += get_cash_drug_prescriptions(encounters, filters)

    # Therapy Prescriptions
    data += get_cash_therapy_prescriptions(encounters, filters)

    return data


def get_cash_encounters(filters):
    """
    Get list of cash patient encounters based on filters.
    """
    pe = DocType("Patient Encounter")

    query = (
        frappe.qb.from_(pe)
        .select(pe.name)
        .where(
            (pe.mode_of_payment.isnotnull())
            & (pe.mode_of_payment != "")
            & (pe.docstatus == 1)
        )
    )

    if filters.get("patient"):
        query = query.where(pe.patient == filters.patient)

    if filters.get("patient_appointment"):
        query = query.where(pe.appointment == filters.patient_appointment)

    if filters.get("patient_type") == "Out-Patient":
        query = query.where(
            (pe.inpatient_record.isnull()) | (pe.inpatient_record == "")
        )

    if filters.get("patient_type") == "In-Patient":
        query = query.where(
            (pe.inpatient_record.isnotnull()) & (pe.inpatient_record != "")
        )

    if filters.get("from_date"):
        query = query.where(pe.encounter_date >= filters.from_date)

    if filters.get("to_date"):
        query = query.where(pe.encounter_date <= filters.to_date)

    query = query.orderby(pe.creation, order=frappe.qb.desc)

    result = query.run(as_dict=True)
    return [d.name for d in result]


def get_cash_lab_prescriptions(encounters, filters):
    """
    Fetch cash lab prescriptions.
    """
    lab = DocType("Lab Prescription")
    temp = DocType("Lab Test Template")
    pe = DocType("Patient Encounter")
    pa = DocType("Patient Appointment")
    ipd_rec = DocType("Inpatient Record")

    query = (
        frappe.qb.from_(lab)
        .inner_join(temp)
        .on(lab.lab_test_code == temp.name)
        .inner_join(pe)
        .on(lab.parent == pe.name)
        .inner_join(pa)
        .on(pe.appointment == pa.name)
        .left_join(ipd_rec)
        .on((pa.name == ipd_rec.patient_appointment) & (pe.name == ipd_rec.admission_encounter))
        .select(
            fn.Date(lab.creation).as_("date"),
            temp.lab_test_group.as_("category"),
            lab.lab_test_name.as_("description"),
            ValueWrapper(1).as_("quantity"),
            lab.amount.as_("rate"),
            lab.amount.as_("amount"),
            pa.patient.as_("patient"),
            pa.patient_name.as_("patient_name"),
            pa.appointment_type.as_("appointment_type"),
            pa.insurance_company.as_("insurance_company"),
            pa.coverage_plan_name.as_("coverage_plan_name"),
            pa.authorization_number.as_("authorization_number"),
            pa.coverage_plan_card_number.as_("coverage_plan_card_number"),
            fn.Date(ipd_rec.admitted_datetime).as_("admitted_date"),
            ipd_rec.discharge_date.as_("discharge_date"),
        )
        .where(
            (lab.is_not_available_inhouse == 0)
            & (lab.is_cancelled == 0)
            & (lab.prescribe == 1)
            & (lab.parent.isin(encounters))
        )
    )

    return query.run(as_dict=True)


def get_cash_radiology_prescriptions(encounters, filters):
    """
    Fetch cash radiology prescriptions.
    """
    rad = DocType("Radiology Procedure Prescription")
    temp = DocType("Radiology Examination Template")
    pe = DocType("Patient Encounter")
    pa = DocType("Patient Appointment")
    ipd_rec = DocType("Inpatient Record")

    query = (
        frappe.qb.from_(rad)
        .inner_join(temp)
        .on(rad.radiology_examination_template == temp.name)
        .inner_join(pe)
        .on(rad.parent == pe.name)
        .inner_join(pa)
        .on(pe.appointment == pa.name)
        .left_join(ipd_rec)
        .on((pa.name == ipd_rec.patient_appointment) & (pe.name == ipd_rec.admission_encounter))
        .select(
            fn.Date(rad.creation).as_("date"),
            temp.item_group.as_("category"),
            rad.radiology_procedure_name.as_("description"),
            ValueWrapper(1).as_("quantity"),
            rad.amount.as_("rate"),
            rad.amount.as_("amount"),
            pa.patient.as_("patient"),
            pa.patient_name.as_("patient_name"),
            pa.appointment_type.as_("appointment_type"),
            pa.insurance_company.as_("insurance_company"),
            pa.coverage_plan_name.as_("coverage_plan_name"),
            pa.authorization_number.as_("authorization_number"),
            pa.coverage_plan_card_number.as_("coverage_plan_card_number"),
            fn.Date(ipd_rec.admitted_datetime).as_("admitted_date"),
            ipd_rec.discharge_date.as_("discharge_date"),
        )
        .where(
            (rad.is_not_available_inhouse == 0)
            & (rad.is_cancelled == 0)
            & (rad.prescribe == 1)
            & (rad.parent.isin(encounters))
        )
    )

    return query.run(as_dict=True)


def get_cash_procedure_prescriptions(encounters, filters):
    """
    Fetch cash procedure prescriptions.
    """
    proc = DocType("Procedure Prescription")
    temp = DocType("Clinical Procedure Template")
    pe = DocType("Patient Encounter")
    pa = DocType("Patient Appointment")
    ipd_rec = DocType("Inpatient Record")

    query = (
        frappe.qb.from_(proc)
        .inner_join(temp)
        .on(proc.procedure == temp.name)
        .inner_join(pe)
        .on(proc.parent == pe.name)
        .inner_join(pa)
        .on(pe.appointment == pa.name)
        .left_join(ipd_rec)
        .on((pa.name == ipd_rec.patient_appointment) & (pe.name == ipd_rec.admission_encounter))
        .select(
            fn.Date(proc.creation).as_("date"),
            temp.item_group.as_("category"),
            proc.procedure_name.as_("description"),
            ValueWrapper(1).as_("quantity"),
            proc.amount.as_("rate"),
            proc.amount.as_("amount"),
            pa.patient.as_("patient"),
            pa.patient_name.as_("patient_name"),
            pa.appointment_type.as_("appointment_type"),
            pa.insurance_company.as_("insurance_company"),
            pa.coverage_plan_name.as_("coverage_plan_name"),
            pa.authorization_number.as_("authorization_number"),
            pa.coverage_plan_card_number.as_("coverage_plan_card_number"),
            fn.Date(ipd_rec.admitted_datetime).as_("admitted_date"),
            ipd_rec.discharge_date.as_("discharge_date"),
        )
        .where(
            (proc.is_not_available_inhouse == 0)
            & (proc.is_cancelled == 0)
            & (proc.prescribe == 1)
            & (proc.parent.isin(encounters))
        )
    )

    return query.run(as_dict=True)


def get_cash_drug_prescriptions(encounters, filters):
    """
    Fetch cash drug prescriptions.
    """
    drug = DocType("Drug Prescription")
    temp = DocType("Medication")
    pe = DocType("Patient Encounter")
    pa = DocType("Patient Appointment")
    ipd_rec = DocType("Inpatient Record")

    query = (
        frappe.qb.from_(drug)
        .inner_join(temp)
        .on(drug.drug_code == temp.name)
        .inner_join(pe)
        .on(drug.parent == pe.name)
        .inner_join(pa)
        .on(pe.appointment == pa.name)
        .left_join(ipd_rec)
        .on((pa.name == ipd_rec.patient_appointment) & (pe.name == ipd_rec.admission_encounter))
        .select(
            fn.Date(drug.creation).as_("date"),
            temp.item_group.as_("category"),
            drug.drug_name.as_("description"),
            (drug.quantity - drug.quantity_returned).as_("quantity"),
            drug.amount.as_("rate"),
            ((drug.quantity - drug.quantity_returned) * drug.amount).as_("amount"),
            pa.patient.as_("patient"),
            pa.patient_name.as_("patient_name"),
            pa.appointment_type.as_("appointment_type"),
            pa.insurance_company.as_("insurance_company"),
            pa.coverage_plan_name.as_("coverage_plan_name"),
            pa.authorization_number.as_("authorization_number"),
            pa.coverage_plan_card_number.as_("coverage_plan_card_number"),
            fn.Date(ipd_rec.admitted_datetime).as_("admitted_date"),
            ipd_rec.discharge_date.as_("discharge_date"),
        )
        .where(
            (drug.is_not_available_inhouse == 0)
            & (drug.is_cancelled == 0)
            & (drug.prescribe == 1)
            & (drug.docstatus == 1)
            & (drug.parent.isin(encounters))
        )
    )

    return query.run(as_dict=True)


def get_cash_therapy_prescriptions(encounters, filters):
    """
    Fetch cash therapy prescriptions.
    """
    therapy = DocType("Therapy Plan Detail")
    temp = DocType("Therapy Type")
    pe = DocType("Patient Encounter")
    pa = DocType("Patient Appointment")
    ipd_rec = DocType("Inpatient Record")

    query = (
        frappe.qb.from_(therapy)
        .inner_join(temp)
        .on(therapy.therapy_type == temp.name)
        .inner_join(pe)
        .on(therapy.parent == pe.name)
        .inner_join(pa)
        .on(pe.appointment == pa.name)
        .left_join(ipd_rec)
        .on((pa.name == ipd_rec.patient_appointment) & (pe.name == ipd_rec.admission_encounter))
        .select(
            fn.Date(therapy.creation).as_("date"),
            temp.item_group.as_("category"),
            therapy.therapy_type.as_("description"),
            (therapy.no_of_sessions - therapy.sessions_cancelled).as_("quantity"),
            therapy.amount.as_("rate"),
            ((therapy.no_of_sessions - therapy.sessions_cancelled) * therapy.amount).as_("amount"),
            pa.patient.as_("patient"),
            pa.patient_name.as_("patient_name"),
            pa.appointment_type.as_("appointment_type"),
            pa.insurance_company.as_("insurance_company"),
            pa.coverage_plan_name.as_("coverage_plan_name"),
            pa.authorization_number.as_("authorization_number"),
            pa.coverage_plan_card_number.as_("coverage_plan_card_number"),
            fn.Date(ipd_rec.admitted_datetime).as_("admitted_date"),
            ipd_rec.discharge_date.as_("discharge_date"),
        )
        .where(
            (therapy.is_not_available_inhouse == 0)
            & (therapy.is_cancelled == 0)
            & (therapy.prescribe == 1)
            & (therapy.parent.isin(encounters))
        )
    )

    return query.run(as_dict=True)


def get_insurance_lrpmt_transaction(filters):
    """
    Fetch insurance transaction data from Healthcare Service Request
    and its child table Healthcare Service Request Payment.
    This covers both OPD and IPD insurance patients.
    """
    hsr = DocType("Healthcare Service Request")
    hsrp = DocType("Healthcare Service Request Payment")
    pa = DocType("Patient Appointment")
    ipd_rec = DocType("Inpatient Record")
    item = DocType("Item")

    # Build the query using frappe.query_builder
    query = (
        frappe.qb.from_(hsr)
        .inner_join(hsrp)
        .on(hsrp.parent == hsr.name)
        .inner_join(pa)
        .on(hsr.appointment == pa.name)
        .left_join(ipd_rec)
        .on(pa.name == ipd_rec.patient_appointment)
        .left_join(item)
        .on(hsrp.service_name == item.item_name)
        .select(
            fn.Date(hsr.posting_datetime).as_("date"),
            Coalesce(item.item_group, hsrp.service_type).as_("category"),
            hsrp.service_name.as_("description"),
            (hsrp.qty - Coalesce(hsrp.qty_returned, 0)).as_("quantity"),
            hsrp.rate.as_("rate"),
            ((hsrp.qty - Coalesce(hsrp.qty_returned, 0)) * hsrp.rate).as_("amount"),
            pa.patient.as_("patient"),
            pa.patient_name.as_("patient_name"),
            pa.appointment_type.as_("appointment_type"),
            hsr.insurance_company.as_("insurance_company"),
            hsr.insurance_coverage_plan.as_("coverage_plan_name"),
            hsrp.authorization_number.as_("authorization_number"),
            hsr.card_no.as_("coverage_plan_card_number"),
            fn.Date(ipd_rec.admitted_datetime).as_("admitted_date"),
            ipd_rec.discharge_date.as_("discharge_date"),
        )
        .where(
            (hsr.payment_type == "Insurance")
            & (hsr.docstatus == 1)
            & (hsrp.is_cancelled == 0)
            & (hsrp.payment_type == "Insurance")
        )
        .orderby(hsr.posting_datetime)
    )

    # Apply filters
    if filters.get("patient"):
        query = query.where(hsr.patient == filters.patient)

    if filters.get("patient_appointment"):
        query = query.where(hsr.appointment == filters.patient_appointment)

    if filters.get("from_date"):
        query = query.where(fn.Date(hsr.posting_datetime) >= filters.from_date)

    if filters.get("to_date"):
        query = query.where(fn.Date(hsr.posting_datetime) <= filters.to_date)

    # Apply patient type filter if specified
    if filters.get("patient_type") == "Out-Patient":
        query = query.where(
            (ipd_rec.name.isnull()) | (ipd_rec.name == "")
        )
    elif filters.get("patient_type") == "In-Patient":
        query = query.where(
            (ipd_rec.name.isnotnull()) & (ipd_rec.name != "")
        )

    data = query.run(as_dict=True)

    return data


def get_report_summary(filters, total_amount):
    customer = frappe.get_cached_value("Patient", filters.get("patient"), "customer")
    company = frappe.get_cached_value("Patient Appointment", filters.get("patient_appointment"), "company")

    deposit_balance = -1 * get_balance_on(party_type="Customer", party=customer, company=company)

    current_balance = flt(flt(deposit_balance) - flt(total_amount))

    currency = frappe.get_cached_value("Company", company, "default_currency")

    return [
        {
            "value": deposit_balance,
            "label": _("Total Deposited Amount"),
            "datatype": "Currency",
            "currency": currency,
        },
        {
            "value": total_amount,
            "label": _("Total Amount Used"),
            "datatype": "Currency",
            "currency": currency,
        },
        {
            "value": current_balance,
            "label": _("Current Balance"),
            "datatype": "Currency",
            "currency": currency,
        },
    ]
