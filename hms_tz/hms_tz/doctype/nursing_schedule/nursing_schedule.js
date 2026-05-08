// Copyright (c) 2026, Aakvatech Limited and contributors
// For license information, please see license.txt

frappe.ui.form.on("Nursing Schedule", {
  setup: function (frm) {
    frm.trigger("set_query");
  },

  set_query: (frm) => {
    frm.set_query("nurse", function () {
      return {
        filters: {
          status: "Active",
          practitioner_role: "Nurse",
          hms_tz_company: frm.doc.company,
        },
      };
    });

    frm.set_query("ward", function () {
      return {
        filters: {
          disabled: 0,
        },
      };
    });

    frm.set_query("room", function () {
      return {
        filters: {
          is_group: 0,
          disabled: 0,
          company: frm.doc.company,
        },
      };
    });
  },

  assign_based_on: function (frm) {
    if (frm.doc.assign_based_on === "Room") {
      frm.set_value("ward", "");
    } else {
      frm.set_value("room", "");
    }
  },

  shift_type: function (frm) {
    if (frm.doc.shift_type) {
      frappe.db.get_value(
        "Shift Type",
        frm.doc.shift_type,
        ["start_time", "end_time"],
        (r) => {
          if (r) {
            frm.set_value("shift_start_time", r.start_time);
            frm.set_value("shift_end_time", r.end_time);
          }
        }
      );
    }
  },
});
