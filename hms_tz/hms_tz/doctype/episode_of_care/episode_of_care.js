// Copyright (c) 2020, earthians and contributors
// For license information, please see license.txt

frappe.ui.form.on("Episode of Care", {
  setup: function (frm) {
    frm.set_query("initiated_by", function () {
      return { filters: { practitioner_role: "Doctor" } };
    });
    frm.set_query("primary_practitioner", function () {
      return { filters: { practitioner_role: "Doctor" } };
    });
  },
});
