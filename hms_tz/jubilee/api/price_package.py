import json
import frappe
import requests
from frappe import _
from time import sleep
from frappe.query_builder import DocType
from frappe.model.naming import make_autoname
from frappe.utils.background_jobs import enqueue
from frappe.utils import flt, now_datetime, create_batch
from hms_tz.jubilee.doctype.jubilee_response_log.jubilee_response_log import add_jubilee_log
from hms_tz.api.insurance import (
    get_insurance_items,
    delete_price_package,
    delete_hsic_data,
    get_items_for_price_list,
    handle_insurance_prices
)


def get_jubilee_price_packages(company):
    if not company:
        frappe.throw(_("No companies found to connect to Jubilee"))

    settings_doc = frappe.get_cached_doc("HMS TZ Setting", company)

    token = settings_doc.get_jubilee_token()
    headers = {"Authorization": "Bearer " + token}
    url = str(settings_doc.jubilee_url) + "/jubileeapi/GetPriceList"

    r = requests.get(url, headers=headers, timeout=60)
    if r.status_code != 200:
        add_jubilee_log(
            request_type="GetPricePackage",
            request_url=url,
            request_header=headers,
            request_body="",
            response_data=r.text,
            status_code=r.status_code,
            company=company,
            ref_doctype="Jubilee Price Package",
        )
        frappe.throw(json.loads(r.text))
    else:
        data = json.loads(r.text)
        log_name = add_jubilee_log(
            request_type="GetPricePackage",
            request_url=url,
            request_header=headers,
            request_body="",
            response_data=data,
            status_code=r.status_code,
            ref_doctype="Jubilee Price Package",
            company=company,
        )

        packages = data["Description"]
        sync_price_package(packages, company, log_name)


def sync_price_package(
    packages,
    company,
    log_name
):
    if len(packages) == 0:
        return

    delete_price_package("Jubilee Price Package", company)

    sleep(30)
    create_price_package(packages, company, log_name)

    sleep(30)
    enqueue(
        method=set_package_diff,
        job_name="set_jubilee_diff_records",
        queue="long",
        timeout=3600,
        is_async=True,
        company=company,
    )


def create_price_package(packages, company, log_name):
    fields = [
        "name",
        "timestamp",
        "log_name",
        "company",
        "providerid",
        "itemcode",
        "strength",
        "dosage",
        "itemprice",
        "itemname",
        "cleanname"
    ]

    data = []
    timestamp = now_datetime()
    for row in packages:
        jpp_name = make_autoname(key="hash")

        data.append(
            (
                jpp_name,
                timestamp,
                log_name,
                company,
                row.get("ProviderID"),
                row.get("ItemCode"),
                row.get("Strength"),
                row.get("Dosage"),
                row.get("ItemPrice"),
                row.get("ItemName"),
                row.get("CleanName"),
            )
        )
    
    frappe.db.bulk_insert(
        "Jubilee Price Package",
        fields=fields,
        values=data,
        ignore_duplicates=True
    )
    frappe.db.commit()
    return True


def set_package_diff(company):
    logs = frappe.get_all(
        "Jubilee Response Log",
        filters={
            "request_type": "GetPricePackage",
            "response_data": ["not in", ["", None]],
            "company": company,
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

    current_rec = json.loads(logs[0]["response_data"])
    previous_rec = json.loads(logs[1]["response_data"])

    current_package = current_rec.get("Description")
    previous_package = previous_rec.get("Description")

    current_items = {item["ItemCode"]: item for item in current_package}
    previous_items = {item["ItemCode"]: item for item in previous_package}

    new_price_packages = [item for code, item in current_items.items() if code not in previous_items]
    deleted_price_packages = [item for code, item in previous_items.items() if code not in current_items]
    
    for key, current_item in current_items.items():
        if key in previous_items:
            previous_item = previous_items[key]
            if current_item != previous_item:
                fields_changed = {
                    field: {
                        "current": current_item[field],
                        "previous": previous_item[field],
                    }
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
        service_map = get_insurance_items("The Jubilee Insurance (T) Ltd", for_prices=True)

        doc = frappe.new_doc("Jubilee Update")

        add_price_packages_records(doc, changed_price_packages, "Changed", service_map)
        add_price_packages_records(doc, new_price_packages, "New", service_map)
        add_price_packages_records(doc, deleted_price_packages, "Deleted", service_map)

        if doc.get("price_package") and len(doc.price_package) > 0:
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
        # price_row.olditemcode = e.get("OldItemCode")
        price_row.itemname = e.get("ItemName")
        price_row.strength = e.get("Strength")
        price_row.dosage = e.get("Dosage")
        price_row.unitprice = e.get("UnitPrice")
        # price_row.record = json.dumps(e)
        price_row.fields_changed = json.dumps(e.get("fields_changed"))
        price_row.previous_item = json.dumps(e.get("previous_item"))


def process_jubilee_prices(company, item=None):
    itp = DocType("Item Price")

    company_info = frappe.get_cached_value(
        "Company", company, ["abbr", "default_currency"], as_dict=True
    )

    default_currency = company_info.default_currency
    price_list_name = f"Jubilee {company_info.abbr}"

    if not frappe.db.exists("Price List", price_list_name):
        price_list_doc = frappe.new_doc("Price List")
        price_list_doc.price_list_name = price_list_name
        price_list_doc.currency = default_currency
        price_list_doc.buying = 0
        price_list_doc.selling = 1
        price_list_doc.save(ignore_permissions=True)

    item_list = get_items_for_price_list(company, item)

    for batch in create_batch(item_list, 1000):
        for item in batch:
            handle_insurance_prices(itp, item, price_list_name, default_currency)

        frappe.db.commit()

