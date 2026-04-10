// Copyright (c) 2026, Aakvatech and contributors
// For license information, please see license.txt

frappe.ui.form.on("Nurse Record", {
  setup: (frm) => {
    render_age(frm);
    render_vital_signs(frm);
  },

  refresh: (frm) => {
    set_queries(frm);
    render_consumables_placeholder(frm);
    render_pending_medications(frm);
    render_medication_progress(frm);
    render_completed_medications(frm);
    check_upcoming_medications(frm);
  },

  onload: (frm) => {
    render_age(frm);
    render_vital_signs(frm);
  },

  appointment: (frm) => {
    if (frm.doc.appointment) {
      render_vital_signs(frm);
      render_age(frm);
    }
  },

  record_vital_signs: (frm) => {
    if (frm.is_new() || frm.doc.docstatus === 2) return;

    show_vital_signs_dialog(frm);
  },
});

function set_queries(frm) {
  frm.set_query("nurse", () => {
    return {
      filters: {
        status: "Active",
        practitioner_role: "Nurse",
        hms_tz_company: frm.doc.company,
      },
    };
  });

  frm.set_query("acknowledged_by", () => {
    return {
      filters: {
        status: "Active",
        practitioner_role: "Nurse",
        hms_tz_company: frm.doc.company,
      },
    };
  });
  frm.set_query("service_unit", () => {
    return {
      filters: {
        disabled: 0,
        is_group: 0,
        company: frm.doc.company,
      },
    };
  });

  frm.set_query("service_unit_type", () => {
    return {
      filters: {
        disabled: 0,
      },
    };
  });
}

function render_vital_signs(frm) {
  if (!frm.doc.patient) return;
  frappe.call({
    method: "hms_tz.hms_tz.doctype.nurse_record.nurse_record.get_vital_signs",
    args: {
      patient: frm.doc.patient,
      appointment: frm.doc.appointment || "",
    },
    callback: function (r) {
      if (r.message && r.message.length > 0) {
        render_vitals_chart_and_table(frm, r.message);
      } else {
        frm.fields_dict.vital_signs_html.$wrapper.html(
          '<div class="text-muted text-center p-4">' +
            __("No vital signs recorded for this patient episode.") +
            "</div>"
        );
      }
    },
  });
}

function render_vitals_chart_and_table(frm, vitals) {
  let $wrapper = frm.fields_dict.vital_signs_html.$wrapper;
  $wrapper.empty();

  // --- Chart Section ---
  let chart_id = "vitals-chart-" + frm.doc.name;
  $wrapper.append('<div class="mb-4"><div id="' + chart_id + '"></div></div>');

  let labels = vitals.map(function (v) {
    return v.signs_date;
  });
  let temp_data = vitals.map(function (v) {
    return parseFloat(v.temperature) || 0;
  });
  let pulse_data = vitals.map(function (v) {
    return parseFloat(v.pulse) || 0;
  });
  let rr_data = vitals.map(function (v) {
    return parseFloat(v.respiratory_rate) || 0;
  });
  let bp_sys_data = vitals.map(function (v) {
    return parseFloat(v.bp_systolic) || 0;
  });
  let bp_dia_data = vitals.map(function (v) {
    return parseFloat(v.bp_diastolic) || 0;
  });

  new frappe.Chart("#" + chart_id, {
    title: __("Vital Signs Trend"),
    data: {
      labels: labels,
      datasets: [
        { name: __("Temperature (°C)"), values: temp_data },
        { name: __("Pulse (bpm)"), values: pulse_data },
        { name: __("Respiratory Rate"), values: rr_data },
        { name: __("BP Systolic"), values: bp_sys_data },
        { name: __("BP Diastolic"), values: bp_dia_data },
      ],
    },
    type: "line",
    height: 280,
    colors: ["#ff6384", "#36a2eb", "#4bc0c0", "#ff9f40", "#9966ff"],
    lineOptions: {
      regionFill: 0,
      hideDots: 0,
    },
  });

  // --- Table Section ---
  let table_html = '<table class="table table-bordered table-sm mt-3">';
  table_html += "<thead><tr>";
  table_html += "<th>" + __("Date") + "</th>";
  table_html += "<th>" + __("Time") + "</th>";
  table_html += "<th>" + __("Temp (°C)") + "</th>";
  table_html += "<th>" + __("Pulse") + "</th>";
  table_html += "<th>" + __("RR") + "</th>";
  table_html += "<th>" + __("BP") + "</th>";
  table_html += "<th>" + __("Weight") + "</th>";
  table_html += "<th>" + __("BMI") + "</th>";
  table_html += "<th>" + __("Notes") + "</th>";
  table_html += "</tr></thead><tbody>";

  vitals.forEach(function (v) {
    let bp_display = v.bp || v.bp_systolic + "/" + v.bp_diastolic;
    table_html += "<tr>";
    table_html += "<td>" + (v.signs_date || "") + "</td>";
    table_html += "<td>" + (v.signs_time || "") + "</td>";
    table_html += "<td>" + (v.temperature || "") + "</td>";
    table_html += "<td>" + (v.pulse || "") + "</td>";
    table_html += "<td>" + (v.respiratory_rate || "") + "</td>";
    table_html += "<td>" + bp_display + "</td>";
    table_html += "<td>" + (v.weight || "") + "</td>";
    table_html += "<td>" + (v.bmi || "") + "</td>";
    table_html += "<td>" + (v.vital_signs_note || "") + "</td>";
    table_html += "</tr>";
  });

  table_html += "</tbody></table>";
  $wrapper.append(table_html);
}

