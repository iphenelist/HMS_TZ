// Copyright (c) 2021, Aakvatech and contributors
// For license information, please see license.txt

frappe.ui.form.on('LRPMT Returns', {
	setup: function (frm) {
		var requested_by = frappe.user.full_name();
		frm.set_value("requested_by", requested_by);
	},

	after_save: function (frm) {
		frm.reload_doc();
	},

	refresh: function (frm) {
		frm.get_field("lrpt_items").grid.cannot_add_rows = true;
		frm.get_field("therapy_items").grid.cannot_add_rows = true;
		frm.get_field("drug_items").grid.cannot_add_rows = true;
		frm.get_field("sales_items").grid.cannot_add_rows = true;

		frm.set_query('appointment', () => {
			return {
				filters: {
					'patient': frm.doc.patient
				}
			}
		});

		if (frm.doc.patient && frm.doc.appointment) {
			frm.add_custom_button(__("Get LRP Items"), function () {
				frm.trigger("get_lrp_items");
			})

			frm.add_custom_button(__("Get Therapy Items"), function () {
				frm.trigger("get_therapy_items");
			})

			frm.add_custom_button(__("Get Drug Items"), function () {
				frm.trigger("get_drug_items");
			})
		}
	},

	onload: function (frm) {
		frm.get_field("lrpt_items").grid.cannot_add_rows = true;
		frm.get_field("therapy_items").grid.cannot_add_rows = true;
		frm.get_field("drug_items").grid.cannot_add_rows = true;
		frm.get_field("sales_items").grid.cannot_add_rows = true;

		frm.validate_quantity_to_return = function (frm, row) {
			frm.doc.drug_items.forEach(data => {
				if (data.quantity_to_return > (data.quantity_prescribed - data.qty_returned)) {
					row.quantity_to_return = 0;
					frappe.msgprint({
						title: __('Message'),
						indicator: 'yellow',
						message: __(
							'<h4 class="text-center" style="background-color: yellow; font-weight: bold;">\
							Quantity to Return can not be greater than Quantity Prescribed<h4>'
						)
					});
					frm.refresh_field("drug_items")
				}
			})
		}
		frm.validate_no_of_sessions_to_cancel = function (frm, row) {
			frm.doc.therapy_items.forEach(data => {
				if (data.sessions_to_cancel > (data.sessions_prescribed - data.sessions_cancelled)) {
					row.sessions_to_cancel = 0;
					frappe.msgprint({
						title: __('Message'),
						indicator: 'yellow',
						message: __(
							'<h4 class="text-center" style="background-color: yellow; font-weight: bold;">\
							No of Sessions to Cancel can not be greater than No of Sessions Prescribed<h4>'
						)
					});
					frm.refresh_field("therapy_items")
				}
			})
		}
	},

	before_submit: function (frm) {
		frm.set_value("approved_by", frappe.user.full_name())
	},

	get_lrp_items: function (frm) {
		let d = new frappe.ui.Dialog({
			title: "Select LRP Items",
			fields: [
				{
					fieldname: "result_area",
					fieldtype: "HTML"
				}
			]
		});
		var $wrapper;
		var $results;
		var $placeholder;
		if (frm.doc.patient && frm.doc.appointment && frm.doc.company) {
			var columns = (["item_name", "encounter_no", "reference_docname", "reference_doctype", "status"])

			frappe.call({
				method: "hms_tz.hms_tz.doctype.lrpmt_returns.lrpmt_returns.get_lrp_item_list",
				args: {
					patient: frm.doc.patient,
					appointment: frm.doc.appointment,
					company: frm.doc.company
				},
				freeze: true,
				freeze_message: __('<i class="fa fa-spinner fa-spin fa-4x"></i>'),
				callback: (data) => {
					if (data.message.length > 0) {
						$results.append(make_lrp_list_row(columns, true));
						for (let i = 0; i < data.message.length; i++) {
							$results.append(make_lrp_list_row(columns, true, data.message[i]));
						}
					} else {
						$results.append($placeholder);
					}
				}
			})
		};
		$wrapper = d.fields_dict.result_area.$wrapper.append(`<div class="results" 
				style="border: 1px solid #d1d8dd; border-radius: 3px; height: 500px; overflow: auto;"></div>`);
		$results = $wrapper.find('.results');
		$placeholder = $(`<div class="multiselect-empty-state">
					<span class="text-center" style="margin-top: -40px;">
						<i class="fa fa-2x fa-heartbeat text-extra-muted"></i>
						<p class="text-extra-muted">No LRP Items found</p>
					</span>
				</div>`);
		$results.on('click', '.list-item--head :checkbox', (e) => {
			$results.find('.list-item-container .list-row-check')
				.prop("checked", ($(e.target).is(':checked')));
		});
		set_lrp_primary_action(frm, d, $results, true);
		d.$wrapper.find('.modal-content').css('width', '900px');
		d.show();
	},
	get_therapy_items: (frm) => {
		let d = new frappe.ui.Dialog({
			title: "Select Therapy Items",
			fields: [
				{
					fieldname: "html_space",
					fieldtype: "HTML"
				}
			]
		});
		var $wrapper;
		var $results;
		var $placeholder;
		if (frm.doc.patient, frm.doc.appointment, frm.doc.company) {
			let columns = (["therapy_type", "sessions", "encounter_no", "therapy_plan", "therapy_session", 'status']);

			frappe.call({
				method: "hms_tz.hms_tz.doctype.lrpmt_returns.lrpmt_returns.get_therapies",
				args: {
					patient: frm.doc.patient,
					appointment: frm.doc.appointment,
					company: frm.doc.company
				},
				freeze: true,
				freeze_message: __('<i class="fa fa-spinner fa-spin fa-4x"></i>'),
				callback: (r) => {
					if (r.message.length > 0) {
						var data = r.message;
						$results.append(make_therapy_list_row(columns, true));
						for (let i = 0; i < data.length; i++) {
							$results.append(make_therapy_list_row(columns, true, data[i]));
						}
					}
					else {
						$results.append($placeholder)
					}
				}
			})
		};
		$wrapper = d.fields_dict.html_space.$wrapper.append(`<div class="results" 
                style="border: 1px solid #d1d8dd; border-radius: 3px; height: 500px; overflow: auto; margin: 0 auto;"></div>`);


		$results = $wrapper.find('.results');
		$placeholder = $(`<div class="multiselect-empty-state">
						<span class="text-center" style="margin-top: -40px;">
							<i class="fa fa-2x fa-heartbeat text-extra-muted"></i>
							<p class="text-extra-muted">No Therapy Items found</p>
						</span>
					</div>`);
		$results.on('click', '.list-item--head :checkbox', (e) => {
			$results.find('.list-item-container .list-row-check')
				.prop("checked", ($(e.target).is(':checked')));
		});
		set_therapy_primary_action(frm, d, $results, true);
		d.$wrapper.find('.modal-content').css('width', '950px');
		d.show();
	},

	get_drug_items: function (frm) {
		let d = new frappe.ui.Dialog({
			title: "Select Drug Items",
			fields: [
				{
					fieldname: "html_space",
					fieldtype: "HTML"
				}
			]
		});
		var $wrapper;
		var $results;
		var $placeholder;
		if (frm.doc.patient, frm.doc.appointment, frm.doc.company) {
			var columns = (["item_name", "qty_prescribed", "qty_returned", "encounter_no", "delivery_note", 'status'])
			frappe.call({
				method: "hms_tz.hms_tz.doctype.lrpmt_returns.lrpmt_returns.get_drug_item_list",
				args: {
					patient: frm.doc.patient,
					appointment: frm.doc.appointment,
					company: frm.doc.company
				},
				freeze: true,
				freeze_message: __('<i class="fa fa-spinner fa-spin fa-4x"></i>'),
				callback: (r) => {
					if (r.message.length > 0) {
						var data = r.message;
						$results.append(make_drug_list_row(columns, true));
						for (let i = 0; i < data.length; i++) {
							$results.append(make_drug_list_row(columns, true, data[i]));
						}
					}
					else {
						$results.append($placeholder)
					}
				}
			})
		};
		$wrapper = d.fields_dict.html_space.$wrapper.append(`<div class="results" 
				style="border: 1px solid #d1d8dd; border-radius: 3px; height: 500px; overflow: auto;"></div>`);
		$results = $wrapper.find('.results');
		$placeholder = $(`<div class="multiselect-empty-state">
					<span class="text-center" style="margin-top: -40px;">
						<i class="fa fa-2x fa-heartbeat text-extra-muted"></i>
						<p class="text-extra-muted">No Drug Items found</p>
					</span>
				</div>`);
		$results.on('click', '.list-item--head :checkbox', (e) => {
			$results.find('.list-item-container .list-row-check')
				.prop("checked", ($(e.target).is(':checked')));
		});
		set_drug_primary_action(frm, d, $results, true);
		d.$wrapper.find('.modal-content').css('width', '950px');
		d.show();
	},
});

