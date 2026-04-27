// Copyright (c) 2025, Aakvatech and contributors
// For license information, please see license.txt

frappe.ui.form.on("Jubilee Service Request", {
  refresh: function (frm) {
    // Show status indicator on the dashboard
    if (frm.doc.preauth_status === "OK") {
      frm.dashboard.set_headline(
        __(
          '<span class="indicator whitespace-nowrap green">' +
            "Pre-Authorization Submitted Successfully — Submission ID: " +
            frm.doc.submission_id +
            "</span>"
        )
      );
    } else if (frm.doc.preauth_status === "ERROR") {
      frm.dashboard.set_headline(
        __(
          '<span class="indicator whitespace-nowrap red">' +
            "Pre-Authorization Failed: " +
            frm.doc.preauth_description +
            "</span>"
        )
      );
    }
  },
});
