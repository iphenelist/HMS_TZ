// Copyright (c) 2022, Aakvatech and contributors
// For license information, please see license.txt

frappe.ui.form.on("NHIF Claim Reconciliation", {
  refresh: (frm) => {
    frm.trigger("toggle_monthly_claim_button");
  },
  onload: (frm) => {
    frm.trigger("toggle_monthly_claim_button");
  },

  toggle_monthly_claim_button: (frm) => {
    const can_submit =
      frm.doc.docstatus === 1 &&
      frm.doc.total_amount_claimed === frm.doc.erp_total_amount_claimed &&
      frm.doc.number_of_submitted_claims === frm.doc.erp_number_of_submitted_claims;

    frm.set_df_property("submit_monthly_claim", "hidden", can_submit ? 0 : 1);
  },

  submit_monthly_claim: (frm) => {
    frm.trigger("open_submit_monthly_claim_dialog");
  },

  open_submit_monthly_claim_dialog: (frm) => {
    const dialog = new frappe.ui.Dialog({
      title: __("Submit Monthly Claim"),
      fields: [
        {
          fieldtype: "Small Text",
          fieldname: "submission_remarks",
          label: __("Submission Remarks"),
          reqd: 0,
        },
      ],
      primary_action_label: __("Send"),
      primary_action: (values) => {
        dialog.hide();
        frappe.call({
          method:
            "hms_tz.nhif.doctype.nhif_monthly_claim.nhif_monthly_claim.submit_monthly_claim_via_api",
          args: {
            data: {
              company: frm.doc.company,
              claim_month: frm.doc.claim_month,
              claim_year: frm.doc.claim_year,
              folio_submitted: frm.doc.erp_number_of_submitted_claims,
              total_amount_claimed: frm.doc.erp_total_amount_claimed,
              submission_remarks: values?.submission_remarks,
            },
          },
          freeze: true,
          freeze_message: __("Submitting Monthly Claims"),
          callback: function (r) {
            if (r.message) {
              frappe.show_alert({
                message: __("Monthly Claims submitted successfully"),
                indicator: "green",
              });
            }
          },
        });
      },
    });

    dialog.show();
  },
});