var make_lrp_list_row = function (columns, item, result = {}) {
	var me = this;
	// Make a head row by default (if result not passed)
	let head = Object.keys(result).length === 0;
	let contents = ``;
	columns.forEach(function (column) {
		contents += `<div class="list-item__content ellipsis">
			${head ? `<span class="ellipsis"><b>${__(frappe.model.unscrub(column))}</b></span>`

				: (column !== "name" ? `<span class="ellipsis">${__(result[column])}</span>`
					: `<a class="list-id ellipsis">${__(result[column])}</a>`)
			}
		</div>`;
	});

	let $row = $(`<div class="list-item">
		<div class="list-item__content" style="flex: 0 0 10px;">
			<input type="checkbox" class="list-row-check" ${result.checked ? 'checked' : ''}>
		</div>
		${contents}
	</div>`);

	$row = list_row_lrp_items(head, $row, result, item);
	return $row;
};

var list_row_lrp_items = function (head, $row, result, item) {
	if (item) {
		head ? $row.addClass('list-item--head')
			: $row = $(`<div class="list-item-container"
				data-child_name = "${result.child_name}"
				data-item = "${result.item_name}"
				data-quantity = "${result.quantity}"
				data-encounter = "${result.encounter_no}"
				data-reference_doctype = "${result.reference_doctype}"
				data-reference_docname = "${result.reference_docname}",
				data-status = "${result.status}"
			</div>`).append($row);
	}
	return $row;
};

