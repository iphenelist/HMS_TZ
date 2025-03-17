frappe.ui.form.on('Healthcare Insurance Company', {
    onload: function (frm) {
        add_nhif_actions_btn(frm)
    },
    refresh: function (frm) {
        add_nhif_actions_btn(frm)
    },
});

var add_nhif_actions_btn = function (frm) {
    if (!frm.doc.insurance_company_name.includes("NHIF")) { 
        return 
    }

    frm.add_custom_button(__('Get NHIF Price Package'), function () {
        frappe.call({
            method: 'hms_tz.nhif.nhif_api.price_package.enqueue_get_nhif_price_packages',
            args: { company: frm.doc.company },
            callback: function (data) {
                if (data.message) {
                    console.log(data.message)
                }
            }
        });
        frappe.show_alert(__('fetch price package via backgroud job'), 5);
    }, __('NHIF Actions'));

    frm.add_custom_button(__('Only Process NHIF Records'), function () {
        frappe.call({
            method: 'hms_tz.nhif.nhif_api.price_package.process_nhif_records',
            args: { company: frm.doc.company },
            callback: function (data) {
                if (data.message) {
                    console.log(data.message)
                }
            }
        });
    }, __('NHIF Actions'));

    frm.add_custom_button(__('Get NHIF Schemes'), function () {
        frappe.call({
            method: 'hms_tz.nhif.nhif_api.price_package.get_nhif_schemes',
            args: { company: frm.doc.company },
            freeze: true,
            freeze_message: __('<i class="fa fa-spinner fa-spin fa-4x"></i>'),
            callback: function (data) {
                if (data.message) {
                    console.log(data.message)
                }
            }
        });
    }, __('NHIF Actions'));

    frm.add_custom_button(__('Get NHIF Item Types'), function () {
        frappe.call({
            method: 'hms_tz.nhif.nhif_api.price_package.get_item_types',
            args: { company: frm.doc.company },
            freeze: true,
            freeze_message: __('<i class="fa fa-spinner fa-spin fa-4x"></i>'),
            callback: function (data) {
                if (data.message) {
                    console.log(data.message)
                }
            }
        });
    }, __('NHIF Actions'));

    frm.add_custom_button(__('Get NHIF Items'), function () {
        frappe.call({
            method: 'hms_tz.nhif.nhif_api.price_package.enqueue_fetch_nhif_items',
            args: { company: frm.doc.company },
            callback: function (data) {
                if (data.message) {
                    console.log(data.message)
                }
            }
        });
    }, __('NHIF Actions'));
}