function show_vital_signs_dialog(frm) {
  let d = new frappe.ui.Dialog({
    title: __("Record Vital Signs"),
    fields: [
      {
        fieldname: "temperature",
        fieldtype: "Data",
        label: __("Temperature (°C)"),
      },
      {
        fieldname: "pulse",
        fieldtype: "Data",
        label: __("Pulse (bpm)"),
      },
      {
        fieldname: "respiratory_rate",
        fieldtype: "Data",
        label: __("Respiratory Rate"),
      },
      { fieldtype: "Column Break" },
      {
        fieldname: "bp_systolic",
        fieldtype: "Data",
        label: __("BP Systolic"),
      },
      {
        fieldname: "bp_diastolic",
        fieldtype: "Data",
        label: __("BP Diastolic"),
      },
      { fieldtype: "Section Break" },
      {
        fieldname: "weight",
        fieldtype: "Float",
        label: __("Weight (kg)"),
      },
      {
        fieldname: "height",
        fieldtype: "Float",
        label: __("Height (cm)"),
      },
      { fieldtype: "Column Break" },
      {
        fieldname: "tongue",
        fieldtype: "Select",
        label: __("Tongue"),
        options: "\nCoated\nVery Coated\nNormal\nFurry\nCuts",
      },
      {
        fieldname: "abdomen",
        fieldtype: "Select",
        label: __("Abdomen"),
        options: "\nNormal\nBloated\nFull\nFluid\nConstipated",
      },
      {
        fieldname: "reflexes",
        fieldtype: "Select",
        label: __("Reflexes"),
        options: "\nNormal\nHyper\nVery Hyper\nOne Sided",
      },
      { fieldtype: "Section Break" },
      {
        fieldname: "vital_signs_note",
        fieldtype: "Small Text",
        label: __("Notes"),
      },
    ],
    primary_action_label: __("Save"),
    primary_action(values) {
      frappe.call({
        method:
          "hms_tz.hms_tz.doctype.nurse_record.nurse_record.create_vital_signs",
        args: {
          patient: frm.doc.patient,
          nurse_record: frm.doc.name,
          ...values,
        },
        callback: function (r) {
          if (r.message) {
            frappe.show_alert({
              message: __("Vital Signs {0} created and submitted", [
                r.message,
              ]),
              indicator: "green",
            });
            d.hide();
            render_vital_signs(frm);
          }
        },
      });
    },
  });

  d.show();
}

