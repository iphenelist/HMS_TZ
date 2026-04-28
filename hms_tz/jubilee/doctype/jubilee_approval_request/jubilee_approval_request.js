// Copyright (c) 2025, Aakvatech and contributors
// For license information, please see license.txt

frappe.ui.form.on("Jubilee Approval Request", {
  refresh: function (frm) {
    if (frm.doc.preauth_status === "OK") {
      frm.dashboard.set_headline(
        __(
          '<span class="indicator whitespace-nowrap green">' +
            "Pre-Authorization Submitted Successfully — Submission ID: " +
            frm.doc.submission_id +
            "</span>"
        )
      );
    } else if (frm.doc.preauth_status === "ERROR") {
      frm.dashboard.set_headline(
        __(
          '<span class="indicator whitespace-nowrap red">' +
            "Pre-Authorization Failed: " +
            frm.doc.preauth_description +
            "</span>"
        )
      );
    }

    frm.trigger("get_preauth_status");
  },

  get_preauth_status: (frm) => {
    if (
      !frm.doc.submission_id &&
      frm.doc.preauth_status &&
      frm.doc.preauth_status != "ERROR"
    ) {
      frm.add_custom_button(__("Get Pre-Auth Status"), () => {
        frappe.call({
          method: "hms_tz.jubilee.api.api.get_preauthorization_status",
          args: {
            approval_request_name: frm.doc.name,
          },
          freeze: true,
          freeze_message: __("Checking Pre-Auth Status..."),
          callback: function (r) {
            if (r.message) {
              let data = r.message;

              if (data.status != "ERROR") {
                frappe.utils.play_sound("success");
                frappe.show_alert({
                  message: __(`${data.description}`),
                });

                frm.reload_doc();
              } else {
                frappe.utils.play_sound("error");
                frappe.msgprint({
                  title: __("Pre-Authorization Error"),
                  indicator: "red",
                  message: __(`${data.description}`),
                });
              }
            }
          },
          onerror: function () {
            frappe.utils.play_sound("error");
            frappe.msgprint({
              title: __("Pre-Authorization Error"),
              indicator: "red",
              message: __(
                "An unexpected error occurred while fetching the pre-authorization status."
              ),
            });
          },
        });
      });
    }
  },
});
