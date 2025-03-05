// Copyright (c) 2025, Aakvatech and contributors
// For license information, please see license.txt

frappe.ui.form.on('Healthcare Service Request', {
	setup: (frm) => {
		frm.trigger('get_services');
		control_add_remove_btns(frm);
	},
	refresh: (frm) => {
		frm.trigger('get_services');
		control_add_remove_btns(frm);
	},
	onload: (frm) => {
		frm.trigger('get_services');
		control_add_remove_btns(frm);
	},
	get_services: (frm) => {
		frm.call('get_services', {})
			.then(r => {
				if (r.message && r.message.length > 0) {

					const grid = frm.fields_dict.payments.grid;

					grid.visible_columns = undefined;
                	grid.setup_visible_columns();

					grid.fields_map.service_name.options = r.message;
					grid.refresh();

					frm.fields_dict.payments.grid.grid_rows.forEach(row => {
						row.docfields.forEach(docfield => {
							if (docfield.fieldname === 'service_name') {
								docfield.options = options;
							}
						});
					});

					frm.refresh_field(payments);
					grid.refresh();
					grid.setup_visible_columns();

					// frm.fields_dict.payments.grid.fields_map.service_name.options = r.message;
                    // frm.refresh_field("payments");
				}
			})

	}
});

frappe.ui.form.on('Healthcare Service Request Item', {
	form_render: (frm, cdt, cdn) => {
		control_add_remove_btns(frm, true);
	},
});

frappe.ui.form.on('Healthcare Service Request Payment', {
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