// ─── Pending Medications (HTML-based, from IMO Entry) ───

function render_pending_medications(frm) {
  if (!frm.fields_dict.pending_medications_html) return;
  if (!frm.doc.patient || !frm.doc.inpatient_record) {
    frm.fields_dict.pending_medications_html.$wrapper.html(
      '<div class="text-muted text-center p-4">' +
        __("Pending medications will appear for admitted patients.") +
        "</div>"
    );
    return;
  }

  frappe.call({
    method:
      "hms_tz.hms_tz.doctype.nurse_record.nurse_record.get_pending_medications",
    args: {
      patient: frm.doc.patient,
      inpatient_record: frm.doc.inpatient_record,
    },
    callback: (r) => {
      if (r.message && r.message.length > 0) {
        render_pending_meds_table(frm, r.message);
      } else {
        frm.fields_dict.pending_medications_html.$wrapper.html(
          '<div class="text-muted text-center p-4">' +
            __("No pending medications.") +
            "</div>"
        );
      }
    },
  });
}

function render_pending_meds_table(frm, entries) {
  let $wrapper = frm.fields_dict.pending_medications_html.$wrapper;
  $wrapper.empty();

  let html =
    '<table class="table table-sm table-bordered">' +
    "<thead><tr>" +
    "<th>" +
    __("Drug") +
    "</th>" +
    "<th>" +
    __("Qty") +
    "</th>" +
    "<th>" +
    __("Form") +
    "</th>" +
    "<th>" +
    __("Date") +
    "</th>" +
    "<th>" +
    __("Time") +
    "</th>" +
    "<th>" +
    __("Status") +
    "</th>" +
    '<th class="text-center">' +
    __("Action") +
    "</th>" +
    "</tr></thead><tbody>";

  entries.forEach((e) => {
    let held_badge =
      e.administration_status === "Held"
        ? ' <span class="badge badge-warning">' + __("Held") + "</span>"
        : "";

    let time_display = e.time ? e.time.substring(0, 5) : "";
    let is_overdue = e.date < frappe.datetime.get_today();
    let overdue_class = is_overdue
      ? ' class="text-danger font-weight-bold"'
      : "";

    html +=
      "<tr>" +
      "<td>" +
      (e.drug_name || e.drug) +
      "</td>" +
      "<td>" +
      (e.dosage || "") +
      "</td>" +
      "<td>" +
      (e.dosage_form || "") +
      "</td>" +
      "<td" +
      overdue_class +
      ">" +
      (e.date || "") +
      (is_overdue ? " ⚠️" : "") +
      "</td>" +
      "<td>" +
      time_display +
      "</td>" +
      "<td>" +
      (held_badge || __("Pending")) +
      "</td>" +
      '<td class="text-center">' +
      '<button class="btn btn-xs btn-primary btn-update-med" ' +
      'data-entry="' +
      e.name +
      '" ' +
      'data-drug="' +
      (e.drug_name || e.drug) +
      '" ' +
      'data-time="' +
      time_display +
      '">' +
      __("Update") +
      "</button>" +
      "</td>" +
      "</tr>";
  });

  html += "</tbody></table>";
  $wrapper.html(html);

  // Bind click handlers
  $wrapper.find(".btn-update-med").on("click", function () {
    let entry_name = $(this).data("entry");
    let drug_name = $(this).data("drug");
    let sched_time = $(this).data("time");
    show_update_medication_dialog(frm, entry_name, drug_name, sched_time);
  });
}

