// Copyright (c) 2026, Aakvatech Limited and contributors
// For license information, please see license.txt

frappe.listview_settings["Nursing Schedule"] = {
  onload: function (listview) {
    listview.page.add_inner_button(__("Open Roster"), function () {
      window.open("/frontend/nurse-roster");
    });
  },
};
