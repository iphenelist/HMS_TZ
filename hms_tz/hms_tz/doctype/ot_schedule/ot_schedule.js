// Copyright (c) 2026, Aakvatech and contributors
// For license information, please see license.txt

frappe.ui.form.on("OT Schedule", {
  setup(frm) {
    // Filter surgeons to doctors only
    for (let field of [
      "primary_surgeon",
      "assistant_surgeon",
      "anesthetist",
    ]) {
      frm.set_query(field, () => ({
        filters: { practitioner_role: "Doctor" },
      }));
    }
    // Filter nurses
    for (let field of ["scrub_nurse", "circulating_nurse"]) {
      frm.set_query(field, () => ({
        filters: { practitioner_role: "Nurse" },
      }));
    }
    frm.set_query("patient", () => ({
      filters: { status: "Active" },
    }));
    frm.set_query("theater_room", () => ({
      filters: { disabled: 0 },
    }));
  },

  refresh(frm) {
    if (!frm.is_new() && frm.doc.status === "Scheduled") {
      frm.add_custom_button(
        __("Start Procedure"),
        () => {
          frm.set_value("status", "In Progress");
          frm.save();
        },
        __("Actions")
      );

      frm.add_custom_button(
        __("Cancel Schedule"),
        () => {
          frappe.confirm(
            __("Are you sure you want to cancel this schedule?"),
            () => {
              frm.set_value("status", "Cancelled");
              frm.save();
            }
          );
        },
        __("Actions")
      );
    }

    if (frm.doc.status === "In Progress") {
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
    if (!frm.is_new() && frm.doc.status !== "Cancelled") {
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
