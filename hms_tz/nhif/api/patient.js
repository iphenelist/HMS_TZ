frappe.ui.form.on("Patient", {
  setup: function (frm) {},
  onload: function (frm) {
    frm.trigger("add_get_info_btn");
    frm.trigger("update_cash_limit");
    if (frm.is_new()) {
      frm.set_value("customer_group", "Patient");
    }
  },
  refresh: function (frm) {
    frm.trigger("add_get_info_btn");
    frm.trigger("update_cash_limit");
  },
  add_get_info_btn: function (frm) {
    frm.add_custom_button(__("Get Patient Info"), function () {
      if (frm.doc.card_no) {
        get_patient_info(frm, "card_no");
      } else if (frm.doc.national_id) {
        get_patient_info(frm, "national_id");
      }
    });
  },
  card_no: function (frm) {
    if (!frm.doc.insurance_provider) return;

    frm.fields_dict.card_no.$input.focusout(function () {
      get_patient_info(frm, "card_no");
      frm.set_df_property("card_no", "read_only", 1);
    });
  },
  national_id: function (frm) {
    if (!frm.doc.insurance_provider) return;

    frm.fields_dict.national_id.$input.focusout(function () {
      get_patient_info(frm, "national_id");
      frm.set_df_property("national_id", "read_only", 1);
    });
  },
  insurance_provider: function (frm) {
    if (
      frm.doc.card_no &&
      frm.doc.insurance_provider &&
      frm.doc.insurance_provider == "NHIF"
    ) {
      get_patient_info(frm, "card_no");
    } else if (
      frm.doc.national_id &&
      frm.doc.insurance_provider &&
      frm.doc.insurance_provider == "NHIF"
    ) {
      get_patient_info(frm, "national_id");
    }
  },
  mobile: function (frm) {
    frappe.call({
      method: "hms_tz.nhif.api.patient.validate_mobile_number",
      args: {
        doc_name: frm.doc.name,
        mobile: frm.doc.mobile,
      },
    });
  },
  update_cash_limit: function (frm) {
    if (frappe.user.has_role("Healthcare Administrator")) {
      frm
        .add_custom_button(__("Update Cash Limit"), function () {
          let d = new frappe.ui.Dialog({
            title: "Change Cash Limit",
            fields: [
              {
                fieldname: "current_cash_limit",
                fieldtype: "Currency",
                label: __("Current Cash Limit"),
                default: frm.doc.cash_limit,
                reqd: true,
              },
              {
                fieldname: "column_break_1",
                fieldtype: "Column Break",
              },
              {
                fieldname: "new_cash_limit",
                fieldtype: "Currency",
                label: "New Cash Limit",
                reqd: true,
              },
            ],
          });
          d.set_primary_action(__("Submit"), function () {
            if (d.get_value("new_cash_limit") == 0) {
              frappe.msgprint({
                title: "Notification",
                indicator: "red",
                message: __("<b>New cash limit cannot be zero</b>"),
              });
            } else {
              frappe
                .call("hms_tz.nhif.api.patient.enqueue_update_cash_limit", {
                  old_cash_limit: d.get_value("current_cash_limit"),
                  new_cash_limit: d.get_value("new_cash_limit"),
                })
                .then((r) => {
                  frappe.show_alert(__("Processing patient's cash limit"));
                });
              d.hide();
            }
          });
          d.show();
        })
        .removeClass("btn-default")
        .addClass("btn-info font-weight-bold text-dark");
    }
  },
});

async function get_patient_info(frm, caller) {
  if (frm.doc.card_no_trigger) return;
  if (frm.doc.national_id_trigger) return;

  if (
    (!frm.doc.card_no && !frm.doc.national_id) ||
    !frm.doc.insurance_provider
  )
    return;

  let card_exists = false;
  let national_id_exists = false;

  if (frm.doc.card_no) {
    await frappe.call({
      method: "hms_tz.nhif.api.patient.check_card_number",
      args: {
        card_no: frm.doc.card_no,
        is_new: frm.is_new(),
        patient: frm.doc.name,
      },
      freeze: true,
      freeze_message: __('<i class="fa fa-spinner fa-spin fa-4x"></i>'),
      callback: function (data) {
        if (data.message) {
          frappe.msgprint(`Card number used with patient ${data.message}`);
          frappe.set_route("Form", "Patient", data.message);
          card_exists = true;
          return;
        }
      },
    });
  }

  if (frm.doc.national_id) {
    await frappe.call({
      method: "hms_tz.nhif.api.patient.check_national_id",
      args: {
        national_id: frm.doc.national_id,
        is_new: frm.is_new(),
        patient: frm.doc.name,
      },
      freeze: true,
      freeze_message: __('<i class="fa fa-spinner fa-spin fa-4x"></i>'),
      callback: function (data) {
        if (data.message) {
          frappe.msgprint(`National ID used with patient ${data.message}`);
          frappe.set_route("Form", "Patient", data.message);
          national_id_exists = true;
          return;
        }
      },
    });
  }

  if (card_exists || national_id_exists) return;

  if (frm.doc.insurance_provider && (frm.doc.card_no || frm.doc.national_id)) {
    if (frm.doc.insurance_provider == "NHIF") {
      get_nhif_patient_info(frm, caller);
    }
  }
}

