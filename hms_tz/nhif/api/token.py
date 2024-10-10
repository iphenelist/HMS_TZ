# -*- coding: utf-8 -*-
# Copyright (c) 2020, Aakvatech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import get_url_to_form, get_url
from frappe import _
from frappe.utils.password import get_decrypted_password
import json
import requests
from time import sleep
from frappe.utils import now, add_to_date, now_datetime, cstr
from hms_tz.nhif.doctype.nhif_response_log.nhif_response_log import add_log


def make_token_request(doc, url, headers, payload, fields):
    for i in range(3):
        try:
            r = requests.request("POST", url, headers=headers, data=payload, timeout=5)
            r.raise_for_status()
            frappe.logger().debug({"webhook_success": r.text})

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
                expiry_date = add_to_date(now(), seconds=(expired - 1000))
                doc.update({fields["token"]: token, fields["expiry"]: expiry_date})

                doc.db_update()
                frappe.db.commit()
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
            frappe.logger().debug({"webhook_error": e, "try": i + 1})
            sleep(3 * i + 1)
            if i != 2:
                continue
            else:
                raise e


def get_nhifservice_token(company):
    setting_doc = frappe.get_cached_doc("Company NHIF Settings", company)
    if (
        setting_doc.nhifservice_expiry
        and setting_doc.nhifservice_expiry > now_datetime()
    ):
        return setting_doc.nhifservice_token

    username = setting_doc.username
    password = get_decrypted_password("Company NHIF Settings", company, "password")
    payload = f"grant_type=password&username={username}&password={password}"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    
    url, extra_params = get_nhif_url(setting_doc, caller="Token")
    # url = str(setting_doc.nhifservice_url) + "/nhifservice/Token"

    nhifservice_fields = {
        "token": "nhifservice_token",
        "expiry": "nhifservice_expiry",
    }

    if extra_params:
        payload = payload + extra_params

    return make_token_request(setting_doc, url, headers, payload, nhifservice_fields)


def get_claimsservice_token(company):
    setting_doc = frappe.get_cached_doc("Company NHIF Settings", company)
    if (
        setting_doc.claimsserver_expiry
        and setting_doc.claimsserver_expiry > now_datetime()
    ):
        return setting_doc.claimsserver_token

    username = setting_doc.username
    password = get_decrypted_password("Company NHIF Settings", company, "password")
    payload = "grant_type=password&username={0}&password={1}".format(username, password)
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    url = get_nhif_url(setting_doc, caller="Token")
    # url = str(setting_doc.claimsserver_url) + "/claimsserver/Token"

    claimserver_fields = {
        "token": "claimsserver_token",
        "expiry": "claimsserver_expiry",
    }

    return make_token_request(setting_doc, url, headers, payload, claimserver_fields)


def get_formservice_token(company):
    company_nhif_doc = frappe.get_cached_doc("Company NHIF Settings", company)
    if not company_nhif_doc.enable:
        frappe.throw(_("Company {0} not enabled for NHIF Integration".format(company)))

    if (
        company_nhif_doc.nhifform_expiry
        and company_nhif_doc.nhifform_expiry > now_datetime()
    ):
        return company_nhif_doc.nhifform_token

    username = company_nhif_doc.username
    password = get_decrypted_password("Company NHIF Settings", company, "password")
    payload = "grant_type=password&username={0}&password={1}".format(username, password)

    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    url = get_nhif_url(setting_doc, caller="Token")
    # url = cstr(company_nhif_doc.nhifform_url) + "/formposting/Token"

    nhifform_fields = {
        "token": "nhifform_token",
        "expiry": "nhifform_expiry",
    }

    return make_token_request(company_nhif_doc, url, headers, payload, nhifform_fields)


def get_nhif_url(setting_doc, caller):
    """Get NHIF URL
    param setting_doc: Company NHIF Settings Doc
    param caller: The caller of the function

    allowed callers: Token, GetCardDetails, AuthorizeCard
    return: NHIF URL
    """

    if caller == "Token":
        url = frappe.conf.get("nhif_portal_token_url")
        extra_params = "&client_id=serviceportal&client_secret=serviceportal&scope=MedicalService"
        
        if not url:
            extra_params = ""
            url = str(setting_doc.nhifservice_url) + "/nhifservice/Token"
        
        return url, extra_params
    
    elif caller == "GetCardDetails":
        url = frappe.conf.get("nhif_portal_carddetails_url")
        if not url:
            url = str(setting_doc.nhifservice_url) + "/nhifservice/breeze/verification/GetCardDetails?CardNo="
        return url
    
    elif caller == "AuthorizeCard":
        url = frappe.conf.get("nhif_portal_authorizecard_url")
        extra_params = "&EnforceOnlineForm=true&Narration=undefined&MethodUsed=Online&BiometricMethod=None"
        
        if not url:
            extra_params = ""
            url = str(setting_doc.nhifservice_url) + "/nhifservice/breeze/verification/AuthorizeCard?"
        
        return url, extra_params
    
    else:
        return None
    