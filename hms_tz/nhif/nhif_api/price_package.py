import json
import frappe
import requests
from time import sleep
from frappe.utils import now_datetime
from pypika.terms import ValueWrapper
from frappe.query_builder import DocType
from frappe.model.naming import make_autoname
from frappe.utils.background_jobs import enqueue
from hms_tz.nhif.doctype.nhif_response_log.nhif_response_log import add_log


def  get_item_types():
    settings = frappe.db.get_all("HMS TZ Settings", filters={"enable_nhif_api": 1}, fields=["company"])
    if len(settings) == 0:
        return
    
    settings_doc = frappe.get_cached_doc("HMS TZ Settings", settings[0].company)

    token = settings_doc.get_nhif_token()

    url = f"{settings_doc.nhif_claim_url}/api/Packages/GetItemTypes"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    r = requests.request("Get", url, headers=headers, timeout=60)
    if r.status_code == 200:
        data = json.loads(r.text)
        add_log(
            request_type="GetItemTypes",
            request_url=url,
            request_header=headers,
            request_body="",
            response_data=data,
            status_code=r.status_code,
            company=settings_doc.name,
            ref_doctype="NHIF Item Type",
        )

        for item in data:
            item_type = frappe.db.get_value("NHIF Item Type", {"item_type_id": item["ItemTypeID"]}, "name")
            if item_type:
                has_changed = False
                doc = frappe.get_doc("NHIF Item Type", item_type)

                if doc.type_name != item["TypeName"]:
                    doc.type_name = item["TypeName"]
                    has_changed = True

                if doc.alias != item["Alias"]:
                    doc.alias = item["Alias"]
                    has_changed = True
                if doc.item_group != item["ItemGroup"]:
                    doc.item_group = item["ItemGroup"]
                    has_changed = True
                if doc.display_item != item["DisplayItem"]:
                    doc.display_item = item["DisplayItem"]
                    has_changed = True
                
                if has_changed:
                    doc.save(ignore_permissions=True)
                
            else:
                doc = frappe.new_doc("NHIF Item Type")
                doc.item_type_id = item["ItemTypeID"]
                doc.type_name = item["TypeName"]
                doc.alias = item["Alias"]
                doc.item_group = item["ItemGroup"]
                doc.display_item = item["DisplayItem"]

                doc.save(ignore_permissions=True)

    else:
        add_log(
            request_type="GetItemTypes",
            request_url=url,
            request_header=headers,
            request_body="",
            response_data=r.text,
            status_code=r.status_code,
            company=settings_doc.name,
            ref_doctype="NHIF Item Type",
        )


@frappe.whitelist()
def enqueue_get_nhif_price_packages(company):
    enqueue(
        method=get_price_package,
        job_name="get_nhif_price_packages",
        queue="long",
        timeout=7200,
        is_async=True,
        company=company,
    )


def get_price_package(company):
    settings_doc = frappe.get_cached_doc("HMS TZ Settings", company)
    token = settings_doc.get_nhif_token()

    url = f"{settings_doc.nhif_claim_url}/api/Packages/GetPricePackage?facilityCode={settings_doc.facility_code}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    r = requests.request("Get", url, headers=headers, timeout=60)
    if r.status_code != 200:
        add_log(
            request_type="GetPricePackage",
            request_url=url,
            request_header=headers,
            request_body="",
            response_data=r.text,
            status_code=r.status_code,
            company=settings_doc.name,
            ref_doctype="NHIF Price Package",
        )
        frappe.throw(json.loads(r.text))
    else:
        packages = json.loads(r.text)
        log_name = add_log(
            request_type="GetPricePackage",
            request_url=url,
            request_header=headers,
            request_body="",
            response_data=packages,
            status_code=r.status_code,
            company=settings_doc.name,
            ref_doctype="NHIF Price Package",
        )

        sync_price_package(
            company,
            settings_doc.facility_code,
            packages,
            log_name
        )


def sync_price_package(company,facility_code, packages, log_name):
    if len(packages) == 0:
        return

    delete_price_package(company)
    
    sleep(30)
    create_price_package(company, facility_code, packages, log_name)

    sleep(30)
    enqueue(
        method=set_package_diff,
        job_name="set_nhif_diff_records",
        queue="long",
        timeout=3600,
        is_async=True,
        company=company,
    )


def delete_price_package(company):
    npp = DocType("NHIF Price Package")
    frappe.qb.from_(npp).delete().where(npp.company == company).run()


