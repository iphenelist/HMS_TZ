frappe.ui.form.on("Radiology Examination", {
  refresh: (frm) => {
    $('[data-label="Not%20Serviced"]').parent().hide();
  },
  onload: (frm) => {
    $('[data-label="Not%20Serviced"]').parent().hide();
    if (frm.doc.patient) {
      frm.add_custom_button(__("Patient History"), function () {
        frappe.route_options = { patient: frm.doc.patient };
        frappe.set_route("tz-patient-history");
      });
    }
  },
  request_approval_no: (frm) => {
    if (
      !frm.doc.insurance_company ||
      !frm.doc.insurance_company.includes("NHIF")
    ) {
      frappe.show_alert(
        {
          message: __("This feature is only applicable for NHIF insurance"),
          indicator: "orange",
        },
        5
      );
      return;
    }

    if (!frm.doc.insurance_subscription) {
      frappe.msgprint(
        "Insurance Subscription is required to request approval"
      );
      return;
    }

    if (frm.is_dirty()) {
      frappe.msgprint("Please save the document before requesting approval");
      return;
    }

    frappe.call({
      method: "hms_tz.nhif.nhif_api.approval.get_service_approval",
      args: {
        ref_doctype: frm.doctype,
        ref_docname: frm.docname,
        service_type: "Radiology Examination Template",
        service_name: frm.doc.radiology_examination_template,
        qty: 1,
      },
      freeze: true,
      freeze_message: __('<i class="fa fa-spinner fa-spin fa-4x"></i>'),
      callback: function (r) {
        if (r.message) {
          frm.refresh();
          if (r.message.status == "success") {
            frappe.show_alert(
              {
                message: __(
                  "<h4 class='text-center' style='background-color: #D3D3D3; font-weight: bold;'>\
                                Approval Request Successful. Reference Number: " +
                    r.message.reference_no +
                    "</h4>"
                ),
                indicator: "green",
              },
              15
            );
            frappe.utils.play_sound("submit");
          } else {
            frappe.show_alert(
              {
                message: __(
                  "<h4 class='text-center' style='background-color: #D3D3D3; font-weight: bold;'>\
                                Approval Request Failed: </h4>"
                ),
                indicator: "red",
              },
              20
            );
            frappe.utils.play_sound("error");
          }
        } else {
          frappe.utils.play_sound("error");
        }
      },
    });
  },
  get_approval_status: (frm) => {
    if (
      !frm.doc.insurance_company ||
      !frm.doc.insurance_company.includes("NHIF")
    ) {
      frappe.show_alert(
        {
          message: __("This feature is only applicable for NHIF insurance"),
          indicator: "orange",
        },
        5
      );
      return;
    }

    if (frm.is_dirty()) {
      frappe.msgprint(
        "Please save the document before requesting approval status"
      );
      return;
    }

    frappe.call({
      method: "hms_tz.nhif.nhif_api.approval.get_approval_status",
      args: {
        ref_doctype: frm.doctype,
        ref_docname: frm.docname,
      },
      freeze: true,
      freeze_message: __('<i class="fa fa-spinner fa-spin fa-4x"></i>'),
      callback: function (r) {
        if (r.message) {
          frm.refresh();
          if (r.message.status == "success") {
            frappe.show_alert(
              {
                message: __(
                  "<h4 class='text-center' style='background-color: #D3D3D3; font-weight: bold;'>\
                                Request Approval Status Successful. Reference Number: " +
                    r.message.reference_no +
                    "</h4>"
                ),
                indicator: "green",
              },
              15
            );
            frappe.utils.play_sound("submit");
          } else {
            frappe.show_alert(
              {
                message: __(
                  "<h4 class='text-center' style='background-color: #D3D3D3; font-weight: bold;'>\
                                Request Approval Status Failed: </h4>"
                ),
                indicator: "red",
              },
              20
            );
            frappe.utils.play_sound("error");
          }
        } else {
          frappe.utils.play_sound("error");
        }
      },
    });
  },
  verify_approval_no: (frm) => {
    if (!frm.doc.insurance_company.includes("NHIF")) {
      frappe.show_alert(
        {
          message: __("This feature is only applicable for NHIF insurance"),
          indicator: "orange",
        },
        5
      );
      return;
    }
    if (!frm.doc.approval_number) {
      frappe.msgprint("Approval Number is required to verify");
      return;
    }
    frappe
      .call({
        method: "hms_tz.nhif.nhif_api.approval.verify_approval_number",
        args: {
          company: frm.doc.company,
          approval_number: frm.doc.approval_number,
          service_type: "Radiology Examination Template",
          service_name: frm.doc.radiology_examination_template,
          appointment: frm.doc.appointment,
          ref_doctype: frm.doctype,
          ref_docname: frm.docname,
        },
        freeze: true,
        freeze_message: __('<i class="fa fa-spinner fa-spin fa-4x"></i>'),
      })
      .then((r) => {
        if (
          r.message &&
          r.message == "approval number validation is disabled"
        ) {
          frappe.utils.play_sound("error");
          return;
        } else if (r.message) {
          frappe.utils.play_sound("submit");
          frappe.show_alert(
            {
              message: __(
                "<h4 class='text-center' style='background-color: #D3D3D3; font-weight: bold;'>\
                        Approval Number is Valid</h4>"
              ),
              indicator: "green",
            },
            20
          );
        } else {
          frappe.utils.play_sound("error");
          frm.set_value("approval_number", "");
          frappe.show_alert(
            {
              message: __(
                "<h4 class='text-center' style='background-color: #D3D3D3; font-weight: bold;'>\
                        Approval Number is not Valid</h4>"
              ),
              indicator: "Red",
            },
            20
          );
        }
      });
  },
  issue_service: async (frm) => {
    if (!frm.doc.insurance_company.includes("NHIF")) {
      frappe.show_alert(
        {
          message: __("This feature is only applicable for NHIF insurance"),
          indicator: "orange",
        },
        5
      );
      return;
    }
    if (frm.doc.is_restricted == 1 && !frm.doc.approval_number) {
      frappe.msgprint("Approval Number is required to issue approved service");
      return;
    }

    if (frm.is_dirty()) {
      frappe.msgprint("Please save the document before issuing approved service");
      return;
    }

    let biometricData;

    if (frm.doc.biometric_method === "Facial Recognition") {
      biometricData = await new FacialRecognition({ label: "Issue Service" });
      if (!biometricData) {
        frappe.msgprint(__("Fingerprint capture failed. Please try again."));
        return;
      }
    } else if (frm.doc.biometric_method === "Fingerprint") {
      biometricData = await new dpFingerprint({ label: "Issue Service" });
      if (!biometricData) {
        frappe.msgprint(__("Fingerprint capture failed. Please try again."));
        return;
      }
    } else {
      const confirmed = await new Promise((resolve) => {
        frappe.confirm(
          __(`
            <div style="border-left: 4px solid #ffc107; background-color: #fff3cd; padding: 15px; border-radius: 10px; box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1); margin: 10px;">
              <p class="text-center"><i>Biometric Method: <b>${frm.doc.biometric_method}</b> is only used when Patient is not able to take fingerprint or facial recognition.</i></p>
            </div>
            <br>
            <p class="text-center"><i>Are you sure you want to continue?</i></p>`
          ),
          () => resolve(true),
          () => resolve(false)
        );
      });
      
      if (!confirmed) {
        return;
      }

      biometricData = {Data: "", fpCode: ""};
    }

    frappe.call({
      method: "hms_tz.nhif.utils.issue_nhif_service",
      args: {
        ref_doctype: frm.doc.doctype,
        ref_docname: frm.doc.name,
        service_type: "Radiology Examination Template",
        service_name: frm.doc.radiology_examination_template,
        fingerprint: biometricData.Data,
        fpcode: biometricData.fpCode,
        biometric_method: frm.doc.biometric_method,
      },
      freeze: true,
      freeze_message: __('<i class="fa fa-spinner fa-spin fa-4x"></i>'),
      callback: function (r) {
        if (r.message) {
          if (r.message) {
            frappe.utils.play_sound("submit");
            let data = r.message;
            if (data.ReferenceNo) {
              frm.set_value("poc_reference_no", data.ReferenceNo);
              frm.save().then(() => {
                frm.reload_doc();
              });
            } else {
              frappe.utils.play_sound("error");
            }
          }
        } else {
          frappe.utils.play_sound("error");
        }
      },
    });
  },
});
