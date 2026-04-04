// Copyright (c) 2026, Aakvatech Limited and contributors
// For license information, please see license.txt

frappe.ui.form.on("Nursing Schedule", {
  setup: function (frm) {
    // Filter 'nurse' column in child table to only show Nurses
    frm.set_query("nurse", "shifts", function () {
      return {
        filters: {
          practitioner_role: "Nurse",
        },
      };
    });

    // Filter 'service_unit' and 'service_unit_type' correctly
    frm.set_query("service_unit", "shifts", function () {
      return {
        filters: {
          is_group: 0,
        },
      };
    });
  },

  start_date: function (frm) {
    if (frm.doc.start_date && frm.doc.end_date) {
      if (frm.doc.start_date > frm.doc.end_date) {
        frappe.msgprint(__("Start Date cannot be after End Date."));
        frm.set_value("start_date", "");
      }
    }
  },

  end_date: function (frm) {
    if (frm.doc.start_date && frm.doc.end_date) {
      if (frm.doc.end_date < frm.doc.start_date) {
        frappe.msgprint(__("End Date cannot be before Start Date."));
        frm.set_value("end_date", "");
      }
    }
  },
});

frappe.ui.form.on("Nurse Schedule Detail", {
  shift_based_on: function (frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    if (row.shift_based_on === "Service Unit") {
      frappe.model.set_value(cdt, cdn, "service_unit_type", "");
    } else {
      frappe.model.set_value(cdt, cdn, "service_unit", "");
    }
  },
});
