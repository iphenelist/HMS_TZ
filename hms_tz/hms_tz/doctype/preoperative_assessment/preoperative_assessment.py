# Copyright (c) 2026, Aakvatech and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class PreoperativeAssessment(Document):
    def before_save(self):
        self.set_missing_values()
        self.validate_clearance_checks()

    def set_missing_values(self):
        """Auto-set fields from OT Schedule → Clinical Procedure → Appointment chain."""
        # Set clinical_procedure and service_name from OT Schedule
        if self.ot_schedule:
            ot_details = frappe.db.get_value(
                "OT Schedule",
                self.ot_schedule,
                ["clinical_procedure", "procedure_template", "patient", "company"],
                as_dict=True,
            )
            if ot_details:
                if not self.patient and ot_details.patient:
                    self.patient = ot_details.patient
                if not self.company and ot_details.company:
                    self.company = ot_details.company
                if not self.clinical_procedure and ot_details.clinical_procedure:
                    self.clinical_procedure = ot_details.clinical_procedure
                if not self.service_name and ot_details.procedure_template:
                    self.service_name = ot_details.procedure_template

        # Fetch appointment from Clinical Procedure (if available)
        if self.clinical_procedure and not self.appointment:
            appointment = frappe.db.get_value(
                "Clinical Procedure", self.clinical_procedure, "appointment"
            )
            if appointment:
                self.appointment = appointment

        # Set inpatient_record from patient
        if self.patient and not self.inpatient_record:
            self.inpatient_record = frappe.db.get_value(
                "Patient", self.patient, "inpatient_record"
            )

        # Set insurance fields from appointment
        if self.appointment and not self.payment_type:
            appt_details = frappe.db.get_value(
                "Patient Appointment",
                self.appointment,
                [
                    "insurance_subscription",
                    "coverage_plan_name",
                    "insurance_company",
                ],
                as_dict=True,
            )
            if appt_details and appt_details.insurance_company:
                self.payment_type = "Insurance"
                self.insurance_subscription = appt_details.insurance_subscription
                self.insurance_coverage_plan = appt_details.coverage_plan_name
                self.insurance_company = appt_details.insurance_company
            else:
                self.payment_type = "Cash"

        # Clear insurance fields for cash patients
        if self.payment_type == "Cash" and self.insurance_subscription:
            self.insurance_subscription = ""
            self.insurance_coverage_plan = ""
            self.insurance_company = ""

    def validate_clearance_checks(self):
        """Warn if marking as Cleared without all checks complete."""
        if self.status != "Cleared for Surgery":
            return

        required_checks = [
            "fasting_status_verified",
            "consent_signed",
            "site_marking_verified",
        ]

        missing = []
        for check in required_checks:
            if not self.get(check):
                missing.append(frappe.unscrub(check))

        if missing:
            frappe.throw(
                _("Cannot mark as 'Cleared for Surgery'. The following checks are incomplete: {0}").format(
                    ", ".join(missing)
                )
            )
