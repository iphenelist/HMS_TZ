import json
import frappe
import requests
from hms_tz.nhif.doctype.nhif_response_log.nhif_response_log import add_log


@frappe.whitelist()
def get_points_of_care():
    settings = frappe.db.get_all("HMS TZ Settings", filters={"enable_nhif_api": 1}, fields=["company"])
    if len(settings) == 0:
        return
    
    setting_doc = frappe.get_cached_doc("HMS TZ Settings", settings[0].company)

    token = setting_doc.get_nhif_token()

    url = f"{setting_doc.nhifservice_url}/api/Reference/GetPointsOfCare"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    r = requests.request("Get", url, headers=headers, timeout=60)
    if r.status_code == 200:
        data = json.loads(r.text)
        add_log(
            request_type="GetPointsOfCare",
            request_url=url,
            request_header=headers,
            request_body="",
            response_data=data,
            status_code=r.status_code
        )

        for poc in data:
            try:
                if frappe.db.exists("Healthcare Points of Care", poc.get("PointOfCareName"), cache=True):
                    has_changed = False
                    hpc_doc = frappe.get_cached_doc("Healthcare Points of Care", poc.get("PointOfCareName"))
                    
                    if hpc_doc.point_of_care_id != str(poc.get("PointOfCareID")):
                        has_changed = True
                        hpc_doc.point_of_care_id = poc.get("PointOfCareID")
                    
                    if hpc_doc.point_of_care_code != str(poc.get("PointOfCareCode")):
                        has_changed = True
                        hpc_doc.point_of_care_code = poc.get("PointOfCareCode")

                    if has_changed:
                        hpc_doc.save(ignore_permissions=True)
                
                else:
                    hpc_doc = frappe.new_doc("Healthcare Points of Care")
                    hpc_doc.point_of_care_name = poc.get("PointOfCareName")
                    hpc_doc.point_of_care_id = poc.get("PointOfCareID")
                    hpc_doc.point_of_care_code = poc.get("PointOfCareCode")
                    hpc_doc.save(ignore_permissions=True)
                    hpc_doc.reload()
            except:
                traceback = frappe.get_traceback()
                frappe.log_error(
                    title="GetPointsOfCare",
                    message=traceback
                )
    else:
        add_log(
            request_type="GetPointsOfCare",
            request_url=url,
            request_header=headers,
            request_body="",
            response_data=r.text,
            status_code=r.status_code
        )


