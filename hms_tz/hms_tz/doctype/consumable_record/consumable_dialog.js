/**
 * Global Consumable Dialog — reusable from any DocType (Nurse Record, Clinical Procedure, etc.)
 *
 * Usage:
 *   hms_tz.open_consumable_dialog({
 *     patient: frm.doc.patient,
 *     company: frm.doc.company,
 *     appointment: frm.doc.appointment,
 *     payment_type: frm.doc.payment_type,
 *     insurance_subscription: frm.doc.insurance_subscription,
 *     insurance_company: frm.doc.insurance_company,
 *     insurance_coverage_plan: frm.doc.insurance_coverage_plan,
 *     prescribed_by: frm.doc.practitioner || frm.doc.nurse,
 *     source_doctype: frm.doc.doctype,
 *     source_docname: frm.doc.name,
 *     on_success: () => frm.reload_doc(),
 *   });
 */

if (!window.hms_tz) {
  window.hms_tz = {};
}

hms_tz.open_consumable_dialog = function (opts) {
  opts = Object.assign({}, opts || {});

  if (!opts.patient) {
    frappe.msgprint(__("Please select a Patient first."));
    return;
  }
  if (!opts.company) {
    frappe.msgprint(__("Company is required."));
    return;
  }

  const is_insurance = opts.payment_type === "Insurance";

  const dialog = new frappe.ui.Dialog({
    title: __("Add Consumable Items"),
    size: "extra-large",
    fields: [
      {
        fieldtype: "Section Break",
        label: __("Patient Details"),
      },
      {
        fieldname: "patient",
        fieldtype: "Link",
        label: __("Patient"),
        options: "Patient",
        default: opts.patient,
        read_only: 1,
      },
      {
        fieldname: "patient_name",
        fieldtype: "Data",
        label: __("Patient Name"),
        default: opts.patient_name || "",
        read_only: 1,
      },
      {
        fieldtype: "Column Break",
      },
      {
        fieldname: "company",
        fieldtype: "Link",
        label: __("Company"),
        options: "Company",
        default: opts.company,
        read_only: 1,
      },
      {
        fieldname: "payment_type",
        fieldtype: "Select",
        label: __("Payment Type"),
        options: "\nCash\nInsurance",
        default: opts.payment_type || "",
        read_only: 1,
      },
      {
        fieldname: "total_amount",
        fieldtype: "Currency",
        label: __("Total Amount"),
        read_only: 1,
        default: 0,
      },
      {
        fieldtype: "Column Break",
      },
      {
        fieldname: "insurance_subscription",
        fieldtype: "Link",
        label: __("Insurance Subscription"),
        options: "Healthcare Insurance Subscription",
        default: opts.insurance_subscription || "",
        read_only: 1,
        hidden: 1,
        depends_on: "eval:doc.payment_type=='Insurance'",
      },
      {
        fieldname: "insurance_coverage_plan",
        fieldtype: "Data",
        label: __("Coverage Plan"),
        default: opts.insurance_coverage_plan || "",
        read_only: 1,
        depends_on: "eval:doc.payment_type=='Insurance'",
      },
      {
        fieldname: "insurance_company",
        fieldtype: "Link",
        label: __("Insurance Company"),
        options: "Healthcare Insurance Company",
        default: opts.insurance_company || "",
        read_only: 1,
        depends_on: "eval:doc.payment_type=='Insurance'",
      },
      {
        fieldname: "default_warehouse",
        fieldtype: "Link",
        label: __("Default Warehouse"),
        options: "Warehouse",
        get_query: () => ({
          filters: {
            is_group: 0,
            company: opts.company,
            warehouse_name: ["like", "%Pharmacy%"],
          },
        }),
      },
      {
        fieldtype: "Section Break",
      },
      {
        fieldname: "source_doctype",
        fieldtype: "Select",
        label: __("Source Doctype"),
        options:
          "\nLab Test\nRadiology Examination\nClinical Procedure\nTherapy Session",
        default: opts.source_doctype || "",
      },
      {
        fieldtype: "Column Break",
      },
      {
        fieldname: "source_docname",
        fieldtype: "Dynamic Link",
        label: __("Source Document"),
        options: "source_doctype",
        default: opts.source_docname || "",
        get_query: () => {
          return {
            filters: {
              patient: opts.patient,
              appointment: opts.appointment,
            },
          };
        },
      },
      {
        fieldtype: "Column Break",
      },
      {
        fieldname: "service_name",
        fieldtype: "Data",
        label: __("Service Name"),
        default: opts.service_name || "",
      },
      {
        fieldtype: "Section Break",
        label: __("Consumable Items"),
      },
      {
        fieldname: "items",
        fieldtype: "Table",
        label: __("Items"),
        cannot_add_rows: false,
        in_place_edit: true,
        data: [],
        fields: _get_item_table_fields(is_insurance, opts.company),
      },
    ],

    primary_action_label: __("Create"),
    primary_action: (values) => {
      _handle_create(dialog, values, opts);
    },
  });

  _bind_item_events(dialog, opts);

  if (opts.patient && !opts.patient_name) {
    frappe.db.get_value("Patient", opts.patient, "patient_name", (r) => {
      if (r && r.patient_name) {
        dialog.set_value("patient_name", r.patient_name);
      }
    });
  }

  dialog.show();
  return dialog;
};

