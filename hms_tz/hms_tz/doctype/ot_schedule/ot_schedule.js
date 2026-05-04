// Copyright (c) 2026, Aakvatech and contributors
// For license information, please see license.txt

frappe.ui.form.on("OT Schedule", {
  setup(frm) {
    frm.set_query("patient", () => ({
      filters: { status: "Active" },
    }));
    frm.set_query("theater_room", () => ({
      filters: {
        disabled: 0,
        is_group: 0,
        company: frm.doc.company,
      },
    }));
    // Filter practitioner in child table based on role
    frm.set_query("practitioner", "surgical_team", (doc, cdt, cdn) => {
      let row = locals[cdt][cdn];
      let role_filter = "Doctor";
      if (row.role === "Nurse") {
        role_filter = "Nurse";
      }
      return {
        filters: { practitioner_role: role_filter },
      };
    });
  },

  refresh(frm) {
    if (frm.doc.docstatus === 1 && frm.doc.status === "Scheduled") {
      frm.add_custom_button(
        __("Start Procedure"),
        () => {
          frm.set_value("status", "In Progress");
          frm.save();
        },
        __("Actions")
      );

      frm.add_custom_button(
        __("Postpone"),
        () => {
          frappe.confirm(
            __("Are you sure you want to postpone this schedule?"),
            () => {
              frm.set_value("status", "Postponed");
              frm.save();
            }
          );
        },
        __("Actions")
      );
    }

    if (frm.doc.docstatus === 1 && frm.doc.status === "In Progress") {
      frm.add_custom_button(
        __("Complete"),
        () => {
          frm.set_value("status", "Completed");
          frm.set_value("end_time", frappe.datetime.now_time());
          frm.save();
        },
        __("Actions")
      );
    }

    // Create linked documents
    if (
      frm.doc.docstatus === 1 &&
      !["Cancelled", "Postponed"].includes(frm.doc.status)
    ) {
      frm.add_custom_button(
        __("Preoperative Assessment"),
        () => {
          frappe.new_doc("Preoperative Assessment", {
            patient: frm.doc.patient,
            ot_schedule: frm.doc.name,
            company: frm.doc.company,
          });
        },
        __("Create")
      );

      frm.add_custom_button(
        __("Surgical Handover"),
        () => {
          frappe.new_doc("Surgical Handover", {
            patient: frm.doc.patient,
            company: frm.doc.company,
          });
        },
        __("Create")
      );
    }
  },
});
