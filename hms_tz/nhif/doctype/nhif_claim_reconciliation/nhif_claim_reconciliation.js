// Copyright (c) 2022, Aakvatech and contributors
// For license information, please see license.txt

frappe.ui.form.on("NHIF Claim Reconciliation", {
  refresh: function (frm) {},
  onload: (frm) => {
    if (
      frm.doc.docstatus === 1 &&
      frm.doc.total_amount_claimed === frm.doc.erp_total_amount_claimed &&
      frm.doc.number_of_submitted_claims ===
        frm.doc.erp_number_of_submitted_claims
    ) {
      frm.set_df_property("submit_monthly_claim", "hidden", 0);
    } else {
      frm.set_df_property("submit_monthly_claim", "hidden", 1);
    }
  },
  submit_monthly_claim: (frm) => {
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
