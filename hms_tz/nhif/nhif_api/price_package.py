import json
import frappe
import requests
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