var set_lrp_primary_action = function (frm, d, $results, item) {
	var me = this;
	d.set_primary_action(__('Add'), function () {
		let checked_items = get_checked_lrp_items($results);
		if (checked_items.length > 0) {
			add_to_lrp_line(frm, checked_items, item);
			d.hide();
		}
	});
};

var get_checked_lrp_items = function ($results) {
	return $results.find('.list-item-container').map(function () {
		let checked_items = {};
		if ($(this).find(".list-row-check:checkbox:checked").length > 0) {
			checked_items["child_name"] = $(this).attr("data-child_name");
			checked_items["item"] = $(this).attr("data-item");
			checked_items["quantity"] = $(this).attr("data-quantity");
			checked_items["encounter"] = $(this).attr("data-encounter");
			if ($(this).attr("data-reference_doctype") != "undefined") {
				checked_items["reference_doctype"] = $(this).attr("data-reference_doctype");
			}
			else {
				checked_items["reference_doctype"] = false;
			}
			if ($(this).attr("data-reference_docname") != "undefined") {
				checked_items["reference_docname"] = $(this).attr("data-reference_docname");
			}
			else {
				checked_items["reference_docname"] = false;
			}
			return checked_items;
		}
	}).get();
};

var add_to_lrp_line = function (frm, checked_items, item) {
	if (item) {
		frappe.call({
			method: "hms_tz.hms_tz.doctype.lrpmt_returns.lrpmt_returns.set_checked_lrp_items",
			args: {
				doc: frm.doc,
				checked_items: checked_items
			},
			callback: function (r) {
				frm.trigger("validate");
				frm.refresh_fields();
				if (frm.is_new()) {
					frappe.set_route("Form", "LRPMT Return", r.message);
				} else {
					frm.reload_doc();
				}
			}
		});
	}
};