function show_update_medication_dialog(
  frm,
  entry_name,
  drug_name,
  sched_time
) {
  let d = new frappe.ui.Dialog({
    title: __("Update Medication Status"),
    fields: [
      {
        fieldname: "drug_info",
        fieldtype: "HTML",
        options:
          '<div class="mb-3" style="padding: 8px; background: var(--bg-light-gray); border-radius: 4px;">' +
          "<strong>" +
          drug_name +
          "</strong>" +
          (sched_time
            ? " &mdash; " + __("Scheduled") + ": " + sched_time
            : "") +
          "</div>",
      },
      {
        fieldname: "status",
        fieldtype: "Select",
        label: __("Status"),
        options: "Administered\nSkipped\nRefused\nHeld",
        default: "Administered",
        reqd: 1,
      },
      {
        fieldname: "notes",
        fieldtype: "Small Text",
        label: __("Notes"),
        description: __(
          "Required when skipping, refusing, or holding a medication."
        ),
        mandatory_depends_on: 'eval:doc.status!="Administered"',
      },
    ],
    primary_action_label: __("Confirm"),
    primary_action(values) {
      if (values.status !== "Administered" && !values.notes) {
        frappe.msgprint(
          __("Please provide a reason in the Notes field for {0}.", [
            values.status,
          ])
        );
        return;
      }

      frappe.call({
        method:
          "hms_tz.hms_tz.doctype.nurse_record.nurse_record.update_medication_status",
        args: {
          imo_entry_name: entry_name,
          status: values.status,
          notes: values.notes || "",
          nurse_record: frm.doc.name,
        },
        callback: (r) => {
          if (r.message && r.message.status === "success") {
            let indicator =
              values.status === "Administered" ? "green" : "orange";
            frappe.show_alert({
              message: __("Medication marked as {0}", [values.status]),
              indicator: indicator,
            });
            d.hide();
            render_pending_medications(frm);
            render_medication_progress(frm);
            render_completed_medications(frm);
          }
        },
      });
    },
  });

  d.show();
}

// ─── Medication Progress Chart ───

function render_medication_progress(frm) {
  if (!frm.fields_dict.medication_progress_html) return;
  if (!frm.doc.patient || !frm.doc.inpatient_record) {
    frm.fields_dict.medication_progress_html.$wrapper.html(
      '<div class="text-muted text-center p-4">' +
        __("Medication progress will appear once medications are ordered.") +
        "</div>"
    );
    return;
  }

  frappe.call({
    method:
      "hms_tz.hms_tz.doctype.nurse_record.nurse_record.get_medication_progress",
    args: {
      patient: frm.doc.patient,
      inpatient_record: frm.doc.inpatient_record,
    },
    callback: (r) => {
      if (r.message && r.message.length > 0) {
        render_med_progress_chart(frm, r.message);
      } else {
        frm.fields_dict.medication_progress_html.$wrapper.html(
          '<div class="text-muted text-center p-4">' +
            __("No medication orders found for this patient.") +
            "</div>"
        );
      }
    },
  });
}

function render_med_progress_chart(frm, data) {
  let $wrapper = frm.fields_dict.medication_progress_html.$wrapper;
  $wrapper.empty();

  let chart_id = "med-progress-chart-" + frm.doc.name;
  $wrapper.append('<div class="mb-3"><div id="' + chart_id + '"></div></div>');

  let labels = data.map((d) => d.drug_name);
  let completed_values = data.map((d) => d.completed);
  let pending_values = data.map((d) => d.pending);

  new frappe.Chart("#" + chart_id, {
    title: __("Medication Administration Progress"),
    data: {
      labels: labels,
      datasets: [
        {
          name: __("Administered"),
          values: completed_values,
          chartType: "bar",
        },
        {
          name: __("Pending"),
          values: pending_values,
          chartType: "bar",
        },
      ],
    },
    type: "bar",
    height: 250,
    colors: ["#36a2eb", "#ff6384"],
    barOptions: {
      stacked: 1,
      spaceRatio: 0.4,
    },
  });

  // Summary table below chart
  let summary_html =
    '<table class="table table-sm table-bordered mt-2">' +
    "<thead><tr>" +
    "<th>" +
    __("Drug") +
    "</th>" +
    "<th class='text-center'>" +
    __("Total") +
    "</th>" +
    "<th class='text-center'>" +
    __("Administered") +
    "</th>" +
    "<th class='text-center'>" +
    __("Pending") +
    "</th>" +
    "</tr></thead><tbody>";

  data.forEach((d) => {
    let pct = d.total > 0 ? Math.round((d.completed / d.total) * 100) : 0;
    let badge_class =
      pct === 100
        ? "badge-success"
        : pct > 50
        ? "badge-warning"
        : "badge-danger";

    summary_html +=
      "<tr>" +
      "<td>" +
      d.drug_name +
      "</td>" +
      '<td class="text-center">' +
      d.total +
      "</td>" +
      '<td class="text-center">' +
      d.completed +
      "</td>" +
      '<td class="text-center">' +
      '<span class="badge ' +
      badge_class +
      '">' +
      d.pending +
      "</span>" +
      "</td></tr>";
  });

  summary_html += "</tbody></table>";
  $wrapper.append(summary_html);
}

