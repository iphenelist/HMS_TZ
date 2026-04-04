// Copyright (c) 2020, earthians and contributors
// For license information, please see license.txt

frappe.ui.form.on("Healthcare Service Order", {
  setup: function (frm) {
    frm.set_query("ordered_by", function () {
      return { filters: { practitioner_role: "Doctor" } };
    });
    frm.set_query("referring_practitioner", function () {
      return { filters: { practitioner_role: "Doctor" } };
    });
  },
  refresh: function (frm) {
    frm.set_query("insurance_subscription", function () {
      return {
        filters: {
          patient: frm.doc.patient,
          docstatus: 1,
        },
      };
    });
  },
});
