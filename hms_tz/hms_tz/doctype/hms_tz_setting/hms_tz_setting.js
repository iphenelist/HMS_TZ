// Copyright (c) 2025, Aakvatech and contributors
// For license information, please see license.txt

frappe.ui.form.on('HMS TZ Setting', {
	// refresh: function(frm) {

	// }
	get_nhif_token: (frm) => {
		if (frm.is_dirty()) {
			frm.save();
		}

		if (frm.doc.enable_nhif_token === 0) {
			frappe.msgprint(__("Please Enable NHIF API to proceed.."));
			return
		}

		frm.call("get_nhif_token").then(
			frm.reload_doc(),
			frappe.show_alert({
				message: __("Token Successful fetched...!!"),
				indicator: 'green'
			})
		)
	}
});
