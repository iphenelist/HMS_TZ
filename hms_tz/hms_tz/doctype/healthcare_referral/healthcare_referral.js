// Copyright (c) 2025, Aakvatech and contributors
// For license information, please see license.txt

frappe.ui.form.on('Healthcare Referral', {
	setup: (frm) => {
		frm.get_field("diagnosis").grid.cannot_add_rows = true;
	},
	refresh: (frm) => {
		frm.get_field("diagnosis").grid.cannot_add_rows = true;
	},
	onload: (frm) => {
		frm.get_field("diagnosis").grid.cannot_add_rows = true;
	},
	select_diagnosis: (frm) => {
		if (!frm.doc.encounter) {
			frappe.msgprint({
				title: __('Message'),
				indicator: 'red',
				message: __(
					'<h4 class="text-center" style="background-color: #D3D3D3; font-weight: bold;">\
					Please select an Encounter before selecting a Diagnosis<h4>'
				)
			});
			return;
		}

		frm.call("get_diagnosis", {}).then((r) => {
			if (r.message) {
				show_diagnosis_dialog(frm, r.message);
			}
		});
	},
	select_service: (frm) => {
		if (!frm.doc.encounter) {
			frappe.msgprint({
				title: __('Message'),
				indicator: 'red',
				message: __(
					'<h4 class="text-center" style="background-color: #D3D3D3; font-weight: bold;">\
					Please select an Encounter before selecting a Service<h4>'
				)
			});
			return;
		}

		frm.call("get_services", {}).then((r) => {
			if (r.message) {
				show_service_dialog(frm, r.message);
			}
		});
	}
});


let show_diagnosis_dialog = (frm, data) => {
	let d = new frappe.ui.Dialog({
		title: __('Select Diagnosis'),
		fields: [
			{
				fieldtype: 'HTML',
				fieldname: 'diagnosis'
			}
		]
	});
	let wrapper = d.fields_dict.diagnosis.$wrapper;

	if (data.length > 0) {
		let data_html = show_diagnosis_details(data);
		wrapper.html(data_html);
	}

	wrapper.on("change", ".check-all", function () {
		const isChecked = $(this).is(":checked");
	
		wrapper.find("tbody .diagnosis-checkbox").prop("checked", isChecked);
	});

	d.set_primary_action(__("Select"), () => {
		let diagnosis = [];

		wrapper.find('tbody tr:has(input:checked)').each(function () {
			diagnosis.push({
				status: $(this).find("#status").attr("data-status"),
				disease_code: $(this).find("#disease_code").attr("data-disease_code"),
				description: $(this).find("#description").attr("data-description"),
			});
		});
		
		if (diagnosis.length > 0) {
			frm.doc.diagnosis = [];

			diagnosis.forEach((d) => {
				frm.add_child("diagnosis", {
					status: d.status,
					disease_code: d.disease_code,
					description: d.description
				});
			});

			frm.refresh_field("diagnosis");

			d.hide();
		} else {
			frappe.msgprint({
				title: __('Message'),
				indicator: 'red',
				message: __(
					'<h4 class="text-center" style="background-color: #D3D3D3; font-weight: bold;">\
					No any Diagnosis selected<h4>'
				)
			});
		}
	});

	d.$wrapper.find('.modal-content').css({
		"width": "750px",
		"max-height": "1000px",
		"overflow": "auto",
	});

	d.show();

	function show_diagnosis_details(data) {
		let html = `
			<style>
				.table-diagnosis {
					width: 700px;
					height: 400px;
					overflow-y: auto;
					border: 1px solid #ccc;
				}
				.table-diagnosis thead th {
					position: sticky;
					top: 0;
					background-color: white;
					z-index: 1;
				}
				.table-diagnosis table {
					width: 100%;
				}
				.check-all {
					transform: scale(1.2);
					margin: 5px;
				}
				.diagnosis-checkbox {
					transform: scale(1.2);
					margin: 5px;
				}
			</style>
			<div class="table-diagnosis">
				<table class="table table-sm table-hover">
					<colgroup>
						<col width="10%">
						<col width="20%">
						<col width="25%">
						<col width="45%">
					</colgroup>
					<thead>
						<tr>
							<th>
								<input type="checkbox" class="check-all">
							</th>
							<th>Status</th>
							<th>Disease Code</th>
							<th>Description</th>
						</tr>
					</thead>
					<tbody>`;
		
		data.forEach(row => {
			html += `<tr>
				<td><input type="checkbox" class="diagnosis-checkbox"/></td>
				<td id="status" data-status="${row.status}">${row.status}</td>
				<td id="disease_code" data-disease_code="${row.disease_code}">${row.disease_code}</td>
				<td id="description" data-description="${row.description}">${row.description}</td>
			</tr>`;
		});

		html += `</tbody></table></div></div>`;
		return html;
	}

}


