// Copyright (c) 2025, Aakvatech and contributors
// For license information, please see license.txt

frappe.ui.form.on('Healthcare Service Request', {
	setup: (frm) => {
		control_add_remove_btns(frm);
	},
	refresh: (frm) => {
		control_add_remove_btns(frm);
	},
	onload: (frm) => {
		control_add_remove_btns(frm);
	}
});

frappe.ui.form.on('Healthcare Service Request Item', {
	form_render: (frm, cdt, cdn) => {
		control_add_remove_btns(frm, true);
	},
});

var control_add_remove_btns = (frm, for_child=false) => {
	if (!for_child) {
		// hide button to add rows of delivery note item
		frm.get_field("services").grid.cannot_add_rows = true;

		// hide button to delete rows of delivery note item
		$("*[data-fieldname='services']").find(".grid-remove-rows").hide();
		$("*[data-fieldname='services']").find(".grid-remove-all-rows").hide();
	} else {
		frm.fields_dict.services.grid.wrapper.find('.grid-delete-row').hide();
		frm.fields_dict.services.grid.wrapper.find('.grid-insert-row-below').hide();
		frm.fields_dict.services.grid.wrapper.find('.grid-insert-row').hide();
		frm.fields_dict.services.grid.wrapper.find('.grid-duplicate-row').hide();
		frm.fields_dict.services.grid.wrapper.find('.grid-move-row').hide();
	}
}