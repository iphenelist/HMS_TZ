// Copyright (c) 2026, Aakvatech and contributors
// For license information, please see license.txt

frappe.ui.form.on("Surgical Handover", {
  setup(frm) {
    frm.set_query("handed_over_by", () => ({
      filters: { status: "Active" },
    }));
    frm.set_query("received_by", () => ({
      filters: { status: "Active" },
    }));
    frm.set_query("patient", () => ({
      filters: { status: "Active" },
    }));
    frm.set_query("from_location", () => ({
      filters: { disabled: 0 },
    }));
    frm.set_query("to_location", () => ({
      filters: { disabled: 0 },
    }));
  },

  refresh(frm) {
    if (!frm.is_new()) {
      // Checklist progress
      let checklist_fields = [
        "patient_identity_verified",
        "consent_verified",
        "surgical_site_marked",
        "allergies_documented",
        "iv_lines_checked",
        "vitals_stable",
        "medications_documented",
        "blood_products_available",
        "specimens_handed_over",
        "drain_tubes_documented",
      ];

      let done = checklist_fields.filter((f) => frm.doc[f]).length;
      let total = checklist_fields.length;
      let color =
        done === total ? "green" : done > total / 2 ? "orange" : "red";
      frm.dashboard.add_indicator(
        __("Checklist: {0}/{1}", [done, total]),
        color
      );
    }
  },

  acknowledgement(frm) {
    if (frm.doc.acknowledgement && !frm.doc.acknowledged_time) {
      frm.set_value("acknowledged_time", frappe.datetime.now_datetime());
    }
  },

  type(frm) {
    // Suggest default checklist items based on handover type
    if (frm.doc.type === "Ward to Theater") {
      frm.dashboard.add_comment(
        __(
          "Ensure patient identity, consent, site marking, and fasting are verified before transfer."
        ),
        "blue",
        true
      );
    }
  },
});
