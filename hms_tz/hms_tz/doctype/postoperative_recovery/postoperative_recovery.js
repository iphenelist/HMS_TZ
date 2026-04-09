// Copyright (c) 2026, Aakvatech and contributors
// For license information, please see license.txt

frappe.ui.form.on("Postoperative Recovery", {
  setup(frm) {
    frm.set_query("recovery_nurse", () => ({
      filters: { practitioner_role: "Nurse" },
    }));
    frm.set_query("patient", () => ({
      filters: { status: "Active" },
    }));
  },

  refresh(frm) {
    if (!frm.is_new()) {
      // Recovery score summary
      if (frm.doc.recovery_scores && frm.doc.recovery_scores.length) {
        let total = 0,
          max_total = 0;
        frm.doc.recovery_scores.forEach((row) => {
          total += cint(row.score);
          max_total += cint(row.max_score || 0);
        });
        let indicator = total >= max_total * 0.7 ? "green" : "orange";
        frm.dashboard.add_indicator(
          __("Recovery Score: {0}/{1}", [total, max_total || "?"]),
          indicator
        );
      }

      // Status transitions
      if (frm.doc.status === "In Recovery") {
        frm.add_custom_button(
          __("Mark Stable"),
          () => {
            frm.set_value("status", "Stable");
            frm.save();
          },
          __("Status")
        );
      }

      if (["In Recovery", "Stable"].includes(frm.doc.status)) {
        frm.add_custom_button(
          __("Discharge to Ward"),
          () => {
            frm.set_value("status", "Discharged to Ward");
            frm.set_value("discharge_time", frappe.datetime.now_datetime());
            frm.save();
          },
          __("Status")
        );

        frm.add_custom_button(
          __("Transfer to ICU"),
          () => {
            frm.set_value("status", "Transferred to ICU");
            frm.save();
          },
          __("Status")
        );
      }

      // Add Aldrete score template
      frm.add_custom_button(__("Add Aldrete Score"), () => {
        add_aldrete_template(frm);
      });
    }
  },
});

function add_aldrete_template(frm) {
  const aldrete_params = [
    { parameter: "Activity", max_score: 2 },
    { parameter: "Respiration", max_score: 2 },
    { parameter: "Circulation", max_score: 2 },
    { parameter: "Consciousness", max_score: 2 },
    { parameter: "O2 Saturation", max_score: 2 },
  ];

  let now_time = frappe.datetime.now_time();

  let fields = aldrete_params.map((p) => ({
    label: p.parameter,
    fieldname: p.parameter.toLowerCase().replace(/ /g, "_"),
    fieldtype: "Select",
    options: "0\n1\n2",
    default: "0",
  }));

  let d = new frappe.ui.Dialog({
    title: __("Aldrete Score Assessment"),
    fields: fields,
    primary_action_label: __("Add Scores"),
    primary_action(values) {
      aldrete_params.forEach((p) => {
        let field_key = p.parameter.toLowerCase().replace(/ /g, "_");
        let row = frm.add_child("recovery_scores");
        row.score_type = "Aldrete";
        row.parameter = p.parameter;
        row.score = cint(values[field_key]);
        row.max_score = p.max_score;
        row.time_recorded = now_time;
      });
      frm.refresh_field("recovery_scores");
      d.hide();
      frm.dirty();
    },
  });
  d.show();
}