function _get_item_table_fields(is_insurance, company) {
  const fields = [
    {
      fieldname: "item_code",
      fieldtype: "Link",
      label: __("Item Code"),
      options: "Item",
      in_list_view: 1,
      reqd: 1,
      columns: 2,
      get_query: () => ({
        filters: { is_stock_item: 1, disabled: 0 },
      }),
    },
    {
      fieldname: "warehouse",
      fieldtype: "Link",
      label: __("Warehouse"),
      options: "Warehouse",
      in_list_view: 1,
      reqd: 1,
      columns: 2,
      get_query: () => {
        return {
          filters: {
            is_group: 0,
            company: company,
            warehouse_name: ["like", "%Pharmacy%"],
          },
        };
      },
    },
    {
      fieldname: "uom",
      fieldtype: "Link",
      label: __("UOM"),
      options: "UOM",
      read_only: 1,
    },
    {
      fieldname: "qty_requested",
      fieldtype: "Float",
      label: __("Qty"),
      in_list_view: 1,
      default: 1,
      columns: 1,
    },
    {
      fieldname: "rate",
      fieldtype: "Currency",
      label: __("Rate"),
      in_list_view: 1,
      read_only: 1,
      columns: 1,
    },
    {
      fieldname: "amount",
      fieldtype: "Currency",
      label: __("Amount"),
      in_list_view: 1,
      read_only: 1,
      columns: 1,
    },
    {
      fieldname: "percent_covered",
      fieldtype: "Percent",
      label: __("%Covered"),
      in_list_view: 1,
      default: 100,
      read_only: !is_insurance,
      hidden: !is_insurance,
      columns: 1,
    },
    {
      fieldname: "payment_type",
      fieldtype: "Select",
      label: __("Payment Type"),
      options: "\nCash\nInsurance",
      in_list_view: 1,
      columns: 1,
    },
    {
      fieldname: "is_billable",
      fieldtype: "Check",
      label: __("Billable"),
      in_list_view: 1,
      default: 1,
      columns: 1,
    },
    {
      fieldname: "item_name",
      fieldtype: "Data",
      label: __("Item Name"),
      read_only: 1,
      hidden: 1,
    },
    {
      fieldname: "is_stock_item",
      fieldtype: "Check",
      label: __("Stock Item"),
      read_only: 1,
      hidden: 1,
    },
    {
      fieldname: "price_list",
      fieldtype: "Data",
      label: __("Price List"),
      hidden: 1,
    },
    {
      fieldname: "insurance_subscription",
      fieldtype: "Data",
      label: __("Ins. Subscription"),
      hidden: 1,
    },
    {
      fieldname: "insurance_company",
      fieldtype: "Data",
      label: __("Ins. Company"),
      hidden: 1,
    },
    {
      fieldname: "insurance_coverage_plan",
      fieldtype: "Data",
      label: __("Coverage Plan"),
      hidden: 1,
    },
  ];
  return fields;
}

