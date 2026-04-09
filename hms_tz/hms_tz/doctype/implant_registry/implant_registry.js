// Copyright (c) 2026, Aakvatech and contributors
// For license information, please see license.txt

frappe.ui.form.on("Implant Registry", {
  setup(frm) {
    frm.set_query("implanted_by", () => ({
      filters: { practitioner_role: "Doctor" },
    }));
    frm.set_query("patient", () => ({
      filters: { status: "Active" },
    }));
  },

  refresh(frm) {
    if (!frm.is_new()) {
      if (frm.doc.status === "Planned") {
        frm.add_custom_button(
          __("Mark Implanted"),
          () => {
            frm.set_value("status", "Implanted");
            if (!frm.doc.implant_date) {
              frm.set_value("implant_date", frappe.datetime.get_today());
            }
            frm.save();
          },
          __("Actions")
        );
      }

      if (frm.doc.status === "Implanted") {
        frm.add_custom_button(
          __("Mark Removed"),
          () => {
            frm.set_value("status", "Removed");
            frm.save();
          },
          __("Actions")
        );
      }

      // Expiry warning
      if (frm.doc.expiry_date) {
        let expiry = frappe.datetime.str_to_obj(frm.doc.expiry_date);
        let today = frappe.datetime.str_to_obj(frappe.datetime.get_today());
        if (expiry < today) {
          frm.dashboard.add_indicator(__("EXPIRED"), "red");
        } else {
          let days_left = frappe.datetime.get_diff(
            frm.doc.expiry_date,
            frappe.datetime.get_today()
          );
          if (days_left <= 30) {
            frm.dashboard.add_indicator(
              __("Expires in {0} days", [days_left]),
              "orange"
            );
          }
        }
      }
    }
  },
});