function get_nhif_patient_info(frm, caller) {
  let args = {};

  if (caller === "card_no") {
    args["card_no"] = frm.doc.card_no;
  } else if (caller === "national_id") {
    args["national_id"] = frm.doc.national_id;
  }
  args["ref_doctype"] = frm.doc.doctype;

  if (!frm.is_new()) {
    args["ref_docname"] = frm.doc.name;
  }

  frappe.call({
    method: "hms_tz.nhif.api.patient.get_nhif_patient_info",
    args: args,
    freeze: true,
    freeze_message: __('<i class="fa fa-spinner fa-spin fa-4x"></i>'),
    callback: function (data) {
      if (data.message && data.message !== "Error") {
        frappe.utils.play_sound("submit");

        const patient_data = data.message;
        if (!frm.is_new()) {
          show_nhif_patient_dialog(frm, patient_data);
        } else {
          update_nhif_patient_info(frm, patient_data);
        }
      } else {
        frappe.utils.play_sound("error");
        frappe.show_alert(
          {
            message: __("Failed to get patient's information"),
            indicator: "red",
          },
          10
        );
      }
    },
    onerror: function (data) {
      frappe.utils.play_sound("error");
      frappe.show_alert(
        {
          message: __("Failed to get patient's information"),
          indicator: "red",
        },
        10
      );
    },
  });
}

function show_nhif_patient_dialog(frm, patient_data) {
  const d = new frappe.ui.Dialog({
    title: "Patient's information",
    size: "large",
    primary_action_label: "Save",
    primary_action(values) {
      update_nhif_patient_info(frm, patient_data);
      d.hide();
    },
  });
  $(`<div class="modal-body ui-front">
        <table class="table table-bordered">
        <colgroup>
            <col style="width: 30%">
            <col style="width: 35%">
            <col style="width: 35%">
        </colgroup>
        <thead>
            <tr>
                <th>Field Name</th>
                <th>Current Values</th>
                <th>New Values</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>First Name</td>
                <td>${frm.doc.first_name}</td>
                <td>${patient_data.FirstName}</td>
            </tr>
            <tr>
                <td>Last Name</td>
                <td>${frm.doc.middle_name}</td>
                <td>${patient_data.MiddleName}</td>
            </tr>
            <tr>
                <td>Last Name</td>
                <td>${frm.doc.last_name}</td>
                <td>${patient_data.LastName}</td>
            </tr>
            <tr>
                <td>Full Name</td>
                <td>${frm.doc.patient_name}</td>
                <td>${patient_data.FullName}</td>
            </tr>
            <tr>
                <td>Gender</td>
                <td>${frm.doc.sex}</td>
                <td>${patient_data.Gender}</td>
            </tr>
             <tr>
                <td>Date of birth</td>
                <td>${frm.doc.dob}</td>
                <td>${patient_data.DateOfBirth.slice(0, 10)}</td>
            </tr>
             <tr>
                <td>National ID</td>
                <td>${frm.doc.national_id}</td>
                <td>${patient_data.CHNationalID}</td>
            </tr>
            <tr>
                <td>Membership No</td>
                <td>${frm.doc.membership_no}</td>
                <td>${patient_data.MembershipNo}</td>
            </tr>
            <tr>
                <td>Product Code</td>
                <td>${frm.doc.product_code}</td>
                <td>${patient_data.ProductCode}</td>
            </tr>
            <tr>
                <td>Scheme ID</td>
                <td>${frm.doc.scheme_id}</td>
                <td>${patient_data.SchemeID}</td>
            </tr>
            <tr>
                <td>Member Picture</td>
                <td><img src="${
                  frm.doc.image
                }" alt="Current Image" style="width: 100px; height: 100px;" /></td>
                <td><img src="${
                  patient_data.MemberPicture
                }" alt="New Image" style="width: 100px; height: 100px;" /></td>
            </tr>
        </tbody>
        </table>
    </div>`).appendTo(d.body);
  d.show();
}

function update_nhif_patient_info(frm, patient_data) {
  frm.set_value("first_name", patient_data.FirstName);
  frm.set_value("middle_name", patient_data.MiddleName);
  frm.set_value("last_name", patient_data.LastName);
  frm.set_value("patient_name", patient_data.FullName);
  frm.set_value("sex", patient_data.Gender);
  frm.set_value("dob", new Date(patient_data.DateOfBirth));
  frm.set_value("product_code", patient_data.ProductCode);
  frm.set_value("scheme_id", patient_data.SchemeID);
  frm.set_value("nhif_employername", patient_data.EmployerName);
  frm.set_value("membership_no", patient_data.MembershipNo);
  frm.set_value("image", patient_data.MemberPicture);

  frm.doc.card_no_trigger = true;
  frm.doc.national_id_trigger = true;

  if (!frm.doc.card_no) {
    frm.set_value("card_no", patient_data.CardNo);
  }

  if (!frm.doc.national_id) {
    frm.set_value("national_id", patient_data.CHNationalID);
  }

  frm.save();
  frappe.show_alert(
    {
      message: __("Patient's information is updated"),
      indicator: "green",
    },
    10
  );
}