let show_service_dialog = (frm, data) => {
	let d = new frappe.ui.Dialog({
		title: __('Select Service'),
		size: 'large',
		fields: [
			{
				fieldtype: 'HTML',
				fieldname: 'services'
			}
		]
	});
	let wrapper = d.fields_dict.services.$wrapper;

	if (data.length > 0) {
		let data_html = show_services_details(data);
		wrapper.html(data_html);
	}

	wrapper.on("change", ".check-all", function () {
		const isChecked = $(this).is(":checked");
	
		wrapper.find("tbody .services-checkbox").prop("checked", isChecked);
	});

	d.set_primary_action(__("Select"), () => {
		let services = [];

		wrapper.find('tbody tr:has(input:checked)').each(function () {
			services.push({
				service_type: $(this).find("#service_type").attr("data-service_type"),
				service_name: $(this).find("#service_name").attr("data-service_name"),
				item_code: $(this).find("#item_code").attr("data-item_code"),
				qty: $(this).find("#qty").attr("data-qty"),
			});
		});
		
		if (services.length > 0) {
			frm.doc.services = [];

			services.forEach((d) => {
				frm.add_child("services", {
					service_type: d.service_type,
					service_name: d.service_name,
					item_code: d.item_code,
					qty: d.qty
				});
			});

			frm.refresh_field("services");

			d.hide();
		} else {
			frappe.msgprint({
				title: __('Message'),
				indicator: 'red',
				message: __(
					'<h4 class="text-center" style="background-color: #D3D3D3; font-weight: bold;">\
					No any Service selected<h4>'
				)
			});
		}
	});

	d.$wrapper.find('.modal-content').css({
		"width": "750px",
		"max-height": "1000px",
		"overflow": "auto",
	});

	d.show();

	function show_services_details(data) {
		let html = `
			<style>
				.table-services {
					width: 700px;
					height: 400px;
					overflow-y: auto;
					border: 1px solid #ccc;
				}
				.table-services thead th {
					position: sticky;
					top: 0;
					background-color: white;
					z-index: 1;
				}
				.table-services table {
					width: 100%;
				}
				.check-all {
					transform: scale(1.2);
					margin: 5px;
				}
				.services-checkbox {
					transform: scale(1.2);
					margin: 5px;
				}
			</style>
			<div class="table-services">
				<table class="table table-sm table-hover">
					<colgroup>
						<col width="10%">
						<col width="35%">
						<col width="40%">
						<col width="15%">
					</colgroup>
					<thead>
						<tr>
							<th>
								<input type="checkbox" class="check-all">
							</th>
							<th>Service Type</th>
							<th>Service Name</th>
							<th>Qty</th>
						</tr>
					</thead>
					<tbody>`;
		
		data.forEach(row => {
			html += `<tr>
				<td><input type="checkbox" class="services-checkbox"/></td>
				<td id="service_type" data-service_type="${row.service_type}">${row.service_type}</td>
				<td id="service_name" data-service_name="${row.service_name}">${row.service_name}</td>
				<td id="qty" data-qty="${row.qty}">${row.qty}</td>
				<td id="item_code" data-item_code="${row.item_code}"></td>
			</tr>`;
		});

		html += `</tbody></table></div></div>`;
		return html;
	}

}