function _get_grid_row(grid, cdn) {
  // Reliable way to get dialog table GridRow object
  return grid.grid_rows.find((r) => r.doc.name === cdn) || null;
}

function _get_row_doc(grid, cdn) {
  const gr = _get_grid_row(grid, cdn);
  return gr ? gr.doc : null;
}

function _refresh_row(grid, cdn) {
  // grid.refresh() doesn't re-render cell values in dialog tables.
  // Individual GridRow.refresh() is required to update the visual display.
  const gr = _get_grid_row(grid, cdn);
  if (gr) gr.refresh();
}

function _bind_item_events(dialog, opts) {
  const is_insurance = opts.payment_type === "Insurance";
  const grid = dialog.fields_dict.items.grid;

  // Track previous item_code per row to detect changes
  const _prev_item_codes = {};

  // Set defaults when a new row is added.
  // Frappe's dialog grid calls on_add_row(row_idx) BEFORE grid.refresh(),
  // so we must set defaults on grid.df.data directly (not on grid_row.doc).
  dialog.fields_dict.items.df.on_add_row = function (row_idx) {
    const data_row = grid.df.data[row_idx - 1];
    if (!data_row) return;

    data_row.payment_type = is_insurance ? "Insurance" : "Cash";

    const default_wh = dialog.get_value("default_warehouse");
    if (default_wh) {
      data_row.warehouse = default_wh;
    }

    data_row.percent_covered = 100;

    if (is_insurance) {
      data_row.insurance_subscription = opts.insurance_subscription || "";
      data_row.insurance_company = opts.insurance_company || "";
      data_row.insurance_coverage_plan = opts.insurance_coverage_plan || "";
    }
  };

  // Set df.change callbacks on grid docfields.
  // Frappe's grid_row.make_control() (grid_row.js) checks df.change and
  // uses it as the control's change handler. This is called reliably for ALL
  // field types including Link fields (via awesomplete selection), unlike
  // DOM 'change' events which don't fire for programmatic value changes.
  const item_code_df = grid.docfields.find(
    (df) => df.fieldname === "item_code"
  );
  if (item_code_df) {
    item_code_df.change = function () {
      // 'this' is the control instance, this.doc is the row doc
      const field = this;
      const row = field.doc;
      if (!row) return;
      const cdn = row.name;
      const current_value = row.item_code || "";
      const prev_value = _prev_item_codes[cdn] || "";

      if (current_value && current_value !== prev_value) {
        _prev_item_codes[cdn] = current_value;
        _fetch_item_details(dialog, grid, row, cdn, opts);
      }
    };
  }

  // Handle qty_requested changes — recalculate amount
  const qty_df = grid.docfields.find((df) => df.fieldname === "qty_requested");
  if (qty_df) {
    qty_df.change = function () {
      const field = this;
      const row = field.doc;
      if (!row) return;

      const qty = flt(row.qty_requested) || 1;
      const rate = flt(row.rate);
      row.amount = qty * rate;

      const grid_row = _get_grid_row(grid, row.name);
      if (grid_row) grid_row.refresh();
      _recalculate_total(dialog);
    };
  }

  // Handle payment_type changes
  const payment_type_df = grid.docfields.find(
    (df) => df.fieldname === "payment_type"
  );
  if (payment_type_df) {
    payment_type_df.change = function () {
      const field = this;
      const row = field.doc;
      if (!row) return;

      if (row.payment_type === "Cash" && row.percent_covered !== 100) {
        row.percent_covered = 100;
      }

      if (row.item_code) {
        const cdn = row.name;
        _fetch_item_details(dialog, grid, row, cdn, opts);
      }

      const grid_row = _get_grid_row(grid, row.name);
      if (grid_row) grid_row.refresh();
    };
  }

  // Handle is_billable changes
  const is_billable_df = grid.docfields.find(
    (df) => df.fieldname === "is_billable"
  );
  if (is_billable_df) {
    is_billable_df.change = function () {
      const field = this;
      const row = field.doc;
      if (!row) return;

      const grid_row = _get_grid_row(grid, row.name);
      if (grid_row) grid_row.refresh();
    };
  }
}

