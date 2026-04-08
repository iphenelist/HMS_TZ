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
    setup_vital_signs_button(frm);
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
