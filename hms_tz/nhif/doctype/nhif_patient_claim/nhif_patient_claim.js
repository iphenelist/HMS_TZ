// Copyright (c) 2020, Aakvatech and contributors
// For license information, please see license.txt

frappe.ui.form.on("NHIF Patient Claim", {
  setup: function (frm) {
    frm.set_query("patient_appointment", function () {
      return {
        filters: {
          nhif_patient_claim: ["in", ["", "None"]],
          insurance_company: ["like", "NHIF%"],
          insurance_subscription: ["not in", ["", "None"]],
        },
      };
    });
  },

  refresh(frm) {
    $("[data-action='delete_all_rows']").hide();

    if (frm.doc.docstatus === 0 && frm.doc.authorization_no) {
      frm.add_custom_button(__("Re-concile Repeated Items"), () => {
        frappe
          .call({
            method:
              "hms_tz.nhif.doctype.nhif_patient_claim.nhif_patient_claim.reconcile_repeated_items",
            args: {
              claim_no: frm.doc.name,
            },
            freeze: true,
            freeze_message: __('<i class="fa fa-spinner fa-spin fa-4x"></i>'),
          })
          .then((r) => {
            if (r.message) {
              frm.refresh();
            }
          });
      });

      frm.add_custom_button(__("Merge Claims"), function () {
        const original_practitioner_name = frm.doc.practitioner_name;
        frm.dirty();
        frm
          .call("get_appointments", {
            self: frm.doc,
            freeze: true,
            freeze_message: __('<i class="fa fa-spinner fa-spin fa-4x"></i>'),
          })
          .then((r) => {
            frm.doc.practitioner_name = original_practitioner_name;
            frm.save();
            frm.refresh();
          });
      });
    }
  },

  onload: function (frm) {
    $("[data-action='delete_all_rows']").hide();
    if (frm.doc.patient && frm.doc.patient_appointment) {
      frappe.db
        .get_list("LRPMT Returns", {
          fields: ["name"],
          filters: {
            patient: frm.doc.patient,
            appointment: frm.doc.patient_appointment,
            docstatus: 1,
          },
        })
        .then((data) => {
          if (data.length > 0) {
            let msg_lrpmt = ``;
            data.forEach((element) => {
              msg_lrpmt += `${__(element.name)} ,`;
            });

            frappe.msgprint({
              title: __("Notification"),
              indicator: "orange",
              message: __(`
							<p class='text-left'>This Patient: <b>${__(
                frm.doc.patient
              )}</b> of appointment No: <b>${__(
                frm.doc.patient_appointment
              )}</b>
							having some item(s) cancelled or some quantity of item(s) returned to stock, by <b>${__(
                msg_lrpmt
              )}</b>,
							inorder for items and their quantities to be reflected on this claim</p>
							<p class='text-center' style='background-color: #FFA500; font-size: 14px;'>
							<strong><em><i>Tick allow changes, then Untick allow changes and Save again</i></em></strong></p>
							`),
            });
          }
        });
    }
  },

  after_save: (frm) => {
    // if (!frm.doc.allow_changes) {
    // frm.reload_doc().then(() => {
    //   if (frm.doc.docstatus === 0 && frm.doc.authorization_no && !frm.doc.folio_signed) {
    //     show_signature_method_dialog(frm);
    //   }
    // });
    // }
  },

  is_ready_for_auto_submission: (frm) => {
    if (frm.doc.is_ready_for_auto_submission == 1) {
      frm.set_value("reviewed_by", frappe.user.full_name());
    } else {
      frm.set_value("reviewed_by", "");
    }
  },

  send_confirmation_code: (frm) => {
    frappe
      .call({
        method: "hms_tz.nhif.nhif_api.patient_claim.send_confirmation_code",
        args: {
          ref_doctype: frm.doc.doctype,
          ref_docname: frm.doc.name,
        },
        freeze: true,
        freeze_message: __('<i class="fa fa-spinner fa-spin fa-4x"></i>'),
      })
      .then((r) => {
        if (r.message) {
          frm.reload_doc();
        }
      });
  },

  get_receipt: (frm) => {
    frappe.call({
      method: "hms_tz.nhif.nhif_api.patient_claim.get_receipt",
      args: {
        ref_doctype: frm.doc.doctype,
        ref_docname: frm.doc.name,
      },
      freeze: true,
      freeze_message: __('<i class="fa fa-spinner fa-spin fa-4x"></i>'),
      callback: function (r) {
        if (r.message) {
          frm.reload_doc();
        }
      },
    });
  },

  // sign_folio: (frm) => {
  //   if (frm.doc.docstatus === 0 && frm.doc.authorization_no && !frm.doc.folio_signed) {
  //     show_signature_method_dialog(frm);
  //   }
  // },
});

