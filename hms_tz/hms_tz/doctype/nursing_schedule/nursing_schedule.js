// Copyright (c) 2026, Aakvatech Limited and contributors
// For license information, please see license.txt

frappe.ui.form.on("Nursing Schedule", {
  setup: function (frm) {
    // Filter 'nurse' column in child table to only show Nurses
    frm.set_query("nurse", "shifts", function () {
      return {
        filters: {
          practitioner_role: "Nurse",
        },
      };
    });

    // Filter 'service_unit' and 'service_unit_type' correctly
    frm.set_query("service_unit", "shifts", function () {
      return {
        filters: {
          is_group: 0,
        },
      };
    });
  },

  start_date: function (frm) {
    calculate_end_date(frm);
  },

  frequency: function (frm) {
    calculate_end_date(frm);
  },

  get_nurses: function (frm) {
    if (!frm.doc.company) {
      frappe.msgprint(__("Please select a Company first."));
      return;
    }

    frappe.call({
      method:
        "hms_tz.hms_tz.doctype.nursing_schedule.nursing_schedule.get_nurses",
      args: {
        company: frm.doc.company,
      },
      freeze: true,
      freeze_message: __("Fetching nurses..."),
      callback: function (r) {
        if (!r.message || r.message.length === 0) {
          frappe.msgprint(
            __("No active nurses found for the selected company.")
          );
          return;
        }

        // Collect existing nurse names to avoid duplicates
        const existing_nurses = new Set(
          (frm.doc.shifts || []).map((row) => row.nurse)
        );

        let added_count = 0;
        r.message.forEach(function (nurse) {
          if (!existing_nurses.has(nurse.name)) {
            let row = frm.add_child("shifts");
            row.nurse = nurse.name;
            row.nurse_name = nurse.practitioner_name;
            existing_nurses.add(nurse.name);
            added_count++;
          }
        });

        frm.refresh_field("shifts");

        if (added_count > 0) {
          frappe.show_alert({
            message: __("{0} nurse(s) added to the schedule.", [added_count]),
            indicator: "green",
          });
        } else {
          frappe.msgprint(
            __("All active nurses are already in the schedule.")
          );
        }
      },
    });
  },
});

frappe.ui.form.on("Nurse Schedule Detail", {
  shift_based_on: function (frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    if (row.shift_based_on === "Service Unit") {
      frappe.model.set_value(cdt, cdn, "service_unit_type", "");
    } else {
      frappe.model.set_value(cdt, cdn, "service_unit", "");
    }
  },
});

function calculate_end_date(frm) {
  if (!frm.doc.start_date || !frm.doc.frequency) {
    frm.set_value("end_date", "");
    return;
  }

  const frequency_map = {
    Daily: { days: 0 },
    Weekly: { days: 6 },
    Monthly: { months: 1 },
    Quarterly: { months: 3 },
    "Bi-Yearly": { months: 6 },
    Yearly: { months: 12 },
  };

  const offset = frequency_map[frm.doc.frequency];
  if (!offset) return;

  let end_date;
  if (offset.days !== undefined) {
    end_date = frappe.datetime.add_days(frm.doc.start_date, offset.days);
  } else {
    // Add months, then subtract 1 day to get the last day of the period
    end_date = frappe.datetime.add_months(frm.doc.start_date, offset.months);
    end_date = frappe.datetime.add_days(end_date, -1);
  }

  frm.set_value("end_date", end_date);
}
