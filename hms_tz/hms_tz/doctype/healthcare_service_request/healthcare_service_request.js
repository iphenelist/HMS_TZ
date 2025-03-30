// Copyright (c) 2025, Aakvatech and contributors
// For license information, please see license.txt

frappe.ui.form.on('Healthcare Service Request', {
	setup: (frm) => {
		set_filters(frm);
		frm.trigger('get_services');
		control_add_remove_btns(frm);
	},
	refresh: (frm) => {
		set_filters(frm);
		frm.trigger('get_services');
		control_add_remove_btns(frm);
	},
	onload: (frm) => {
		set_filters(frm);
		frm.trigger('get_services');
		control_add_remove_btns(frm);

		frm.get_service_rate = (row) => {
			frm.call('get_service_rate', {row})
				.then(r => {
					if (r.message) {
						frappe.model.set_value(row.doctype, row.name, "rate", r.message.item_rate);
						if (r.message.discount_percent > 0) {
							frappe.model.set_value(row.doctype, row.name, "discount_applied", 1);
						}
						let amount = (row.percent_covered / 100 * r.message.item_rate) * row.qty;
						frappe.model.set_value(row.doctype, row.name, "amount", amount);
						frm.refresh_field("payments");
					}
				});
		}

		frm.get_plan_name = (row) => {
			let insurance_subscription = row.insurance_subscription;
			frm.call('get_coverage_plan', {insurance_subscription})
				.then(r => {
					if (r.message) {
						frappe.model.set_value(row.doctype, row.name, "payor_plan", r.message);
						frm.refresh_field("payments");
					}
				});
		};
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
								docfield.options = r.message;
							}
						});
					});

					frm.refresh_field("payments");
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
	service_name: (frm, cdt, cdn) => {
		let row = locals[cdt][cdn];
		if (row.service_name && row.price_list) {
			frm.get_service_rate(row);
		}
	},
	price_list: (frm, cdt, cdn) => {
		let row = locals[cdt][cdn];
		if (row.price_list && row.service_name) {
			frm.get_service_rate(row);
		}
	},
	percent_covered: (frm, cdt, cdn) => {
		let row = locals[cdt][cdn];
		if (row.percent_covered > 100) {
			frappe.msgprint(__("Percent Covered cannot be more than 100"));
			frappe.model.set_value(cdt, cdn, "percent_covered", 0);
			frm.refresh_field("payments");
			return;
		} else if (row.percent_covered < 0) {
			frappe.msgprint(__("Percent Covered cannot be less than 0"));
			frappe.model.set_value(cdt, cdn, "percent_covered", 0);
			frm.refresh_field("payments");
			return;
		} else {
			let amount = (row.percent_covered / 100 * row.rate) * row.qty;
			frappe.model.set_value(cdt, cdn, "amount", amount);
			frm.refresh_field("payments");
		}
	},
	qty: (frm, cdt, cdn) => {
		let row = locals[cdt][cdn];
		let amount = (row.percent_covered / 100 * row.rate) * row.qty;
		frappe.model.set_value(cdt, cdn, "amount", amount);
		frm.refresh_field("payments");
	},
	insurance_subscription: (frm, cdt, cdn) => {
		let row = locals[cdt][cdn];
		if (row.insurance_subscription) {
			frm.get_plan_name(row);
		} else {
			frappe.model.set_value(cdt, cdn, "payor_plan", 'Cash');
			frm.refresh_field("payments");
		}
	}
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

var set_filters = (frm) => {
	frm.set_query("insurance_subscription", "payments", () => {
		return {
			filters: {
				'is_active': 1,
				'patient': frm.doc.patient,
				'name': ['!=', frm.doc.insurance_subscription]
			}
		}
	});

	frm.set_query("price_list", "payments", () => {
		return {
			filters: {
				'enabled': 1,
				'selling': 1
			}
		}
	});
};