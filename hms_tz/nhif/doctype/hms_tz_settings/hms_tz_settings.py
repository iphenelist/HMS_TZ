# Copyright (c) 2025, Aakvatech and contributors
# For license information, please see license.txt

import json
import frappe
import requests
from time import sleep
from datetime import datetime
from frappe.model.document import Document
from frappe.utils import now_datetime, add_to_date
from hms_tz.nhif.doctype.nhif_response_log.nhif_response_log import add_log


class HMSTZSettings(Document):
	def get_nhif_token(self):
		if self.enable_nhif_api == 0:
			frappe.msgprint("Please Enable NHIF API to proceed..")
			return
		
		if (
			self.nhif_token_expiry and 
			self.nhif_token_expiry > now_datetime()
		):
			return self.nhif_token

		payload = {
            "grant_type": self.nhif_grant_type,
            "client_id": self.facility_code,
            "client_secret": self.get_password("nhif_client_secret"),
            "scope": self.nhif_scope,
            "user": self.nhif_user
        }

		headers = {
			"Accept": "application/json",
			'Content-Type': 'application/x-www-form-urlencoded'
		}

		url = f"{self.nhif_token_url}"

		for i in range(3):
			try:
				r = requests.request("POST", url, headers=headers, data=payload)
				r.raise_for_status()

				data = json.loads(r.text)

				if data:
					add_log(
						request_type="Token",
						request_url=url,
						request_header=headers,
						request_body=payload,
						response_data=data,
						status_code=r.status_code,
					)

				if data["token_type"].lower() == "bearer":
					token = data["access_token"]
					expired = data["expires_in"]
					expiry_date = add_to_date(now_datetime(), seconds=(expired - 1000))
					
					self.update({
						"nhif_token": token,
						"nhif_token_expiry": expiry_date
					})

					self.db_update()
					self.reload()
					return token
				else:
					add_log(
						request_type="Token",
						request_url=url,
						request_header=headers,
						request_body=payload,
						status_code=r.status_code,
					)
					frappe.throw(str(data))
			
			except Exception as e:
				sleep(3 * i + 1)
				if i != 2:
					continue
				else:
					raise e