def create_price_package(company, facility_code, packages, log_name):
    fields = [
        "name",
        "creation",
        "owner",
        "modified",
        "modified_by",
        "time_stamp",
        "log_name",
        "company",
        "facilitycode",
        "itemcode",
        "itemtypeid",
        "pricecode",
        "itemname",
        "schemeid",
        "packageid",
        "isrestricted",
        "hascopayment",
        "strength",
        "dosage",
        "unitprice",
        "maximumquantity",
        "maximumquantityoutpatient",
        "maximumquantityinpatient",
    ]

    data = []
    for row in packages:
        npp_name = make_autoname(key='hash')

        data.append(
            (
                npp_name,
                now_datetime(),
                frappe.session.user,
                now_datetime(),
                frappe.session.user,
                now_datetime(),
                log_name,
                company,
                facility_code,
                row.get("ItemCode"),
                row.get("ItemTypeID"),
                row.get("PriceCode"),
                row.get("ItemName"),
                row.get("SchemeID"),
                row.get("PackageID"),
                row.get("IsRestricted"),
                row.get("HasCoPayment"),
                row.get("Strength"),
                row.get("Dosage"),
                row.get("UnitPrice"),
                row.get("MaximumQuantity"),
                row.get("MaximumQuantityOutPatient"),
                row.get("MaximumQuantityInPatient"),
            )
        )
    frappe.db.bulk_insert(
        "NHIF Price Package",
        fields=fields,
        values=data,
        ignore_duplicates=True
    )
    frappe.db.commit()
    return True


def set_package_diff(company):
    logs = frappe.get_all(
        "NHIF Response Log",
        filters={
            "request_type": "GetPricePackage",
            "response_data": ["not in", ["", None]],
            "company": company,
            "status_code": 200,
        },
        fields=["name", "response_data"],
        order_by="creation desc",
        page_length=2,
    )
    if len(logs) < 2:
        return
    
    new_price_packages = []
    changed_price_packages = []
    deleted_price_packages = []

    current_package = json.loads(logs[0]["response_data"])
    previous_package = json.loads(logs[1]["response_data"])
    
    current_items = {(item["ItemCode"], item["SchemeID"]): item for item in current_package}
    previous_items = {(item["ItemCode"], item["SchemeID"]): item for item in previous_package}

    new_price_packages = [item for code, item in current_items.items() if code not in previous_items]
    deleted_price_packages = [item for code, item in previous_items.items() if code not in current_items]

    changed_price_packages = []
    for key, current_item in current_items.items():
        if key in previous_items:
            previous_item = previous_items[key]
            if current_item != previous_item:
                fields_changed = {
                    field: {"current": current_item[field], "previous": previous_item[field]}
                    for field in current_item
                    if field in previous_item and current_item[field] != previous_item[field]
                }

                new_row = current_item.copy()
                new_row["fields_changed"] = fields_changed
                new_row["previous_item"] = previous_item

                changed_price_packages.append(new_row)

    if (
        len(changed_price_packages) > 0
        or len(new_price_packages) > 0
        or len(deleted_price_packages) > 0
    ):
        service_map = get_insurance_items()

        doc = frappe.new_doc("NHIF Update")

        add_price_packages_records(doc, changed_price_packages, "Changed", service_map)
        add_price_packages_records(doc, new_price_packages, "New", service_map)
        add_price_packages_records(doc, deleted_price_packages, "Deleted", service_map)

        if (doc.get("price_package") and len(doc.price_package)) > 0:
            doc.timestamp = now_datetime()
            doc.user_id = frappe.session.user
            doc.company = company
            doc.current_log = logs[0].name
            doc.previous_log = logs[1].name
            doc.save(ignore_permissions=True)


def add_price_packages_records(doc, rec, type, service_map):
    if len(rec) == 0:
        return

    for e in rec:
        price_row = doc.append("price_package", {})
        price_row.type = type

        if service_map.get(e.get("ItemCode")):
            price_row.service_type = service_map.get(e.get("ItemCode")).get("service_type")
            price_row.service_name = service_map.get(e.get("ItemCode")).get("service_name")
        
        price_row.itemcode = e.get("ItemCode")
        price_row.itemname = e.get("ItemName")
        price_row.itemtypeid = e.get("ItemTypeID")
        price_row.strength = e.get("Strength")
        price_row.dosage = e.get("Dosage")
        price_row.schemeid = e.get("SchemeID")
        price_row.packageid = e.get("PackageID")
        price_row.pricecode = e.get("PriceCode")
        price_row.unitprice = e.get("UnitPrice")
        price_row.isrestricted = e.get("IsRestricted")
        price_row.hascopayment = e.get("HasCoPayment")
        price_row.maximumquantity = e.get("MaximumQuantity")
        price_row.maximumquantityoutpatient = e.get("MaximumQuantityOutPatient")
        price_row.maximumquantityinpatient = e.get("MaximumQuantityInPatient")
        price_row.fields_changed = json.dumps(e.get("fields_changed"))
        price_row.previous_item = json.dumps(e.get("previous_item"))


