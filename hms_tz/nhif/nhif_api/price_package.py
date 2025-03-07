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
            ref_doctype="NHIF Item Type",
        )


@frappe.whitelist()
def enqueue_get_nhif_price_packages(company):
    enqueue(
        method=get_price_package,
        job_name="get_nhif_price_packages",
        queue="long",
        timeout=None,
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
