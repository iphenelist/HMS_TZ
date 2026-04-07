// Copyright (c) 2026, Aakvatech Limited and contributors
// For license information, please see license.txt

frappe.ui.form.on("Nursing Schedule", {
  setup: function (frm) {
    frm.trigger("set_query");
  },

  set_query: (frm) => {
    frm.set_query("nurse", function () {
      return {
        filters: {
          status: "Active",
          practitioner_role: "Nurse",
          hms_tz_company: frm.doc.company,
        },
      };
    });

    frm.set_query("service_unit_type", function () {
      return {
        filters: {
          disabled: 0,
        },
      };
    });

    frm.set_query("service_unit", function () {
      return {
        filters: {
          is_group: 0,
          disabled: 0,
          company: frm.doc.company,
        },
      };
    });
  },

  assign_based_on: function (frm) {
    if (frm.doc.assign_based_on === "Service Unit") {
      frm.set_value("service_unit_type", "");
    } else {
      frm.set_value("service_unit", "");
    }
  },
});
