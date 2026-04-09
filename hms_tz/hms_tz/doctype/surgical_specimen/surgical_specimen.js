// Copyright (c) 2026, Aakvatech and contributors
// For license information, please see license.txt

frappe.ui.form.on("Surgical Specimen", {
  setup(frm) {
    frm.set_query("collected_by", () => ({
      filters: { status: "Active" },
    }));
    frm.set_query("patient", () => ({
      filters: { status: "Active" },
    }));
  },

  refresh(frm) {
    if (!frm.is_new()) {
      // Status transitions
      if (frm.doc.status === "Collected") {
        frm.add_custom_button(
          __("Send to Lab"),
          () => {
            frm.set_value("status", "Sent to Lab");
            frm.save();
          },
          __("Actions")
        );
      }

      if (frm.doc.status === "Sent to Lab") {
        frm.add_custom_button(
          __("Results Received"),
          () => {
            frm.set_value("status", "Results Received");
            frm.save();
          },
          __("Actions")
        );
      }

      // Create Lab Test from specimen
      if (frm.doc.status === "Collected" && !frm.doc.lab_test) {
        frm.add_custom_button(
          __("Lab Test"),
          () => {
            frappe.new_doc("Lab Test", {
              patient: frm.doc.patient,
              company: frm.doc.company,
            });
          },
          __("Create")
        );
      }
    }
  },
});