def get_insurance_items():
    services = []
    consultation_items = []

    it = DocType("Item")
    icd = DocType("Item Customer Detail")
    at = DocType("Appointment Type")
    hp = DocType("Healthcare Practitioner")
    ltt = DocType("Lab Test Template")
    ret = DocType("Radiology Examination Template")
    cpt = DocType("Clinical Procedure Template")
    med = DocType("Medication")
    tt = DocType("Therapy Type")
    hsut = DocType("Healthcare Service Unit Type")

    practitioner_services = (
        frappe.qb.from_(hp)
        .select(
            hp.op_consulting_charge_item,
            hp.inpatient_visit_charge_item
        )
        .distinct()
    ).run(as_dict=True)

    for row in practitioner_services:
        for field in row:
            if row[field]:
                consultation_items.append(row[field])

    appointment_services = (
        frappe.qb.from_(at)
        .select(
            at.assistant_md_followup_item,
            at.gp_followup_item,
            at.specialist_followup_item,
            at.super_specialist_followup_item,
            at.assistant_md_fasttrack_item,
            at.gp_fasttrack_item,
            at.specialist_fasttrack_item,
            at.super_specialist_fasttrack_item,
        )
        .distinct()
    ).run(as_dict=True)

    for row in appointment_services:
        for field in row:
            if row[field]:
                consultation_items.append(row[field])
    
    services += (
        frappe.qb.from_(icd)
        .inner_join(it)
        .on(icd.parent == it.name)
        .select(
            icd.ref_code,
            it.name.as_("service_name"),
            ValueWrapper("Consulation Charges").as_("service_type"),
        )
        .where(
            (icd.customer_name == "NHIF")
            & (
                (icd.ref_code.isnotnull()) & 
                (icd.ref_code != "")
            )
            & (it.name.isin(consultation_items))
        )
    ).run(as_dict=True)

    services += (
        frappe.qb.from_(icd)
        .inner_join(ltt)
        .on(icd.parent == ltt.item)
        .select(
            icd.ref_code,
            ltt.name.as_("service_name"),
            ValueWrapper("Lab Test Template").as_("service_type"),
        )
        .where(
            (icd.customer_name == "NHIF")
            & (
                (icd.ref_code.isnotnull()) & 
                (icd.ref_code != "")
            )
        )
    ).run(as_dict=True)

    services += (
        frappe.qb.from_(icd)
        .inner_join(ret)
        .on(icd.parent == ret.item)
        .select(
            icd.ref_code,
            ret.name.as_("service_name"),
            ValueWrapper("Radiology Examination Template").as_("service_type"),
        )
        .where(
            (icd.customer_name == "NHIF")
            & (
                (icd.ref_code.isnotnull()) & 
                (icd.ref_code != "")
            )
        )
    ).run(as_dict=True)

    services += (
        frappe.qb.from_(icd)
        .inner_join(cpt)
        .on(icd.parent == cpt.item)
        .select(
            icd.ref_code,
            cpt.name.as_("service_name"),
            ValueWrapper("Clinical Procedure Template").as_("service_type"),
        )
        .where(
            (icd.customer_name == "NHIF")
            & (
                (icd.ref_code.isnotnull()) & 
                (icd.ref_code != "")
            )
        )
    ).run(as_dict=True)

    services += (
        frappe.qb.from_(icd)
        .inner_join(med)
        .on(icd.parent == med.item)
        .select(
            icd.ref_code,
            med.name.as_("service_name"),
            ValueWrapper("Medication").as_("service_type"),
        )
        .where(
            (icd.customer_name == "NHIF")
            & (
                (icd.ref_code.isnotnull()) & 
                (icd.ref_code != "")
            )
        )
    ).run(as_dict=True)

    services += (
        frappe.qb.from_(icd)
        .inner_join(tt)
        .on(icd.parent == tt.item)
        .select(
            icd.ref_code,
            tt.name.as_("service_name"),
            ValueWrapper("Therapy Type").as_("service_type"),
        )
        .where(
            (icd.customer_name == "NHIF")
            & (
                (icd.ref_code.isnotnull()) & 
                (icd.ref_code != "")
            )
        )
    ).run(as_dict=True)

    services += (
        frappe.qb.from_(icd)
        .inner_join(hsut)
        .on(icd.parent == hsut.item)
        .select(
            icd.ref_code,
            hsut.name.as_("service_name"),
            ValueWrapper("Healthcare Service Unit Type").as_("service_type"),
        )
        .where(
            (icd.customer_name == "NHIF")
            & (
                (icd.ref_code.isnotnull()) & 
                (icd.ref_code != "")
            )
        )
    ).run(as_dict=True)

    service_map = {}
    for service in services:
        service_map[service["ref_code"]] = service
    
    return service_map