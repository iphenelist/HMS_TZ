frappe.ui.form.on('Healthcare Insurance Subscription', {
    setup: function (frm) {
        frm.set_query('healthcare_insurance_coverage_plan', function () {
            return {
                filters: {
                    'insurance_company': frm.doc.insurance_company,
                    'is_active': 1
                }
            };
        });
    },
    coverage_plan_card_number: function (frm) {
        frm.fields_dict.coverage_plan_card_number.$input.focusout(function () {
            frm.trigger("get_patient_name");
            if (!frm.doc.insurance_company.includes("NHIF")) {
                if (!frm.doc.coverage_plan_card_number) return

                setTimeout(() => {
                    frappe.show_alert({
                        message: __('<b>Healthcare Insurance Subscription is submitted</b>'),
                        'indicator': 'success'
                    });
                    frm.save("Submit")
                }, 10000);
            }
        });
    },
    insurance_company: function (frm) {
        frm.trigger("get_patient_name");
        frm.set_value("daily_limit", 0);
    },
    get_patient_name: function (frm) {
        if (!frm.doc.insurance_company.includes("NHIF")) return
        if (!frm.doc.coverage_plan_card_number && !frm.doc.national_id) return

        let args = {
            'patient': frm.doc.patient,
            'patient_name': frm.doc.patient_name
        }

        if (frm.doc.coverage_plan_card_number) {
            args.card_no = frm.doc.coverage_plan_card_number
        } else if (frm.doc.national_id) {
            args.national_id = frm.doc.national_id
        }

        args.ref_doctype = frm.doc.doctype;

        if (!frm.is_new()) {
            args.ref_docname = frm.doc.name;
        }

        frappe.show_alert({
            message: __("Getting patient's information from NHIF"),
            indicator: 'green'
        }, 5);

        frappe.call({
            method: "hms_tz.nhif.api.insurance_subscription.check_patient_info",
            args: args,
            freeze: true,
            freeze_message: __('<i class="fa fa-spinner fa-spin fa-4x"></i>'),
        }).then(data => {
            frappe.utils.play_sound("submit");

            if (data.message) {
                if (data.message != frm.doc.patient_name){
                    frm.set_value("patient_name", data.message);
                    frm.save("Submit")
                }
            } else {
                frappe.utils.play_sound("error");
                frappe.show_alert({
                    message: __("Failed to get patient's information"),
                    indicator: 'red'
                }, 10);
            }
        }).on_error(err => {
            frappe.utils.play_sound("error");
            frappe.show_alert({
                message: __("Failed to get patient's information"),
                indicator: 'red'
            }, 10);
        });
    },
});