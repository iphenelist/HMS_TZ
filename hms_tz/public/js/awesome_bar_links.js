/**
 * Register HMS TZ custom pages in the Frappe Awesome Bar.
 *
 * These pages live outside /app/ (served via website_route_rules at /frontend/),
 * so we use make_function_searchable with window.location.href to bypass
 * Frappe's default /app/ routing.
 */
frappe.search.utils.make_function_searchable(
  () => (window.location.href = "/frontend/nurse-roster"),
  "Nurse Roster"
);

frappe.search.utils.make_function_searchable(
  () => (window.location.href = "/frontend/ot-roster"),
  "OT Roster"
);
