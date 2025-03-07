import json
import frappe
import requests
from time import sleep
from frappe.utils import now_datetime
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

                changed_price_packages.append({new_row})

    if (
        len(changed_price_packages) > 0
        or len(new_price_packages) > 0
        or len(deleted_price_packages) > 0
    ):
        doc = frappe.new_doc("NHIF Update")

        add_price_packages_records(doc, changed_price_packages, "Changed")
        add_price_packages_records(doc, new_price_packages, "New")
        add_price_packages_records(doc, deleted_price_packages, "Deleted")

        if (doc.get("price_package") and len(doc.price_package)) > 0:
            doc.timestamp = now_datetime()
            doc.user_id = frappe.session.user
            doc.company = company
            doc.current_log = logs[0].name
            doc.previous_log = logs[1].name
            doc.save(ignore_permissions=True)


def add_price_packages_records(doc, rec, type):
    if len(rec) == 0:
        return

    for e in rec:
        price_row = doc.append("price_package", {})
        price_row.type = type
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
        price_row.record = json.dumps(e)