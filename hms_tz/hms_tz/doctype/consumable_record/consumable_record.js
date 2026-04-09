// Copyright (c) 2026, Aakvatech and contributors
// For license information, please see license.txt

frappe.ui.form.on("Consumable Record", {
  setup(frm) {
    frm.set_query("prescribed_by", () => ({
      filters: { practitioner_role: "Doctor" },
    }));
    frm.set_query("patient", () => ({
      filters: { status: "Active" },
    }));
  },

  refresh(frm) {
    if (frm.doc.docstatus === 1 && frm.doc.status === "Dispensed") {
      frm.add_custom_button(
        __("Finalize"),
        () => {
          frappe.confirm(
            __("Mark all items as used and finalize this record?"),
            () => {
              frm.call("update_status", { status: "Finalized" }).then(() => {
                frm.reload_doc();
              });
            }
          );
        },
        __("Actions")
      );
    }
  },

  patient(frm) {
    if (frm.doc.patient) {
      frappe.db.get_value(
        "Patient",
        frm.doc.patient,
        "inpatient_record",
        (r) => {
          if (r && r.inpatient_record) {
            frm.set_value("inpatient_record", r.inpatient_record);
          }
        }
      );
    }
  },
});

frappe.ui.form.on("Consumable Item", {
  item_code(frm, cdt, cdn) {
    let row = frappe.get_doc(cdt, cdn);
    if (row.item_code && frm.doc.company) {
      frappe.call({
        method: "frappe.client.get_value",
        args: {
          doctype: "Item Price",
          filters: {
            item_code: row.item_code,
            price_list: row.price_list || "Standard Selling",
            selling: 1,
          },
          fieldname: "price_list_rate",
        },
        callback(r) {
          if (r.message && r.message.price_list_rate) {
            frappe.model.set_value(
              cdt,
              cdn,
              "rate",
              r.message.price_list_rate
            );
          }
        },
      });
    }
  },

  qty_requested(frm, cdt, cdn) {
    calculate_row_amount(frm, cdt, cdn);
  },

  rate(frm, cdt, cdn) {
    calculate_row_amount(frm, cdt, cdn);
  },

  qty_used(frm, cdt, cdn) {
    calculate_row_amount(frm, cdt, cdn);
  },
});

function calculate_row_amount(frm, cdt, cdn) {
  let row = frappe.get_doc(cdt, cdn);
  let qty = row.qty_used || row.qty_dispensed || row.qty_requested || 0;
  frappe.model.set_value(cdt, cdn, "amount", flt(qty) * flt(row.rate));
  calculate_total(frm);
}

function calculate_total(frm) {
  let total = 0;
  (frm.doc.items || []).forEach((row) => {
    total += flt(row.amount);
  });
  frm.set_value("total_amount", total);
}
