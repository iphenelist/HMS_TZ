// Copyright (c) 2020, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Patient Referral", {
  setup: function (frm) {
    frm.set_query("referred_to_practitioner", function () {
      return { filters: { practitioner_role: "Doctor" } };
    });
    frm.set_query("practitioner", function () {
      return { filters: { practitioner_role: "Doctor" } };
    });
  },
  refresh: function (frm) {
    if (!frm.doc.__islocal) {
      if (frm.doc.status == "Pending" && frm.doc.docstatus == 1) {
        frm.add_custom_button(__("Book Appointment"), function () {
          frappe.route_options = {
            patient: frm.doc.patient,
            practitioner: frm.doc.referred_to_practitioner,
            department: frm.doc.department,
            patient_referral: frm.doc.name,
            company: frm.doc.company,
          };
          frappe.new_doc("Patient Appointment");
        });
      }
    }
  },
});
