// Copyright (c) 2026, Aakvatech and contributors
// For license information, please see license.txt

frappe.ui.form.on("Preoperative Assessment", {
  setup(frm) {
    frm.set_query("patient", () => ({
      filters: { status: "Active" },
    }));
  },

  refresh(frm) {
    if (!frm.is_new()) {
      // Status action buttons
      if (frm.doc.status === "Pending" || frm.doc.status === "Completed") {
        frm.add_custom_button(
          __("Clear for Surgery"),
          () => {
            frm.set_value("status", "Cleared for Surgery");
            frm.save();
          },
          __("Actions")
        );

        frm.add_custom_button(
          __("Not Cleared"),
          () => {
            frm.set_value("status", "Not Cleared");
            frm.save();
          },
          __("Actions")
        );
      }

      // Show checklist progress
      let checks = [
        "fasting_status_verified",
        "blood_crossmatch_available",
        "consent_signed",
        "site_marking_verified",
        "iv_access_secured",
        "pre_op_labs_reviewed",
      ];
      let done = checks.filter((c) => frm.doc[c]).length;
      frm.dashboard.add_indicator(
        __("Checks: {0}/{1}", [done, checks.length]),
        done === checks.length ? "green" : "orange"
      );
    }
  },

  ot_schedule(frm) {
    if (frm.doc.ot_schedule) {
      frappe.db.get_value(
        "OT Schedule",
        frm.doc.ot_schedule,
        ["patient", "company"],
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
