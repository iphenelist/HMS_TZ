/*
(c) ESS 2015-16
*/
frappe.listview_settings['Patient Encounter'] = {
	filters: [["docstatus", "!=", "2"], ["duplicated", "==", "0"]],
	onload: function (listview) {
		listview.page.fields_dict['admission_service_unit_type'].get_query = function () {
			return {
				filters: {
					inpatient_occupancy: 1
				}
			};
		};
	}
};
