frappe.ui.form.on("Radiology Examination", {
    refresh: (frm) => {
        $('[data-label="Not%20Serviced"]').parent().hide();

        // Add Request Approval button for NHIF patients with restricted services
        if (frm.doc.insurance_company && frm.doc.insurance_company.includes("NHIF") &&
            frm.doc.docstatus === 0 && frm.doc.is_restricted && !frm.doc.approval_number) {
            frm.add_custom_button(__('Request Approval'), function() {
                frm.events.request_approval(frm);
            }).addClass("btn-primary");
        }
    },
    onload: (frm) => {
        $('[data-label="Not%20Serviced"]').parent().hide();
        if (frm.doc.patient) {
            frm.add_custom_button(__('Patient History'), function () {
                frappe.route_options = { 'patient': frm.doc.patient };
                frappe.set_route('tz-patient-history');
            });
        }
    },

    request_approval: (frm) => {
        if (!frm.doc.insurance_company || !frm.doc.insurance_company.includes("NHIF")) {
            frappe.show_alert({
                message: __("This feature is only applicable for NHIF insurance"),
                indicator: 'orange'
            }, 5);
            return;
        }

        if (!frm.doc.insurance_subscription) {
            frappe.msgprint("Insurance Subscription is required to request approval");
            return;
        }

        if (frm.is_dirty()) {
            frappe.msgprint("Please save the document before requesting approval");
            return;
        }

        frappe.call({
            method: "hms_tz.nhif.nhif_api.approval.get_service_approval",
            args: {
                ref_doctype: frm.doctype,
                ref_docname: frm.docname,
                service_type: "Radiology Examination Template",
                service_name: frm.doc.radiology_examination_template,
                qty: 1
            },
            freeze: true,
            freeze_message: __('<i class="fa fa-spinner fa-spin fa-4x"></i>'),
            callback: function(r) {
                if (r.message) {
                    frm.refresh();
                    if (r.message.status == "success") {
                        frappe.show_alert({
                            message: __("<h4 class='text-center' style='background-color: #D3D3D3; font-weight: bold;'>\
                                Approval Request Successful. Reference Number: " + r.message.reference_no + "</h4>"),
                            indicator: "green"
                        }, 15);
                        frappe.utils.play_sound("submit");
                    } else {
                        frappe.show_alert({
                            message: __("<h4 class='text-center' style='background-color: #D3D3D3; font-weight: bold;'>\
                                Approval Request Failed: "  + "</h4>"),
                            indicator: "red"
                        }, 20);
                        frappe.utils.play_sound("error");
                    }
                } else {
                    frappe.utils.play_sound("error");
                }
            }
        });
    },
    approval_number: (frm) => {
        frm.fields_dict.approval_number.$input.focusout(() => {
            if (frm.doc.approval_number != "" && frm.doc.approval_number != undefined) {
                if (!frm.doc.insurance_company.includes("NHIF")) {
                    return;
                }
                frappe.call({
                    method: "hms_tz.nhif.api.healthcare_utils.verify_service_approval_number_for_LRPMT",
                    args: {
                        company: frm.doc.company,
                        approval_number: frm.doc.approval_number,
                        template_doctype: "Radiology Examination Template",
                        template_name: frm.doc.radiology_examination_template,
                        appoiintment: frm.doc.appointment,
                        encounter: frm.doc.ref_docname
                    },
                    freeze: true,
                    freeze_message: __('<i class="fa fa-spinner fa-spin fa-4x"></i>'),

                }).then(r => {
                    if (r.message && r.message == "approval number validation is disabled") {
                        return
                    }
                    else if (r.message) {
                        frappe.show_alert({
                            message: __("<h4 class='text-center' style='background-color: #D3D3D3; font-weight: bold;'>\
                                Approval Number is Valid</h4>"),
                            indicator: "green"
                        }, 20);

                    } else {
                        frm.set_value("approval_number", "");
                        frappe.show_alert({
                            message: __("<h4 class='text-center' style='background-color: #D3D3D3; font-weight: bold;'>\
                                Approval Number is not Valid</h4>"),
                            indicator: "Red"
                        }, 20);
                    }
                });
            }
        });
    }
})