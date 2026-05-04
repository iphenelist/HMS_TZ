// Copyright (c) 2026, Aakvatech Limited and contributors
// For license information, please see license.txt

frappe.listview_settings["Nursing Schedule"] = {
  onload: function (listview) {
    // Remove default "+ Add Nursing Schedule" and replace with "Open Roster"
    listview.page.clear_primary_action();
    listview.page.set_primary_action(
      __("Open Roster"),
      function () {
        window.open("/frontend/nurse-roster");
      },
      "es-line-icon-externallink"
    );
  },

  refresh: function (listview) {
    // Re-apply on every refresh since Frappe may reset the primary action
    listview.page.clear_primary_action();
    listview.page.set_primary_action(
      __("Open Roster"),
      function () {
        window.open("/frontend/nurse-roster");
      },
      "es-line-icon-externallink"
    );
  },
};
