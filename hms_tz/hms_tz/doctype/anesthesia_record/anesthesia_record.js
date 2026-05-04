// Copyright (c) 2026, Aakvatech and contributors
// For license information, please see license.txt

frappe.ui.form.on("Anesthesia Record", {
  setup(frm) {
    frm.set_query("anesthetist", () => ({
      filters: { practitioner_role: "Doctor" },
    }));
    frm.set_query("patient", () => ({
      filters: { status: "Active" },
    }));
  },

  refresh(frm) {
    if (!frm.is_new() && frm.doc.clinical_procedure) {
      frm.add_custom_button(__("Open Procedure"), () => {
        frappe.set_route(
          "Form",
          "Clinical Procedure",
          frm.doc.clinical_procedure
        );
      });
    }
  },

  clinical_procedure(frm) {
    if (frm.doc.clinical_procedure) {
      frappe.db.get_value(
        "Clinical Procedure",
        frm.doc.clinical_procedure,
        ["patient", "company", "practitioner"],
        (r) => {
          if (r) {
            frm.set_value("patient", r.patient);
            frm.set_value("company", r.company);
          }
        }
      );
    }
  },
});
