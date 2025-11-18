import json
import frappe
import requests
from frappe import _
from erpnext import get_default_company
from hms_tz.jubilee.doctype.jubilee_response_log.jubilee_response_log import add_jubilee_log


@frappe.whitelist()
def get_member_card_detials(card_no, insurance_provider=None):
    if not card_no or insurance_provider != "Jubilee":
        return

    company = get_default_company()
    if not company:
        company = frappe.defaults.get_user_default("Company")

    if not company:
        hms_tz_records = frappe.get_list(
            "HMS TZ Setting",
            fields=["company"],
            filters={"enable_jubilee_api": 1},
            limit=1,
        )

        if len(hms_tz_records) > 0:
            company = hms_tz_records[0].company

    if not company:
        frappe.throw(_("No companies found to connect to Jubilee"))

    setting_doc = frappe.get_cached_doc("HMS TZ Setting", company)

    token = setting_doc.get_jubilee_token()
    headers = {"Authorization": "Bearer " + token}
    url = f"{setting_doc.jubilee_url}/jubileeapi/Getcarddetails?MemberNo={str(card_no)}"

    r = requests.get(url, headers=headers, timeout=60)
    r.raise_for_status()

    data = json.loads(r.text)

    if data.get("Status") == "OK":
        add_jubilee_log(
            request_type="GetCardDetails",
            request_url=url,
            request_header=headers,
            response_data=data,
            status_code=r.status_code,
            company=company,
            ref_doctype="Patient",
            card_no=card_no,
        )
        frappe.msgprint(_(data["Status"]), alert=True)
        return data
    else:
        add_jubilee_log(
            request_type="GetCardDetails",
            request_url=url,
            request_header=headers,
            response_data=data,
            status_code=r.status_code,
            company=company,
            ref_doctype="Patient",
            card_no=card_no,
        )

        frappe.msgprint(
            title="Jubilee API Error",
            msg=f"Failed to Fetch card details<br><br>Status Code: {r.status_code}<br>Jubilee Response: <b>{data.get('Description')}<b>",
            indicator="red",
        )

        return 'Error'