/**
 * Show dialog to choose signature method (Signature or Fingerprint)
 */
function show_signature_method_dialog(frm) {
  const dialog = new frappe.ui.Dialog({
    title: __("Sign Folio:"),
    fields: [
      {
        fieldtype: "HTML",
        fieldname: "info_html",
        options: `
          <div style="text-align: center; padding: 20px;">
            <p style="font-size: 14px; margin-bottom: 20px;">
              ${__("Please select the signature method")}
            </p>
            <div style="display: flex; justify-content: center; gap: 30px; flex-wrap: wrap;">
              <div class="signature-option" data-method="signature" 
                   style="cursor: pointer; padding: 20px; border: 2px solid #ccc; border-radius: 10px; width: 150px; text-align: center; transition: all 0.3s;">
                <i class="fa fa-pencil" style="font-size: 48px; color: #5e64ff;"></i>
                <p style="margin-top: 10px; font-weight: bold;">${__("Signature")}</p>
                <small>${__("Draw signature with pen")}</small>
              </div>
              <div class="signature-option" data-method="fingerprint"
                   style="cursor: pointer; padding: 20px; border: 2px solid #ccc; border-radius: 10px; width: 150px; text-align: center; transition: all 0.3s;">
                <i class="fa fa-hand-paper-o" style="font-size: 48px; color: #28a745;"></i>
                <p style="margin-top: 10px; font-weight: bold;">${__("Fingerprint")}</p>
                <small>${__("Use fingerprint device")}</small>
              </div>
            </div>
          </div>
        `,
      },
    ],
    size: "small",
    secondary_action_label: __("Cancel"),
    secondary_action: () => dialog.hide(),
  });

  dialog.show();

  // Add hover effects and click handlers
  dialog.$wrapper.find(".signature-option").hover(
    function () {
      $(this).css({
        "border-color": "#5e64ff",
        "background-color": "#f0f4ff",
      });
    },
    function () {
      $(this).css({
        "border-color": "#ccc",
        "background-color": "transparent",
      });
    }
  );

  dialog.$wrapper.find(".signature-option").on("click", function () {
    const method = $(this).data("method");
    dialog.hide();

    if (method === "signature") {
      capture_signature_and_sign(frm);
    } else if (method === "fingerprint") {
      capture_fingerprint_and_sign(frm);
    }
  });
}

/**
 * Capture handwritten signature using the Signature class and sign folio
 */
async function capture_signature_and_sign(frm) {
  try {
    const signature = await new Signature({ 
      label: __("Sign Folio"),
      title: __("Sign Folio - Draw Signature"),
    });
    
    if (!signature) {
      frappe.msgprint(__("Signature failed, please try again."))
      return;
    }

    frappe.call({
      method: "hms_tz.nhif.nhif_api.patient_claim.sign_folio",
      args: {
        ref_doctype: frm.doc.doctype,
        ref_docname: frm.doc.name,
        signature_method: "signature",
        signature: signature.Data,
      },
      freeze: true,
      freeze_message: __('<i class="fa fa-spinner fa-spin fa-4x"></i>'),
      callback: function (r) {
        if (r.message && r.message !== "Error") {
          frappe.utils.play_sound("submit");
          // frappe.show_alert({
          //   message: __("Folio signed successfully!"),
          //   indicator: "green",
          // });
          frm.reload_doc();
        } else {
          frappe.utils.play_sound("error");
        }
      },
    });
  } catch (error) {
    console.error("Signature capture error:", error);
    frappe.msgprint(__("Signature capture failed. Please try again."));
  }
}

/**
 * Capture fingerprint and sign folio
 */
async function capture_fingerprint_and_sign(frm) {
  try {
    let fingerprint = await new Fingerprint({ label: "Sign Folio" });
    if (!fingerprint) {
      frappe.msgprint(__("Fingerprint capture failed. Please try again."));
      return;
    }

    frappe.call({
      method: "hms_tz.nhif.nhif_api.patient_claim.sign_folio",
      args: {
        ref_doctype: frm.doc.doctype,
        ref_docname: frm.doc.name,
        signature_method: "fingerprint",
        fingerprint: fingerprint.Data,
        fpcode: fingerprint.fpCode,
      },
      freeze: true,
      freeze_message: __('<i class="fa fa-spinner fa-spin fa-4x"></i>'),
      callback: function (r) {
        if (r.message && r.message !== "Error") {
          frappe.utils.play_sound("submit");
          // frappe.show_alert({
          //   message: __("Folio signed successfully with fingerprint!"),
          //   indicator: "green",
          // });
          frm.reload_doc();
        } else {
          frappe.utils.play_sound("error");
        }
      },
    });
  } catch (error) {
    console.error("Fingerprint capture error:", error);
    frappe.msgprint(__("Fingerprint capture failed. Please try again."));
  }
}
