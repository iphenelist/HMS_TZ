/*
(c) ESS 2015-16
*/
frappe.listview_settings['Patient Encounter'] = {
	filters: [["docstatus", "!=", "2"], ["duplicated", "==", "0"]],

	onload: function (listview) {
		listview.page.fields_dict['admission_service_unit_type'].get_query = function () {
			return {
				filters: {
					inpatient_occupancy: 1
				}
			};
		};
		practitioner_login_out_to_from_nhif(listview);

	}
};


var practitioner_login_out_to_from_nhif = (listview) => {
    if (!frappe.user.has_role("Healthcare Practitioner")) {
        return;
    }

    frappe.call({
        method: 'hms_tz.nhif.api.healthcare_practitioner.get_nhif_loggedin_practitioner_info',
        args: {},
        callback: (r) => {
            if (!r.message) {
                return;
            }

			if (listview.page.custom_actions.find('.nhif-buttons').length > 0) {
				return;
			}

            let $container = $(`
                <div class="nhif-buttons" style="margin-right: 10px;">
                    <button class="btn btn-sm btn-primary nhif-login-btn" style="${r.message ? '' : 'display: none;'}">
                        ${__("Login To NHIF")}
                    </button>
                    <button class="btn btn-sm btn-primary nhif-logout-btn" style="${r.message ? 'display: none;' : ''}">
                        ${__("Logout From NHIF")}
                    </button>
                </div>
            `);

            listview.page.custom_actions.prepend($container);

            // Bind the Login click event
            $container.find(".nhif-login-btn").on("click", async function () {
                let fingerprint = await new dpFingerprint({ label: 'Login To NHIF' });
                if (!fingerprint) {
                    frappe.msgprint(__('Fingerprint capture failed. Please try again.'));
                    return;
                }
                frappe.call({
                    method: 'hms_tz.nhif.nhif_api.attendance.login_practitioner',
                    args: {
                        'fingerprint': fingerprint.Data,
                        'fpcode': fingerprint.fpCode,
                    },
                    async: true,
                    freeze: true,
                    freeze_message: __('<i class="fa fa-spinner fa-spin fa-4x"></i>'),
                    callback: function (data) {
                        if (data.message && data.message !== 'Error') {
                            frappe.utils.play_sound("submit");

                            $container.find(".nhif-login-btn").hide();
                            $container.find(".nhif-logout-btn").show();
                        } else {
                            frappe.utils.play_sound("error");
                        }
                    },
                    onerror: function (data) {
                        frappe.utils.play_sound("error");
                    }
                });
            });

            // Bind the logout click event
            $container.find(".nhif-logout-btn").on("click", function () {
                frappe.call({
                    method: 'hms_tz.nhif.nhif_api.attendance.logout_practitioner',
                    args: {},
                    async: true,
                    freeze: true,
                    freeze_message: __('<i class="fa fa-spinner fa-spin fa-4x"></i>'),
                    callback: function (data) {
                        if (data.message && data.message !== 'Error') {
                            frappe.utils.play_sound("submit");

                            $container.find(".nhif-login-btn").show();
                            $container.find(".nhif-logout-btn").hide();
                        } else {
                            frappe.utils.play_sound("error");
                        }
                    },
                    onerror: function (data) {
                        frappe.utils.play_sound("error");
                    }
                });
            });
        }
    });
}
