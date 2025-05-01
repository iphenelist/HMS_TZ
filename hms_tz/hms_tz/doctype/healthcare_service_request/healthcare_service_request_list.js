frappe.listview_settings['Healthcare Service Request'] = {
    add_fields: ['source_doctype', 'source_docname', 'doctype', 'patient', 'appointment'],
    hide_name_column: true,
    
    onload: (listview) => {
        listview.page.clear_primary_action();

        listview.page.add_inner_button(__("Create Service Request"), () => {
            show_dialog(listview);
        }).removeClass("btn-default").addClass("btn-primary btn-sm");
    },
};


var show_dialog = (listview) => {
    let d = new frappe.ui.Dialog({
        title: "Service Request",
        fields: [
            {
                label: 'Source Doctype',
                fieldname: 'source_doctype',
                fieldtype: 'Select',
                options: [
                    {label: __('Patient Encounter'), value: 'Patient Encounter'},
                    {label: __('Lab Test'), value: 'Lab Test'},
                    {label: __('Radiology Examination'), value: 'Radiology Examination'},
                    {label: __('Clinical Procedure'), value: 'Clinical Procedure'},
                    {label: __('Therapy Session'), value: 'Therapy Session'},
                ],
                reqd: 1
            },
            {
                fieldname: 'insp_cb',
                fieldtype: 'Column Break'
            },
            {
                label: 'Source Docname',
                fieldname: 'source_docname',
                fieldtype: 'Link',
                reqd: 1
            },
        ],
        size: "small",
        primary_action_label: 'Save',
        primary_action(values) {
            if (values) {
                if (values.source_doctype != 'Patient Encounter') {
                    frappe.msgprint('Only Patient Encounter is supported for now')
                    return;
                } else {
                    frappe.call({
                        method: 'hms_tz.hms_tz.doctype.healthcare_service_request.healthcare_service_request.create_service_request',
                        args: {
                            data: values
                        },
                        freeze: true,
                        freeze_message: __('<i class="fa fa-spinner fa-spin fa-4x"></i>'),
                        callback: (r) => {
                            if (r.message) {
                                d.hide()
    
                                frappe.set_route('Form', 'Healthcare Service Request', r.message);
    
                                frappe.show_alert({
                                    message: __("{0} Service Request Created successfully", [r.message]),
                                    indicator: 'green'
                                }, 10);
                            }
                        }
                    });
                }
            }
        }
    });

    d.fields_dict.source_doctype.df.onchange = () => {
        let source_doctype = d.get_value('source_doctype');
        if (source_doctype != 'Patient Encounter') {
            frappe.msgprint('Only Patient Encounter is supported for now')
            return;
        }

        d.fields_dict.source_docname.df.options = source_doctype;
    }
    d.fields_dict.source_docname.df.get_query = (doc) => {
        return {
            filters: {
                'docstatus': 1,
            }
        }
    }

    d.show();
}
