import json
import frappe
import requests
from frappe import _
from time import sleep
from frappe.query_builder import DocType
from frappe.utils import flt, now_datetime
from hms_tz.jubilee.doctype.jubilee_response_log.jubilee_response_log import add_jubilee_log



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
    log_name,
    insurance_provider="Jubilee"
):
    if len(packages) == 0:
        return
    
    delete_price_package(company)

    sleep(30)
    create_price_package(packages, company, log_name)

    # sleep(30)
    # set_package_diff(company)


def delete_price_package(company):
    jpp = DocType("Jubilee Price Package")
    frappe.qb.from_(jpp).delete().where(jpp.company == company).run()


def create_price_package(packages, company, log_name):
    fields = [
        "name",
        "timestamp",
        "log_name",
        "company",
        "providerid",
        "itemcode",
        # "strength",
        # "dosage",
        "itemprice",
        "itemname",
        "cleanname"
    ]

    data = []
    timestamp = now_datetime()
    for row in packages:
        jpp_name = frappe.generate_hash(length=10)

        data.append(
            (
                jpp_name,
                timestamp,
                log_name,
                company,
                row.get("ProviderID"),
                row.get("ItemCode"),
                # row.get("Strength"),
                # row.get("Dosage"),
                row.get("ItemPrice"),
                row.get("ItemName"),
                row.get("CleanName"),
            )
        )
    
    frappe.db.bulk_insert(
        "Jubilee Price Package", fields=fields, values=data, chunk_size=1000
    )

