import json
import frappe
import requests
from time import sleep
from pypika.terms import ValueWrapper
from frappe.query_builder import DocType
from frappe.model.naming import make_autoname
from frappe.utils.background_jobs import enqueue
from frappe.utils import now_datetime, nowdate,flt, cint
from hms_tz.nhif.doctype.nhif_response_log.nhif_response_log import add_log
from hms_tz.nhif.doctype.nhif_custom_excluded_services.nhif_custom_excluded_services import (
    get_custom_excluded_services,
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
    frappe.msgprint("Fetch price package via backgroud job", alert=True)

    enqueue(
        method=get_nhif_cost_sharing,
        job_name="get_nhif_cost_sharing",
        queue="long",
        timeout=1800,
        is_async=True,
        company=company,
    )
    frappe.msgprint("Fetch NHIF cost sharing via backgroud job", alert=True)


@frappe.whitelist()
def process_nhif_records(company):
    facility_code = frappe.get_cached_value(
        "HMS TZ Settings", company, "facility_code"
    )
    enqueue(
        method=process_nhif_prices,
        queue="long",
        timeout=3600,
        is_async=True,
        company=company,
        facility_code=facility_code,
    )
    frappe.msgprint("Processing NHIF prices via backaground job", alert=True)

    enqueue(
        method=process_insurance_coverages,
        queue="long",
        timeout=10000000,
        is_async=True,
        company=company,
        facility_code=facility_code,
    )
    frappe.msgprint("Processing NHIF Insurance Coverage via backaground job", alert=True)


@frappe.whitelist()
def enqueue_fetch_nhif_items(company):
    enqueue(
        method=get_nhif_items,
        job_name="get_nhif_items",
        queue="default",
        timeout=1800,
        is_async=True,
        company=company,
    )
    frappe.msgprint("Fetch NHIF Items via backaground job", alert=True)


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
            response_data=json.dumps(packages),
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
        service_map = get_insurance_items(for_prices=True)

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


def process_nhif_prices(company, facility_code, item_code=None):
    currency = frappe.get_cached_value("Company", company, "default_currency")

    schemes, price_package_map = get_price_package_map(company, facility_code, for_prices=True)

    for scheme in schemes:
        price_list_name = "NHIF-" + scheme + "-" + facility_code

        if not frappe.db.exists("Price List", price_list_name):
            price_list_doc = frappe.new_doc("Price List")
            price_list_doc.price_list_name = price_list_name
            price_list_doc.currency = currency
            price_list_doc.buying = 0
            price_list_doc.selling = 1
            price_list_doc.save(ignore_permissions=True)

            # set price list to a coverage plan
            plan_name = frappe.get_cached_value(
                "Healthcare Insurance Coverage Plan", {
                    "nhif_scheme_id": scheme,
                    "company": company
                },
                "name",
            )
            if plan_name:
                frappe.db.set_value(
                    "Healthcare Insurance Coverage Plan",
                    plan_name,
                    "price_list",
                    price_list_name,
                )
                out = frappe.get_doc({
                    "doctype": "Comment",
                    "comment_type": "Comment",
                    "comment_email": frappe.session.user,
                    "comment_by": frappe.session.user,
                    "content": f"Created Price List {price_list_name} for {scheme}",
                    "reference_doctype": "Healthcare Insurance Coverage Plan",
                    "reference_name": plan_name,
                }).insert(ignore_permissions=True)

    service_map = get_insurance_items(for_prices=True)

    for itemcode, item in service_map.items():
        for i, package in price_package_map.items():
            if itemcode != i[2]:
                continue

            price_list_name = "NHIF-" + i[1] + "-" + facility_code
            if package:
                erp_item = None
                if item.get("service_type") == "Consulation Charges":
                    erp_item = item.get("service_name")
                else:
                    erp_item = frappe.get_cached_value(item.get("service_type"), item.get("service_name"), "item")
                
                if not erp_item:
                    continue

                item_price_list = frappe.db.get_all(
                    "Item Price",
                    filters={
                        "price_list": price_list_name,
                        "item_code": erp_item,
                        "currency": currency,
                        "selling": 1,
                    },
                    fields=["name", "item_code", "price_list_rate"],
                )
                if len(item_price_list) > 0:
                    for price in item_price_list:
                        if flt(price.price_list_rate) != flt(package.unitprice):
                            # delete Item Price if no package.unitprice or it is 0
                            if (
                                not flt(package.unitprice)
                                or flt(package.unitprice) == 0
                            ):
                                frappe.delete_doc("Item Price", price.name)
                                print(f"Deleted the item {item.get('service_name')}")
                            else:
                                print(f"Updated the item {item.get('service_name')}")
                                frappe.set_value(
                                    "Item Price",
                                    price.name,
                                    "price_list_rate",
                                    flt(package.unitprice),
                                )

                else:
                    print(f"Create item price for {item.get('service_name')} for {price_list_name}")
                    item_price_doc = frappe.new_doc("Item Price")
                    item_price_doc.update(
                        {
                            "item_code": erp_item,
                            "price_list": price_list_name,
                            "currency": currency,
                            "price_list_rate": flt(package.unitprice),
                            "buying": 0,
                            "selling": 1,
                        }
                    )
                    item_price_doc.save(ignore_permissions=True)
        frappe.db.commit()


def process_insurance_coverages(company, facility_code, coverage_plan=None):
    print(f"Gettign Insurance Coverage Items")
    hsic_data = []
    plans_for_deletion = []
    fields = [
        "name",
        "creation",
        "owner",
        "modified",
        "modified_by",
        "healthcare_service",
        "healthcare_service_template",
        "is_active",
        "healthcare_insurance_coverage_plan",
        "company",
        "has_copayment",
        "approval_mandatory_for_claim",
        "dosage",
        "strength",
        "maximum_quantity",
        "maximum_quantity_outpatient",
        "maximum_quantity_inpatient",
        "is_auto_generated",
        "start_date",
        "end_date",
    ]
    service_map = get_insurance_items()
    price_package_map = get_price_package_map(company, facility_code)

    filters = {
        "insurance_company": ["like", "NHIF%"],
        "is_active": 1,
        "company": company,
    }
    if coverage_plan:
        filters["name"] = {coverage_plan}
    
    coverage_plan_list = frappe.db.get_all(
        "Healthcare Insurance Coverage Plan",
        fields=["name", "nhif_scheme_id"],
        filters=filters,
    )

    for plan in coverage_plan_list:
        print(f"Processing Insurance Coverage {plan}")
        has_data = False
        for package in price_package_map.values():
            if plan.nhif_scheme_id != package.schemeid:
                continue
            
            print(f"Processing Item {package.get('itemname')} for {plan}")

            user_excluded_scheme = get_custom_excluded_services(company, package.get("itemcode"))
            
            # check if the scheme id is in the excluded products
            # scheme ids must listed on custom excluded services separated by comma
            if (
                user_excluded_scheme
                and plan.nhif_scheme_id
                and plan.nhif_scheme_id in user_excluded_scheme
            ):
                continue
            
            if not service_map.get(package.get("itemcode")):
                continue

            hsic_name = make_autoname(key='hash')

            row = (
                    hsic_name,
                    now_datetime(),
                    frappe.session.user,
                    now_datetime(),
                    frappe.session.user,
                    service_map.get(package.get("itemcode")).get("service_type"),
                    service_map.get(package.get("itemcode")).get("service_name"),
                    1,
                    plan.name,
                    company,
                    cint(package.get("hascopayment")),
                    cint(package.get("isrestricted")),
                    package.get("dosage"),
                    package.get("strength"),
                    package.get("maximumquantity"),
                    package.get("maximumquantityoutpatient"),
                    package.get("maximumquantityinpatient"),
                    1,
                    nowdate(),
                    "2099-12-31",
                )
            
            if not has_data and row:
                has_data = True
            
            hsic_data.append(row)

        if has_data:
            plans_for_deletion.append(plan.name)
    
    delete_hsic_data(plans_for_deletion)

    sleep(30)
    frappe.db.bulk_insert(
        "Healthcare Service Insurance Coverage",
        fields=fields,
        values=hsic_data,
        ignore_duplicates=True
    )
    frappe.db.commit()
    return True


def delete_hsic_data(coverage_plans):
    if len(coverage_plans) == 0:
        return
    
    hsic = DocType("Healthcare Service Insurance Coverage")
    frappe.qb.from_(hsic).delete().where(
        hsic.healthcare_insurance_coverage_plan.isin(coverage_plans)
    ).run()


def get_price_package_map(company, facility_code, for_prices=False):
    npp = DocType("NHIF Price Package")
    price_packages = (
        frappe.qb.from_(npp)
        .select(
            npp.facilitycode,
            npp.itemcode,
            npp.itemname,
            npp.schemeid,
            npp.packageid,
            npp.pricecode,
            npp.unitprice,
            npp.isrestricted,
            npp.hascopayment,
            npp.strength,
            npp.dosage,
            npp.maximumquantity,
            npp.maximumquantityoutpatient,
            npp.maximumquantityinpatient,
        )
        .where(npp.company == company)
        .where(npp.facilitycode == facility_code)
    ).run(as_dict=True)

    schemes = []

    price_package_map = {}
    for price_package in price_packages:
        if price_package["schemeid"] not in schemes:
            schemes.append(price_package["schemeid"])

        price_package_map[price_package["facilitycode"], price_package["schemeid"], price_package["itemcode"]] = price_package
    
    if for_prices:
        return schemes, price_package_map

    return price_package_map


def get_insurance_items(for_prices=False):
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

    if for_prices:
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


def get_nhif_cost_sharing(company):
    settings_doc = frappe.get_cached_doc("HMS TZ Settings", company)
    token = settings_doc.get_nhif_token()

    url = f"{settings_doc.nhif_claim_url}/api/Packages/GetCostSharingSchedule"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    r = requests.request("Get", url, headers=headers, timeout=60)
    if r.status_code != 200:
        add_log(
            request_type="GetCostSharingSchedule",
            request_url=url,
            request_header=headers,
            request_body="",
            response_data=r.text,
            status_code=r.status_code,
            company=settings_doc.name,
            ref_doctype="NHIF Cost Sharing",
        )
        frappe.throw(json.loads(r.text))
    else:
        data = json.loads(r.text)
        log_name = add_log(
            request_type="GetCostSharingSchedule",
            request_url=url,
            request_header=headers,
            request_body="",
            response_data=json.dumps(data),
            status_code=r.status_code,
            company=settings_doc.name,
            ref_doctype="NHIF Cost Sharing",
        )

        sync_cost_sharing(data)


def sync_cost_sharing(data):
    if len(data) == 0:
        return
    
    ncs = DocType("NHIF Cost Sharing")
    frappe.qb.from_(ncs).delete().run()

    sleep(30)
    values = []
    fields = [
        "name",
        "owner",
        "creation",
        "modified",
        "modified_by",
        "service_type",
        "service_name",
        "itemcode",
        "scheduleitemid",
        "yearno",
        "productcode",
        "packageid",
        "percentcovered"
    ]

    service_map = get_insurance_items(for_prices=True)

    for row in data:
        ncs_name = make_autoname(key='hash')
        service_type = ""
        service_name = ""
        if service_map.get(row.get("ItemCode")):
            service_type = service_map.get(row.get("ItemCode")).get("service_type")
            service_name = service_map.get(row.get("ItemCode")).get("service_name")

        values.append(
            (
                ncs_name,
                now_datetime(),
                frappe.session.user,
                now_datetime(),
                frappe.session.user,
                service_type,
                service_name,
                row.get("ItemCode"),
                row.get("ScheduleItemID"),
                row.get("YearNo"),
                row.get("ProductCode"),
                row.get("PackageID"),
                row.get("PercentCovered")
            )
        )
    
    frappe.db.bulk_insert(
        "NHIF Cost Sharing",
        fields=fields,
        values=values,
        ignore_duplicates=True
    )
    frappe.db.commit()
    return True


@frappe.whitelist()
def  get_nhif_schemes(company=None, caller=None):
    if not company:
        settings = frappe.db.get_all("HMS TZ Settings", filters={"enable_nhif_api": 1}, fields=["company"])
        company = settings[0].company
    
    if not company:
        return
    
    settings_doc = frappe.get_cached_doc("HMS TZ Settings", company)

    token = settings_doc.get_nhif_token()

    url = f"{settings_doc.nhif_claim_url}/api/Packages/GetBenefitSchemes"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    r = requests.request("Get", url, headers=headers, timeout=60)
    if r.status_code != 200:
        add_log(
            request_type="GetBenefitSchemes",
            request_url=url,
            request_header=headers,
            request_body="",
            response_data=r.text,
            status_code=r.status_code,
            company=settings_doc.name,
            ref_doctype="NHIF Scheme",
        )

    else:
        data = json.loads(r.text)
        add_log(
            request_type="GetBenefitSchemes",
            request_url=url,
            request_header=headers,
            request_body="",
            response_data=data,
            status_code=r.status_code,
            company=settings_doc.name,
            ref_doctype="NHIF Scheme",
        )

        if len(data) == 0:
            return
        
        for row in data:
            scheme_id = frappe.get_cached_value("NHIF Scheme", {"scheme_id": row["SchemeID"]}, "name")
            if scheme_id:
                has_changed = False
                doc = frappe.get_cached_doc("NHIF Scheme", scheme_id)

                if doc.scheme_name != row["SchemeName"]:
                    doc.scheme_name = row["SchemeName"]
                    has_changed = True
                
                if has_changed:
                    doc.save(ignore_permissions=True)
                
            else:
                doc = frappe.new_doc("NHIF Scheme")
                doc.scheme_id = row["SchemeID"]
                doc.scheme_name = row["SchemeName"]

                doc.save(ignore_permissions=True)
        
        if company and caller=='Front End':
            frappe.msgprint("successfully fetched NHIF Schemes", alert=True, indicator="green")


@frappe.whitelist()
def  get_nhif_products(company=None, caller=None):
    companies = []

    if company:
        companies = [company]
    
    if len(companies) == 0:
        companies = frappe.db.get_all(
            "HMS TZ Settings",
            filters={"enable_nhif_api": 1},
            fields=["company"],
            pluck="company"
        )
    
    if len(companies) == 0:
        return
    
    product_dict =  {
        "status": False
    }
    for company in companies:
        get_nhif_product_per_company(company, product_dict)
    
    if (
        company and
        caller == 'Front End' and 
        product_dict["status"]
    ):
        frappe.msgprint("successfully fetched NHIF Products", alert=True, indicator="green")


def get_nhif_product_per_company(company, product_dict):
    settings_doc = frappe.get_cached_doc("HMS TZ Settings", company)
    token = settings_doc.get_nhif_token()

    url = f"{settings_doc.nhif_claim_url}/api/Packages/GetProducts"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    r = requests.request("Get", url, headers=headers, timeout=60)
    if r.status_code != 200:
        add_log(
            request_type="GetProducts",
            request_url=url,
            request_header=headers,
            request_body="",
            response_data=r.text,
            status_code=r.status_code,
            company=settings_doc.name,
            ref_doctype="NHIF Product",
        )

    else:
        data = json.loads(r.text)
        add_log(
            request_type="GetProducts",
            request_url=url,
            request_header=headers,
            request_body="",
            response_data=data,
            status_code=r.status_code,
            company=settings_doc.name,
            ref_doctype="NHIF Product",
        )

        if len(data) == 0:
            return
        
        abbr = frappe.get_cached_value("Company", company, "abbr")

        for row in data:
            try:
                add_nhif_product(row, company, abbr)
                
                if not product_dict["status"]:
                    product_dict["status"] = True
                
            except Exception as e:
                frappe.log_error(
                    title='NHIF Product Creation Error',
                    message=frappe.get_traceback()
                )


def add_nhif_product(row, company, abbr):
    product_id = str(row["ProductCode"]) + "-" + str(abbr)

    nhif_product_pr_key = frappe.get_cached_value("NHIF Product", {"company": company, "nhif_product_code": row["ProductCode"]}, "name")
    if not nhif_product_pr_key:
        nhif_product_pr_key = frappe.get_cached_value("NHIF Product", {"company": "", "nhif_product_code": row["ProductCode"]})

    if nhif_product_pr_key:
        if (
            row["ProductName"] and
            row["ProductName"] != "null"
        ):
            has_changed = False
            doc = frappe.get_cached_doc("NHIF Product", nhif_product_pr_key)

            if doc.product_id != product_id:
                doc.product_id = product_id
                has_changed = True
            
            if doc.product_name != row["ProductName"]:
                doc.product_name = row["ProductName"]
                has_changed = True
            
            if doc.schemeid != row["SchemeID"]:
                doc.schemeid = row["SchemeID"]
                has_changed = True
            
            if doc.productdescription != row["ProductDescription"]:
                doc.productdescription = row["ProductDescription"]
                has_changed = True
            
            if doc.highestorderwithoutreferral != row["HighestOrderWithoutReferral"]:
                doc.highestorderwithoutreferral = row["HighestOrderWithoutReferral"]
                has_changed = True
            
            if doc.maximumadmissiondays != row["MaximumAdmissionDays"]:
                doc.maximumadmissiondays = row["MaximumAdmissionDays"]
                has_changed = True
            
            if doc.requiresnationalid != row["RequiresNationalID"]:
                doc.requiresnationalid = row["RequiresNationalID"]
                has_changed = True

            if doc.usespolicy != row["UsesPolicy"]:
                doc.usespolicy = row["UsesPolicy"]
                has_changed = True

            doc.company = company

            plan = frappe.db.get_all(
                "Healthcare Insurance Coverage Plan", 
                filters={"nhif_scheme_id": row["SchemeID"], "company": company}
            )
            if len(plan) == 1:
                if doc.healthcare_insurance_coverage_plan != plan[0].name:
                    has_changed = True
                    doc.healthcare_insurance_coverage_plan = plan[0].name
            else:
                has_changed = True
                doc.healthcare_insurance_coverage_plan = ""
                doc.add_comment(
                    "Comment",
                    f"Failed to find matching plan for SchemeId: {row['SchemeID']}"
                )

            if has_changed:
                doc.save(ignore_permissions=True)
    else:
        doc = frappe.new_doc('NHIF Product')
        doc.product_id = product_id
        doc.company = company

        doc.nhif_product_code = row["ProductCode"]
        if row["ProductName"] and row["ProductName"] != "null":
            doc.product_name = row["ProductName"]
        
        doc.schemeid = row["SchemeID"]
        doc.productdescription = row["ProductDescription"]
        doc.highestorderwithoutreferral = row["HighestOrderWithoutReferral"]
        doc.maximumadmissiondays = row["MaximumAdmissionDays"]
        doc.requiresnationalid = row["RequiresNationalID"]
        doc.usespolicy = row["UsesPolicy"]
        plan = frappe.db.get_all(
            "Healthcare Insurance Coverage Plan", 
            filters={"nhif_scheme_id": row["SchemeID"], "company": company}
        )
        if len(plan) == 1:
            doc.healthcare_insurance_coverage_plan = plan[0].name
        else:
            doc.healthcare_insurance_coverage_plan = ""
        
        doc.save(ignore_permissions=True)


@frappe.whitelist()
def  get_item_types(company=None, caller=None):
    if not company:
        settings = frappe.db.get_all("HMS TZ Settings", filters={"enable_nhif_api": 1}, fields=["company"])
        company = settings[0].company
    
    if not company:
        return
    
    settings_doc = frappe.get_cached_doc("HMS TZ Settings", company)

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
            item_type = frappe.get_cached_value("NHIF Item Type", {"item_type_id": item["ItemTypeID"]}, "name")
            if item_type:
                has_changed = False
                doc = frappe.get_cached_doc("NHIF Item Type", item_type)

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

        if company and caller=='Front End':
            frappe.msgprint("successfully fetched Item Types", alert=True, indicator="green")

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


def  get_nhif_items(company=None):
    if not company:
        settings = frappe.db.get_all("HMS TZ Settings", filters={"enable_nhif_api": 1}, fields=["company"])
        company = settings[0].company
    
    if not company:
        return
    
    settings_doc = frappe.get_cached_doc("HMS TZ Settings", company)

    token = settings_doc.get_nhif_token()

    url = f"{settings_doc.nhif_claim_url}/api/Packages/GetItems"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    r = requests.request("Get", url, headers=headers, timeout=60)
    if r.status_code != 200:
        add_log(
            request_type="GetItems",
            request_url=url,
            request_header=headers,
            request_body="",
            response_data=r.text,
            status_code=r.status_code,
            company=settings_doc.name,
            ref_doctype="NHIF Item",
        )

    else:
        data = json.loads(r.text)
        add_log(
            request_type="GetItems",
            request_url=url,
            request_header=headers,
            request_body="",
            response_data=data,
            status_code=r.status_code,
            company=settings_doc.name,
            ref_doctype="NHIF Item",
        )

        if len(data) == 0:
            return
        
        ni = DocType("NHIF Item")
        frappe.qb.from_(ni).delete().run()

        sleep(30)

        values = []
        fields = [
            "name",
            "creation",
            "owner",
            "modified",
            "modified_by",
            "itemcode",
            "itemtypeid",
            "itemname",
            "subgroup",
            "strength",
            "dosage",
            "isactive",
            "isrestricted",
            "calculatedperday",
            "servicetypeid",
            "serviceinterval",
            "typeofinterval",
            "waitingperiod",
            "typeofperiod",
            "eligibility",
            "commonprice",
            "percentcovered",
            "availableinlevels",
            "practitionerqualifications",
        ]


        for row in data:
            ni_name = make_autoname(key='hash')

            values.append(
                (
                    ni_name,
                    now_datetime(),
                    frappe.session.user,
                    now_datetime(),
                    frappe.session.user,
                    row.get("ItemCode"),
                    row.get("ItemTypeID"),
                    row.get("ItemName"),
                    row.get("SubGroup"),
                    row.get("Strength"),
                    row.get("Dosage"),
                    row.get("IsActive"),
                    row.get("IsRestricted"),
                    row.get("CalculatedPerDay"),
                    row.get("ServiceTypeID"),
                    row.get("ServiceInterval"),
                    row.get("TypeOfInterval"),
                    row.get("WaitingPeriod"),
                    row.get("TypeOfPeriod"),
                    row.get("Eligibility"),
                    row.get("CommonPrice"),
                    row.get("PercentCovered"),
                    row.get("AvailableInLevels"),
                    row.get("PractitionerQualifications"),
                )
            )

        frappe.db.bulk_insert(
            "NHIF Item",
            fields=fields,
            values=values,
            ignore_duplicates=True
        )
        frappe.db.commit()
        return True