function _fetch_item_details(dialog, grid, row, cdn, opts) {
  const payment_type =
    row.payment_type || dialog.get_value("payment_type") || "";

  frappe.call({
    method:
      "hms_tz.hms_tz.doctype.consumable_record.consumable_api.get_consumable_item_details",
    args: {
      item_code: row.item_code,
      company: dialog.get_value("company"),
      payment_type: payment_type,
      insurance_subscription: dialog.get_value("insurance_subscription") || "",
      insurance_company: dialog.get_value("insurance_company") || "",
      patient: dialog.get_value("patient"),
    },
    async: true,
    callback: (r) => {
      if (r.message) {
        const d = r.message;
        const current_row = _get_row_doc(grid, cdn);
        if (!current_row) return;

        current_row.item_name = d.item_name || "";
        current_row.uom = d.uom || "";
        current_row.is_stock_item = d.is_stock_item || 0;
        current_row.rate = flt(d.rate);
        current_row.price_list = d.price_list || "";

        if (!current_row.warehouse) {
          const default_wh = dialog.get_value("default_warehouse");
          if (default_wh) {
            current_row.warehouse = default_wh;
          }
        }

        const qty = flt(current_row.qty_requested) || 1;
        current_row.amount = qty * flt(current_row.rate);

        _refresh_row(grid, cdn);
        _recalculate_total(dialog);

        if (
          payment_type === "Insurance" &&
          opts.insurance_coverage_plan &&
          opts.insurance_company &&
          opts.insurance_company.includes("NHIF")
        ) {
          _fetch_coverage_percent(dialog, grid, current_row, cdn, opts);
        }

        if (d.error) {
          frappe.msgprint({
            title: __("Rate Lookup Warning"),
            message: d.error,
            indicator: "orange",
          });
        }
      }
    },
  });
}

function _fetch_coverage_percent(dialog, grid, row, cdn, opts) {
  frappe.call({
    method:
      "hms_tz.hms_tz.doctype.consumable_record.consumable_api.get_nhif_coverage_percent",
    args: {
      appointment: opts.appointment,
      company: opts.company,
      item_code: row.item_code,
      insurance_coverage_plan: opts.insurance_coverage_plan,
      insurance_company: opts.insurance_company,
      payment_type: row.payment_type,
    },
    async: true,
    callback: (r) => {
      if (r.message !== undefined) {
        const percent = flt(r.message);
        const current_row = _get_row_doc(grid, cdn);
        if (!current_row) return;

        current_row.percent_covered = percent;

        if (percent < 100 && percent > 0) {
          const remaining = 100 - percent;
          frappe.show_alert(
            {
              message: __(
                "Item <b>{0}</b> is covered at <b>{1}%</b>. " +
                  "Add another row for the remaining <b>{2}%</b> and set payment type to Cash.",
                [row.item_code, percent, remaining]
              ),
              indicator: "orange",
            },
            10
          );
        } else if (percent === 0) {
          current_row.payment_type = "Cash";
          frappe.show_alert(
            {
              message: __(
                "Item <b>{0}</b> is not covered by insurance. Payment type changed to Cash.",
                [row.item_code]
              ),
              indicator: "red",
            },
            7
          );
        }

        _refresh_row(grid, cdn);
      }
    },
  });
}

function _recalculate_total(dialog) {
  const items = dialog.fields_dict.items.grid.grid_rows.map((r) => r.doc);
  let total = 0;
  items.forEach((item) => {
    total += flt(item.amount);
  });
  dialog.set_value("total_amount", total);
}

