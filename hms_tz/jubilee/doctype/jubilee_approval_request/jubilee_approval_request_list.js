// Copyright (c) 2026, Aakvatech Limited and contributors
// For license information, please see license.txt

frappe.listview_settings["Jubilee Approval Request"] = {
  onload: function (listview) {
    setup_primary_action(listview);
  },

  refresh: function (listview) {
    setup_primary_action(listview);
  },
};

function setup_primary_action(listview) {
  listview.page.clear_primary_action();
  listview.page.set_primary_action(
    __("Create Preauthorization"),
    function () {
      open_preauth_dialog();
    },
    "es-line-icon-externallink"
  );
}

function open_preauth_dialog() {
  const dialog = new frappe.ui.Dialog({
    title: __("Create Jubilee Preauthorization"),
    fields: [
      {
        label: __("Patient Appointment"),
        fieldname: "appointment",
        fieldtype: "Link",
        options: "Patient Appointment",
        reqd: 1,
        get_query: () => {
          return {
            filters: {
              status: "Closed",
              insurance_company: ["like", "Jubilee%"],
            },
          };
        },
        onchange: function () {
          if (dialog.get_value("appointment")) {
            dialog.set_df_property("benefit", "hidden", 0);
          } else {
            dialog.set_df_property("benefit", "hidden", 1);
          }
        },
      },
      {
        label: __("Benefit"),
        fieldname: "benefit",
        fieldtype: "Link",
        options: "Jubilee Benefit",
        reqd: 1,
        hidden: 1,
        get_query: function () {
          return {
            filters: {
              appointment: dialog.get_value("appointment"),
            },
          };
        },
      },
    ],
    primary_action_label: __("Open New Record"),
    primary_action: () => {
      let values = dialog.get_values();
      if (values) {
        dialog.hide();
        frappe.new_doc("Jubilee Approval Request", {
          appointment: values.appointment,
          jubilee_benefit: values.benefit,
        });
      }
    },
  });

  dialog.show();
}
