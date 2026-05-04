// Copyright (c) 2026, Aakvatech and contributors
// For license information, please see license.txt

frappe.listview_settings["OT Schedule"] = {
  onload: function (listview) {
    listview.page.clear_primary_action();
    listview.page.set_primary_action(
      __("Open Roster"),
      function () {
        window.open("/frontend/ot-roster");
      },
      "es-line-icon-externallink"
    );
  },

  refresh: function (listview) {
    listview.page.clear_primary_action();
    listview.page.set_primary_action(
      __("Open Roster"),
      function () {
        window.open("/frontend/ot-roster");
      },
      "es-line-icon-externallink"
    );
  },

  get_indicator(doc) {
    const status_map = {
      Scheduled: [__("Scheduled"), "blue"],
      "In Progress": [__("In Progress"), "orange"],
      Completed: [__("Completed"), "green"],
      Cancelled: [__("Cancelled"), "red"],
      Postponed: [__("Postponed"), "gray"],
    };
    const s = status_map[doc.status];
    return s ? [s[0], s[1], `status,=,${doc.status}`] : null;
  },
};