var make_drug_list_row = function (columns, item, result = {}) {
	var me = this;
	// Make a head row by default (if result not passed)
	let head = Object.keys(result).length === 0;
	let contents = ``;
	columns.forEach(function (column) {
		let contentWidth = column === "qty_prescribed" || column === "qty_returned" || column === "status" ? 100 : 160; // Set width based on column name
		contents += `<div class="list-item__content ellipsis" style="flex: 0 0 ${contentWidth}px;">
			${head ? `<span class="ellipsis"><b>${__(frappe.model.unscrub(column))}</b></span>`

				: (column !== "name" ? `<span class="ellipsis">${__(result[column])}</span>`
					: `<a class="list-id ellipsis">${__(result[column])}</a>`)
			}
		</div>`;
	});

	let $row = $(`<div class="list-item">
		<div class="list-item__content" style="flex: 0 0 10px;">
			<input type="checkbox" class="list-row-check" ${result.checked ? 'checked' : ''}>
		</div>
		${contents}
	</div>`);

	$row = list_row_drug_items(head, $row, result, item);
	return $row;
};

var list_row_drug_items = function (head, $row, result, item) {
	if (item) {
		head ? $row.addClass('list-item--head')
			: $row = $(`<div class="list-item-container"
				data-child_name = "${result.child_name}"
				data-item_name = "${result.item_name}"
				data-qty_prescribed = "${result.qty_prescribed}"
				data-qty_returned = "${result.qty_returned}"
				data-encounter_no = "${result.encounter_no}"
				data-delivery_note = "${result.delivery_note}"
				data-dn_detail = "${result.dn_detail}",
				data-status = "${result.status}"
			</div>`).append($row);
	}
	return $row;
};

var set_drug_primary_action = function (frm, d, $results, item) {
	var me = this;
	d.set_primary_action(__('Add'), function () {
		let checked_items = get_checked_drug_items($results);
		if (checked_items.length > 0) {
			add_to_drug_line(frm, checked_items, item);
			d.hide();
		}
	});
};

var get_checked_drug_items = function ($results) {
	return $results.find('.list-item-container').map(function () {
		let checked_items = {};
		if ($(this).find(".list-row-check:checkbox:checked").length > 0) {
			checked_items["child_name"] = $(this).attr("data-child_name");
			checked_items["item_name"] = $(this).attr("data-item_name");
			checked_items["qty_prescribed"] = $(this).attr("data-qty_prescribed");
			checked_items["qty_returned"] = $(this).attr("data-qty_returned");
			checked_items["encounter_no"] = $(this).attr("data-encounter_no");
			checked_items["delivery_note"] = $(this).attr("data-delivery_note");
			checked_items["dn_detail"] = $(this).attr("data-dn_detail");
			checked_items["status"] = $(this).attr("data-status");
			return checked_items;
		}
	}).get();
};

var add_to_drug_line = function (frm, checked_items, item) {
	if (item) {
		frappe.call({
			method: "hms_tz.hms_tz.doctype.lrpmt_returns.lrpmt_returns.set_checked_drug_items",
			args: {
				doc: frm.doc,
				checked_items: checked_items
			},
			callback: function (r) {
				frm.trigger("validate");
				frm.refresh_fields();
				if (frm.is_new()) {
					frappe.set_route("Form", "LRPMT Returns", r.message);
				} else {
					frm.reload_doc();
				}
			}
		});
	}
};

