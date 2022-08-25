// Copyright (c) 2022, Aakvatech and contributors
// For license information, please see license.txt

frappe.ui.form.on('NHIF Claim Reconciliation', {
	refresh: function(frm) {
		if (frm.doc.status == "Pending" && !frm.doc.__islocal) {
			frm.add_custom_button(__('Get Detail'), () => {
				frappe.call({
					method: "hms_tz.nhif.doctype.nhif_claim_reconciliation.nhif_claim_reconciliation.get_submitted_claims",
					args: {
						self: frm.doc
					},
					freeze: true,
					callback: function(r) {
						if (r.message) {
							frm.refresh();
						}
					}
				});
			}).addClass("btn-primary");
		}
	}
});