// ─── Completed Medications ───

function render_completed_medications(frm) {
  if (!frm.fields_dict.completed_medications_html) return;
  if (!frm.doc.patient || !frm.doc.inpatient_record) {
    frm.fields_dict.completed_medications_html.$wrapper.html("");
    return;
  }

  frappe.call({
    method:
      "hms_tz.hms_tz.doctype.nurse_record.nurse_record.get_completed_medications",
    args: {
      patient: frm.doc.patient,
      inpatient_record: frm.doc.inpatient_record,
    },
    callback: (r) => {
      if (r.message && r.message.length > 0) {
        render_completed_meds_table(frm, r.message);
      } else {
        frm.fields_dict.completed_medications_html.$wrapper.html(
          '<div class="text-muted text-center p-3">' +
            __("No completed medications yet.") +
            "</div>"
        );
      }
    },
  });
}

function render_completed_meds_table(frm, entries) {
  let $wrapper = frm.fields_dict.completed_medications_html.$wrapper;
  $wrapper.empty();

  let html =
    '<table class="table table-sm table-bordered">' +
    "<thead><tr>" +
    "<th>" +
    __("Drug") +
    "</th>" +
    "<th>" +
    __("Qty") +
    "</th>" +
    "<th>" +
    __("Form") +
    "</th>" +
    "<th>" +
    __("Date") +
    "</th>" +
    "<th>" +
    __("Time") +
    "</th>" +
    "<th>" +
    __("Status") +
    "</th>" +
    "<th>" +
    __("Notes") +
    "</th>" +
    "</tr></thead><tbody>";

  entries.forEach((e) => {
    let status = e.administration_status || __("Administered");
    let status_color =
      status === "Administered"
        ? "green"
        : status === "Held"
        ? "orange"
        : "red";

    html +=
      "<tr>" +
      "<td>" +
      (e.drug_name || e.drug) +
      "</td>" +
      "<td>" +
      (e.dosage || "") +
      "</td>" +
      "<td>" +
      (e.dosage_form || "") +
      "</td>" +
      "<td>" +
      (e.date || "") +
      "</td>" +
      "<td>" +
      (e.time || "") +
      "</td>" +
      '<td><span class="indicator-pill ' +
      status_color +
      '">' +
      status +
      "</span></td>" +
      "<td>" +
      (e.administration_notes || "") +
      "</td>" +
      "</tr>";
  });

  html += "</tbody></table>";
  $wrapper.append(html);
}

// ─── Upcoming Medications Alert Banner ───

function check_upcoming_medications(frm) {
  if (!frm.doc.nurse || frm.is_new()) return;

  frappe.call({
    method:
      "hms_tz.hms_tz.doctype.nurse_record.nurse_record.get_upcoming_medications",
    args: {
      nurse: frm.doc.nurse,
      within_minutes: 30,
    },
    callback: (r) => {
      if (r.message && r.message.length > 0) {
        show_medication_alert_banner(frm, r.message);
      }
    },
  });
}

