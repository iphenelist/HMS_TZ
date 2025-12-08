frappe.ui.form.on("Lab Test", {
  setup: function (frm) {
    frm.get_field("normal_test_items").grid.editable_fields = [
      { fieldname: "lab_test_name", columns: 2 },
      { fieldname: "lab_test_event", columns: 2 },
      { fieldname: "result_value", columns: 2 },
      { fieldname: "lab_test_uom", columns: 1 },
      { fieldname: "detailed_normal_range", columns: 2 },
      { fieldname: "result_status", columns: 1 },
    ];
    frm.get_field("descriptive_test_items").grid.editable_fields = [
      { fieldname: "lab_test_particulars", columns: 3 },
      { fieldname: "result_component_option", columns: 4 },
      { fieldname: "result_value", columns: 4 },
    ];
    frm.set_query(
      "result_component_option",
      "descriptive_test_items",
      function (doc, cdt, cdn) {
        let d = locals[cdt][cdn];
        return {
          filters: [
            [
              "Result Component Option",
              "result_component",
              "=",
              d.lab_test_particulars,
            ],
          ],
        };
      }
    );
  },
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

    frappe.call({
      method: "hms_tz.nhif.nhif_api.approval.get_service_approval",
      args: {
        ref_doctype: frm.doctype,
        ref_docname: frm.docname,
        service_type: "Lab Test Template",
        service_name: frm.doc.template,
        qty: 1,
      },
      freeze: true,
      freeze_message: __('<i class="fa fa-spinner fa-spin fa-4x"></i>'),
      callback: function (r) {
        if (r.message) {
          frm.refresh();
          if (r.message.status == "success") {
            frm.save().then(() => {
              frm.reload_doc();
            });

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
            frm.save().then(() => {
              frm.reload_doc();
            });

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
          service_type: "Lab Test Template",
          service_name: frm.doc.template,
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
          frm.save().then(() => {
            frm.reload_doc();
          });
          
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
  get_poc_reference_no: async (frm) => {
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

    let biometricData;

    if (frm.doc.biometric_method === "FACIAL") {
      biometricData = await new FacialRecognition({ label: "Get POC Reference No" });
      if (!biometricData) {
        frappe.msgprint(__("Face capture failed. Please try again."));
        return;
      }
    } else if (frm.doc.biometric_method === "FINGERPRINT") {
      biometricData = await new Fingerprint({ label: "Get POC Reference No" });
      if (!biometricData) {
        frappe.msgprint(__("Fingerprint capture failed. Please try again."));
        return;
      }
    } else {
      const confirmed = await new Promise((resolve) => {
        frappe.confirm(
          __(`
            <div style="border-left: 4px solid #ffc107; background-color: #fff3cd; padding: 15px; border-radius: 10px; box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1); margin: 10px;">
              <p class="text-center"><i>Biometric Method: <b>${frm.doc.biometric_method}</b> is only used when Patient is not able to take fingerprint or face.</i></p>
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
      method: "hms_tz.nhif.utils.get_poc_reference_no_for_lrpmt",
      args: {
        ref_doctype: frm.doc.doctype,
        ref_docname: frm.doc.name,
        service_type: "Lab Test Template",
        service_name: frm.doc.template,
        fingerprint: biometricData.Data,
        fpcode: biometricData.fpCode,
        biometric_method: frm.doc.biometric_method,
      },
      freeze: true,
      freeze_message: __('<i class="fa fa-spinner fa-spin fa-4x"></i>'),
      callback: function (r) {
        if (r.message) {
          if (r.message) {
            frm.save().then(() => {
              frm.reload_doc();
            });
            
            frappe.utils.play_sound("submit");
          } else {
            frappe.utils.play_sound("error");
          }
        } else {
          frappe.utils.play_sound("error");
        }
      },
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

    let biometricData;

    if (frm.doc.biometric_method === "FACIAL") {
      biometricData = await new FacialRecognition({ label: "Issue Service" });
      if (!biometricData) {
        frappe.msgprint(__("Face capture failed. Please try again."));
        return;
      }
    } else if (frm.doc.biometric_method === "FINGERPRINT") {
      biometricData = await new Fingerprint({ label: "Issue Service" });
      if (!biometricData) {
        frappe.msgprint(__("Fingerprint capture failed. Please try again."));
        return;
      }
    } else {
      const confirmed = await new Promise((resolve) => {
        frappe.confirm(
          __(`
            <div style="border-left: 4px solid #ffc107; background-color: #fff3cd; padding: 15px; border-radius: 10px; box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1); margin: 10px;">
              <p class="text-center"><i>Biometric Method: <b>${frm.doc.biometric_method}</b> is only used when Patient is not able to take fingerprint or face.</i></p>
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
        service_type: "Lab Test Template",
        service_name: frm.doc.template,
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

frappe.ui.form.on("Normal Test Result", {
  result_value: function (frm, cdn, cdt) {
    if (!frm.doc.lab_test_name) {
      return;
    }
    const row = locals[cdn][cdt];
    const patient_age = get_patient_age(frm);
    frappe.call({
      method: "hms_tz.nhif.api.lab_test.get_normals",
      args: {
        lab_test_name: row.lab_test_name,
        patient_age: patient_age,
        patient_sex: frm.doc.patient_sex,
      },
      callback: function (data) {
        if (data.message) {
          const r = data.message;
          row.min_normal = r.min;
          row.max_normal = r.max;
          row.text_normal = r.text;
          const data_normals = calc_data_normals(r, row.result_value);
          row.detailed_normal_range = data_normals.detailed_normal_range;
          row.result_status = data_normals.result_status;
          frm.refresh_field("normal_test_items");
        }
      },
    });
  },
});

var calc_data_normals = function (data, value) {
  const result = {
    detailed_normal_range: "",
    result_status: "",
  };
  if (data.min && !data.max) {
    result.detailed_normal_range = "> " + data.min;
    if (value > data.min) {
      result.result_status = "N";
    } else {
      result.result_status = "L";
    }
  } else if (!data.min && data.max) {
    result.detailed_normal_range = "< " + data.max;
    if (value < data.max) {
      result.result_status = "N";
    } else {
      result.result_status = "H";
    }
  } else if (data.min && data.max) {
    result.detailed_normal_range = data.min + " - " + data.max;
    if (value > data.min && value < data.max) {
      result.result_status = "N";
    } else if (value < data.min) {
      result.result_status = "L";
    } else if (value > data.max) {
      result.result_status = "H";
    }
  }
  if (data.text) {
    if (result.detailed_normal_range) {
      result.detailed_normal_range += " / ";
    }
    result.detailed_normal_range += data.text;
  }
  return result;
};

var get_patient_age = function (frm) {
  var patient_age = 0;
  if (frm.doc.patient) {
    frappe.call({
      method: "hms_tz.hms_tz.doctype.patient.patient.get_patient_detail",
      args: { patient: frm.doc.patient },
      async: false,
      callback: function (data) {
        if (data.message.dob) {
          patient_age = calculate_age(data.message.dob);
        }
      },
    });
    return patient_age;
  }
};

var calculate_age = function (dob) {
  var ageMS = Date.parse(Date()) - Date.parse(dob);
  var age = new Date();
  age.setTime(ageMS);
  var years = age.getFullYear() - 1970;
  return years;
};
