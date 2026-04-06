// Copyright (c) 2026, Aakvatech Limited and contributors
// For license information, please see license.txt

frappe.ui.form.on("Nursing Schedule", {
  setup: function (frm) {
    frm.trigger("set_query");
  },

  set_query: (frm) => {
    frm.set_query("nurse", "assignments", function () {
      return {
        filters: {
          status: 'Active',
          practitioner_role: "Nurse",
          hms_tz_company: frm.doc.company,
        },
      };
    });

    frm.set_query("service_unit_type", "assignments", function () {
      return {
        filters: {
          disabled: 0,
        },
      };
    });

    frm.set_query("service_unit", "assignments", function () {
      return {
        filters: {
          is_group: 0,
          disabled: 0,
          company: frm.doc.company,
        },
      };
    });
  },

  start_date: function (frm) {
    calculate_end_date(frm);
  },

  frequency: function (frm) {
    calculate_end_date(frm);
    set_daily_assignment_dates(frm);
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
            __(
              "No active nurses found for the selected company."
            )
          );
          return;
        }

        // Collect existing nurse names to avoid duplicates
        const existing_nurses = new Set(
          (frm.doc.assignments || []).map(
            (row) => row.nurse
          )
        );

        let added_count = 0;
        r.message.forEach(function (nurse) {
          if (!existing_nurses.has(nurse.name)) {
            let row = frm.add_child("assignments");
            row.nurse = nurse.name;
            row.nurse_name = nurse.practitioner_name;
            if (frm.doc.frequency === "Daily" && frm.doc.end_date) {
              row.assignment_date = frm.doc.end_date;
            }
            existing_nurses.add(nurse.name);
            added_count++;
          }
        });

        frm.refresh_field("assignments");

        if (added_count > 0) {
          frappe.show_alert({
            message: __(
              "{0} nurse(s) added to the schedule.",
              [added_count]
            ),
            indicator: "green",
          });
        } else {
          frappe.msgprint(
            __(
              "All active nurses are already in the schedule."
            )
          );
        }
      },
    });
  },
});

frappe.ui.form.on("Nurse Schedule Detail", {
  assignments_add: function (frm, cdt, cdn) {
    if (frm.doc.frequency === "Daily" && frm.doc.end_date) {
      frappe.model.set_value(
        cdt,
        cdn,
        "assignment_date",
        frm.doc.end_date
      );
    }
  },

  assign_based_on: function (frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    if (row.assign_based_on === "Service Unit") {
      frappe.model.set_value(
        cdt,
        cdn,
        "service_unit_type",
        ""
      );
    } else {
      frappe.model.set_value(cdt, cdn, "service_unit", "");
    }
  },
});

function set_daily_assignment_dates(frm) {
  if (frm.doc.frequency !== "Daily" || !frm.doc.end_date) return;

  (frm.doc.assignments || []).forEach(function (row) {
    if (!row.assignment_date) {
      frappe.model.set_value(
        row.doctype,
        row.name,
        "assignment_date",
        frm.doc.end_date
      );
    }
  });
  frm.refresh_field("assignments");
}

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
    end_date = frappe.datetime.add_days(
      frm.doc.start_date,
      offset.days
    );
  } else {
    // Add months, then subtract 1 day to get the last day of the period
    end_date = frappe.datetime.add_months(
      frm.doc.start_date,
      offset.months
    );
    end_date = frappe.datetime.add_days(end_date, -1);
  }

  frm.set_value("end_date", end_date);
}