function show_medication_alert_banner(frm, medications) {
  // Build a detailed table of all upcoming medications across all patients
  let total_count = medications.length;

  let table_html =
    '<table class="table table-sm table-bordered mb-0" ' +
    'style="background: white; font-size: 12px;">' +
    "<thead>" +
    '<tr style="background: #fff3cd;">' +
    "<th>" +
    __("Patient") +
    "</th>" +
    "<th>" +
    __("Drug") +
    "</th>" +
    "<th>" +
    __("Qty") +
    "</th>" +
    "<th>" +
    __("Dosage Form") +
    "</th>" +
    "<th>" +
    __("Scheduled Time") +
    "</th>" +
    "</tr>" +
    "</thead><tbody>";

  medications.forEach((med) => {
    let url = frappe.utils.get_form_link(
      "Nurse Record",
      med.nurse_record_name
    );
    let time_display = med.scheduled_time
      ? med.scheduled_time.substring(0, 5)
      : "";

    table_html +=
      "<tr>" +
      '<td><a href="' +
      url +
      '" class="font-weight-bold">' +
      med.patient_name +
      "</a></td>" +
      "<td>" +
      (med.drug_name || "") +
      "</td>" +
      "<td>" +
      (med.dosage || "") +
      "</td>" +
      "<td>" +
      (med.dosage_form || "") +
      "</td>" +
      "<td>" +
      time_display +
      "</td>" +
      "</tr>";
  });

  table_html += "</tbody></table>";

  let alert_html =
    '<div class="alert alert-warning alert-dismissible fade show" ' +
    'role="alert" style="margin-bottom: 0; border-radius: 0; padding: 10px;">' +
    '<div class="d-flex align-items-center mb-2">' +
    '<span class="mr-2" style="font-size: 1.2em;">⚠️</span>' +
    "<strong>" +
    total_count +
    __(" medication(s) due within the next 30 minutes") +
    "</strong>" +
    '<button type="button" class="close ml-auto" data-dismiss="alert" aria-label="Close">' +
    '<span aria-hidden="true">&times;</span>' +
    "</button>" +
    "</div>" +
    '<div style="max-height: 200px; overflow-y: auto;">' +
    table_html +
    "</div>" +
    "</div>";

  // Insert above the form
  frm.$wrapper
    .find(".form-message, .medication-alert-banner")
    .filter(".medication-alert-banner")
    .remove();
  $(alert_html)
    .addClass("medication-alert-banner")
    .prependTo(frm.$wrapper.find(".form-page"));
}

// ─── Consumables Placeholder ───

function render_consumables_placeholder(frm) {
  if (!frm.fields_dict.consumables_html) return;

  frm.fields_dict.consumables_html.$wrapper.html(
    '<div class="text-muted text-center p-4">' +
      __(
        "Consumables tracking will be available after the Consumable Record module is implemented."
      ) +
      "</div>"
  );
}

// ─── Age Display ───

function render_age(frm) {
  if (!frm.fields_dict.age || !frm.fields_dict.age.$wrapper) return;

  if (!frm.doc.patient) {
    frm.fields_dict.age.$wrapper.html("");
    return;
  }

  frappe.call({
    method: "frappe.client.get_value",
    args: {
      doctype: "Patient",
      filters: { name: frm.doc.patient },
      fieldname: "dob",
    },
    callback: (r) => {
      if (r.message && r.message.dob) {
        const age_str = get_age(r.message.dob);
        frm.fields_dict.age.$wrapper.html(
          `<div class="clearfix"><span class="text-muted">${__(
            "AGE"
          )} : ${age_str}</span></div>`
        );
      } else {
        frm.fields_dict.age.$wrapper.html("");
      }
    },
  });
}

const get_age = function (birth) {
  let birth_moment = moment(birth);
  let current_moment = moment(Date());
  let diff = moment.duration(current_moment.diff(birth_moment));
  return `${diff.years()} ${__("Year(s)")} ${diff.months()} ${__(
    "Month(s)"
  )} ${diff.days()} ${__("Day(s)")}`;
};
