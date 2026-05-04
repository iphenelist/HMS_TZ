// Copyright (c) 2026, Aakvatech and contributors
// For license information, please see license.txt

frappe.ui.form.on("Preoperative Assessment", {
  setup(frm) {
    frm.trigger("set_filters");
  },

  refresh(frm) {
    if (!frm.is_new()) {
      // Status action buttons
      // if (frm.doc.status === "Pending" || frm.doc.status === "Completed") {
      //   frm.add_custom_button(
      //     __("Clear for Surgery"),
      //     () => {
      //       frm.set_value("status", "Cleared for Surgery");
      //       frm.save();
      //     },
      //     __("Actions")
      //   );

      //   frm.add_custom_button(
      //     __("Not Cleared"),
      //     () => {
      //       frm.set_value("status", "Not Cleared");
      //       frm.save();
      //     },
      //     __("Actions")
      //   );
      // }

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

    // Render consumables tab
    render_consumables_section(frm);
  },

  onload: (frm) => {
    frm.trigger("set_filters");
  },

  ot_schedule(frm) {
    if (frm.doc.ot_schedule) {
      frappe.db.get_value(
        "OT Schedule",
        frm.doc.ot_schedule,
        ["patient", "company", "clinical_procedure", "procedure_template"],
        (r) => {
          if (r) {
            if (r.patient) frm.set_value("patient", r.patient);
            if (r.company) frm.set_value("company", r.company);
            if (r.procedure_template)
              frm.set_value("service_name", r.procedure_template);

            if (r.clinical_procedure) {
              frm.set_value("clinical_procedure", r.clinical_procedure);
              // Fetch appointment from Clinical Procedure
              frappe.db.get_value(
                "Clinical Procedure",
                r.clinical_procedure,
                ["appointment"],
                (cp) => {
                  if (cp && cp.appointment) {
                    frm.set_value("appointment", cp.appointment);
                  }
                }
              );
            }
          }
        }
      );
    }
  },

  appointment(frm) {
    if (frm.doc.appointment) {
      frappe.db.get_value(
        "Patient Appointment",
        frm.doc.appointment,
        ["insurance_subscription", "coverage_plan_name", "insurance_company"],
        (r) => {
          if (r) {
            if (r.insurance_company) {
              frm.set_value("payment_type", "Insurance");
              frm.set_value(
                "insurance_subscription",
                r.insurance_subscription || ""
              );
              frm.set_value(
                "insurance_coverage_plan",
                r.coverage_plan_name || ""
              );
              frm.set_value("insurance_company", r.insurance_company || "");
            } else {
              frm.set_value("payment_type", "Cash");
              frm.set_value("insurance_subscription", "");
              frm.set_value("insurance_coverage_plan", "");
              frm.set_value("insurance_company", "");
            }
          }
        }
      );
    } else {
      frm.set_value("payment_type", "");
      frm.set_value("insurance_subscription", "");
      frm.set_value("insurance_coverage_plan", "");
      frm.set_value("insurance_company", "");
    }
  },

  set_filters: (frm) => {
    frm.set_query("appointment", () => {
      return {
        filters: {
          status: ["not in", ["Open", "Scheduled", "Cancelled"]],
        },
      };
    });
    frm.set_query("patient", () => {
      return {
        filters: { status: "Active" },
      };
    });

    frm.set_query("service_name", () => {
      return {
        filters: { disabled: 0 },
      };
    });

    frm.set_query("ot_schedule", () => {
      const filters = {};
      if (frm.doc.patient) filters.patient = frm.doc.patient;
      return { filters };
    });
    frm.set_query("pre_operative_notes_template", () => {
      return {
        filters: {
          disabled: 0,
          terms: ["!=", ""],
        },
      };
    });
  },
});

function render_consumables_section(frm) {
  if (!frm.fields_dict.consumables_html) return;

  if (frm.is_new() || !frm.doc.patient) {
    frm.fields_dict.consumables_html.$wrapper.html(
      '<div class="text-muted text-center p-4">' +
        __("Save the Preoperative Assessment first to add consumables.") +
        "</div>"
    );
    return;
  }

  const $wrapper = frm.fields_dict.consumables_html.$wrapper;
  $wrapper.empty();

  // Button container
  const $btn_container = $(
    '<div class="d-flex justify-content-end mb-3" style="gap: 8px;"></div>'
  ).appendTo($wrapper);

  // "Add Consumables" button
  $('<button class="btn btn-primary btn-sm">')
    .html('<i class="fa fa-plus mr-1"></i>' + __("Add Consumables"))
    .on("click", () => {
      if (!window.hms_tz || !hms_tz.open_consumable_dialog) {
        frappe.msgprint(
          __("Consumable dialog not loaded. Please reload the page.")
        );
        return;
      }
      hms_tz.open_consumable_dialog({
        patient: frm.doc.patient,
        patient_name: frm.doc.patient_name,
        appointment: frm.doc.appointment || "",
        company: frm.doc.company,
        payment_type: frm.doc.payment_type || "Cash",
        insurance_subscription: frm.doc.insurance_subscription || "",
        insurance_company: frm.doc.insurance_company || "",
        insurance_coverage_plan: frm.doc.insurance_coverage_plan || "",
        prescribed_by: frm.doc.practitioner,
        source_doctype: "Clinical Procedure",
        source_docname: frm.doc.clinical_procedure,
        service_name: frm.doc.service_name || "",
        on_success: () => {
          frm.reload_doc();
        },
      });
    })
    .appendTo($btn_container);

  // Fetch and display existing consumable records
  const filters = { patient: frm.doc.patient };
  if (frm.doc.appointment) {
    filters.appointment = frm.doc.appointment;
  }

  frappe.call({
    method: "frappe.client.get_list",
    args: {
      doctype: "Consumable Record",
      filters: filters,
      fields: [
        "name",
        "posting_date",
        "status",
        "total_amount",
        "payment_type",
        "delivery_note",
        "docstatus",
      ],
      order_by: "creation desc",
      limit_page_length: 50,
    },
    callback: (r) => {
      if (!r.message || r.message.length === 0) {
        $('<div class="text-muted text-center p-3">')
          .text(__("No consumable records yet."))
          .appendTo($wrapper);
        return;
      }

      const records = r.message;
      let table_html =
        '<div class="table-responsive"><table class="table table-bordered table-sm">';
      table_html += "<thead><tr>";
      table_html += '<th class="text-left">' + __("Record") + "</th>";
      table_html += '<th class="text-left">' + __("Date") + "</th>";
      table_html += '<th class="text-left">' + __("Payment") + "</th>";
      table_html += '<th class="text-right">' + __("Total") + "</th>";
      table_html += '<th class="text-center">' + __("Status") + "</th>";
      table_html += '<th class="text-left">' + __("Delivery Note") + "</th>";
      table_html += '<th class="text-center">' + __("Action") + "</th>";
      table_html += "</tr></thead><tbody>";

      records.forEach((rec) => {
        const status_color = {
          Draft: "orange",
          Submitted: "blue",
          "Pending Payment": "red",
          Dispensed: "green",
          Finalized: "darkgreen",
          Billed: "purple",
        };
        const color = status_color[rec.status] || "gray";

        table_html += "<tr>";
        table_html +=
          '<td><a href="/app/consumable-record/' +
          rec.name +
          '">' +
          rec.name +
          "</a></td>";
        table_html += "<td>" + (rec.posting_date || "") + "</td>";
        table_html += "<td>" + (rec.payment_type || "") + "</td>";
        table_html +=
          '<td class="text-right">' +
          format_currency(rec.total_amount || 0) +
          "</td>";
        table_html +=
          '<td class="text-center"><span class="indicator-pill ' +
          color +
          '">' +
          (rec.status || "Draft") +
          "</span></td>";
        table_html +=
          "<td>" +
          (rec.delivery_note
            ? '<a href="/app/delivery-note/' +
              rec.delivery_note +
              '">' +
              rec.delivery_note +
              "</a>"
            : "-") +
          "</td>";

        // Action column — Submit button for draft records
        if (rec.docstatus === 0) {
          table_html +=
            '<td class="text-center">' +
            '<button class="btn btn-xs btn-primary btn-submit-consumable" data-name="' +
            rec.name +
            '">' +
            __("Submit") +
            "</button></td>";
        } else {
          table_html += '<td class="text-center">-</td>';
        }

        table_html += "</tr>";
      });

      table_html += "</tbody></table></div>";
      const $table = $(table_html).appendTo($wrapper);

      // Wire submit buttons
      $table.find(".btn-submit-consumable").on("click", function () {
        const consumable_name = $(this).data("name");
        frappe.confirm(
          __("Are you sure you want to submit Consumable Record {0}?", [
            consumable_name,
          ]),
          () => {
            frappe.call({
              method:
                "hms_tz.hms_tz.doctype.consumable_record.consumable_api.submit_consumable_record",
              args: { consumable_record: consumable_name },
              freeze: true,
              freeze_message: __("Submitting..."),
              callback: (r) => {
                if (!r.exc) {
                  frappe.show_alert({
                    message: __("Consumable Record {0} submitted.", [
                      consumable_name,
                    ]),
                    indicator: "green",
                  });
                  frm.reload_doc();
                }
              },
            });
          }
        );
      });
    },
  });
}