function _handle_create(dialog, values, opts) {
  const items = dialog.fields_dict.items.grid.grid_rows.map((r) => r.doc);

  if (!items || items.length === 0) {
    frappe.msgprint(__("Please add at least one item."));
    return;
  }

  for (const item of items) {
    if (!item.item_code) {
      frappe.msgprint(__("Row {0}: Item Code is required.", [item.idx]));
      return;
    }
    if (!item.warehouse) {
      frappe.msgprint(__("Row {0}: Warehouse is required.", [item.idx]));
      return;
    }
    if (flt(item.qty_requested) <= 0) {
      frappe.msgprint(__("Row {0}: Qty must be greater than 0.", [item.idx]));
      return;
    }
  }

  // For cash patients — validate deposit first
  const payment_type = dialog.get_value("payment_type");
  if (payment_type === "Cash") {
    let cash_total = 0;
    items.forEach((item) => {
      if (item.payment_type === "Cash" || !item.payment_type) {
        cash_total += flt(item.amount);
      }
    });

    if (cash_total > 0) {
      frappe.call({
        method:
          "hms_tz.hms_tz.doctype.consumable_record.consumable_api.validate_patient_deposit",
        args: {
          patient: dialog.get_value("patient"),
          company: dialog.get_value("company"),
          appointment: opts.appointment || "",
          inpatient_record: opts.inpatient_record || "",
          total_amount: cash_total,
        },
        async: false,
        callback: (r) => {
          if (r.message && !r.message.has_sufficient_balance) {
            frappe.msgprint({
              title: __("Insufficient Deposit"),
              message: __(
                "Patient does not have sufficient deposit.<br>" +
                  "Required: <b>{0}</b><br>Available: <b>{1}</b><br>" +
                  "Please request the patient to deposit <b>{2}</b> more.",
                [
                  format_currency(cash_total),
                  format_currency(r.message.current_balance),
                  format_currency(r.message.required_amount),
                ]
              ),
              indicator: "red",
            });
            return;
          }
        },
      });
    }
  }

  // Build items payload
  const cleaned_items = items.map((item) => ({
    item_code: item.item_code,
    item_name: item.item_name,
    qty_requested: flt(item.qty_requested),
    warehouse: item.warehouse,
    rate: flt(item.rate),
    uom: item.uom,
    price_list: item.price_list,
    payment_type: item.payment_type || payment_type,
    percent_covered: flt(item.percent_covered) || 100,
    is_billable: item.is_billable ? 1 : 0,
    insurance_subscription: item.insurance_subscription || "",
    insurance_company: item.insurance_company || "",
    insurance_coverage_plan: item.insurance_coverage_plan || "",
  }));

  frappe.dom.freeze(__("Creating Consumable Record..."));

  frappe.call({
    method:
      "hms_tz.hms_tz.doctype.consumable_record.consumable_api.create_consumable_record",
    args: {
      args: JSON.stringify({
        patient: dialog.get_value("patient"),
        company: dialog.get_value("company"),
        appointment: opts.appointment || "",
        encounter: opts.encounter || "",
        payment_type: payment_type,
        insurance_subscription:
          dialog.get_value("insurance_subscription") || "",
        insurance_company: dialog.get_value("insurance_company") || "",
        insurance_coverage_plan:
          dialog.get_value("insurance_coverage_plan") || "",
        prescribed_by: opts.prescribed_by || "",
        source_doctype: opts.source_doctype || "",
        source_docname: opts.source_docname || "",
        items: cleaned_items,
      }),
    },
    callback: (r) => {
      frappe.dom.unfreeze();
      if (r.message) {
        frappe.show_alert(
          {
            message: r.message.message || __("Consumable Record created."),
            indicator: r.message.has_pending_payment ? "orange" : "green",
          },
          7
        );
        dialog.hide();
        if (opts.on_success) {
          opts.on_success(r.message);
        }
      }
    },
    error: () => {
      frappe.dom.unfreeze();
    },
  });
}