var make_therapy_list_row = function (columns, item, result = {}) {
	var me = this;
	// Make a head row by default (if result not passed)
	let head = Object.keys(result).length === 0;
	let contents = ``;
	columns.forEach(function (column) {
		let contentWidth = column === "status" || column === "sessions" ? 65 : 150; // Set width based on column name
		contents += `<div class="list-item__content ellipsis" style="flex: 0 0 ${contentWidth}px;">
            ${head ? `<span class="ellipsis"><b>${__(frappe.model.unscrub(column))}</b></span>`
				: (column !== "name" ? `<span class="ellipsis">${__(result[column])}</span>`
					: `<a class="list-id ellipsis">${__(result[column])}</a>`)
			}
        </div>`;
	});

	let $row = $(`<div class="list-item">
        <div class="list-item__content" style="flex: 0 0 10px;">
            <input type="checkbox" class="list-row-check" ${result.checked ? 'checked' : ''}>
        </div>
        ${contents}
    </div>`);

	$row = list_row_therapy_items(head, $row, result, item);
	return $row;
};

var list_row_therapy_items = function (head, $row, result, item) {
	if (item) {
		head ? $row.addClass('list-item--head')
			: $row = $(`<div class="list-item-container"
                data-status = "${result.status}"
                data-sessions = "${result.sessions}"
                data-encounter_no = "${result.encounter_no}"
                data-therapy_plan = "${result.therapy_plan}"
                data-therapy_type = "${result.therapy_type}"
                data-therapy_session = "${result.therapy_session}"
				data-sessions_cancelled = "${result.sessions_cancelled}"
                data-plan_child_table_id = "${result.plan_child_table_id}"
                data-encounter_child_table_id = "${result.encounter_child_table_id}"

            </div>`).append($row);
	}
	return $row;
};

var set_therapy_primary_action = function (frm, d, $results, item) {
	var me = this;
	d.set_primary_action(__('Add'), function () {
		let checked_items = get_checked_therapy_items($results);
		if (checked_items.length > 0) {
			add_to_therapy_line(frm, checked_items, item);
			d.hide();
		}
	});
};

var get_checked_therapy_items = function ($results) {
	return $results.find('.list-item-container').map(function () {
		let checked_items = {};
		if ($(this).find(".list-row-check:checkbox:checked").length > 0) {
			checked_items["status"] = $(this).attr("data-status");
			checked_items["therapy_type"] = $(this).attr("data-therapy_type");
			checked_items["encounter_no"] = $(this).attr("data-encounter_no");
			checked_items["therapy_plan"] = $(this).attr("data-therapy_plan");
			checked_items["sessions_prescribed"] = $(this).attr("data-sessions");
			checked_items["therapy_session"] = $(this).attr("data-therapy_session");
			checked_items["sessions_cancelled"] = $(this).attr("data-sessions_cancelled");
			checked_items["plan_child_table_id"] = $(this).attr("data-plan_child_table_id");
			checked_items["encounter_child_table_id"] = $(this).attr("data-encounter_child_table_id");
			return checked_items;
		}
	}).get();
};

var add_to_therapy_line = function (frm, checked_items, item) {
	if (item) {
		frappe.call({
			method: "hms_tz.hms_tz.doctype.lrpmt_returns.lrpmt_returns.set_checked_therapy_items",
			args: {
				doc: frm.doc,
				checked_items: checked_items
			},
			callback: function (r) {
				frm.trigger("validate");
				frm.refresh_fields();
				if (frm.is_new()) {
					frappe.set_route("Form", "LRPMT Returns", r.message);
				} else {
					frm.reload_doc();
				}
			}
		});
	}
};

frappe.ui.form.on("Medication Return", {
	quantity_to_return: function (frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		frm.validate_quantity_to_return(frm, row)
	}
})


frappe.ui.form.on("Therapy Return", {
	sessions_to_cancel: function (frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		frm.validate_no_of_sessions_to_cancel(frm, row)
	}
})
