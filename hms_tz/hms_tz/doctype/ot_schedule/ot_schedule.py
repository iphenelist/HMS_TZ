# Copyright (c) 2026, Aakvatech and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class OTSchedule(Document):
    def before_save(self):
        self.validate_schedule_conflict()

    def validate_schedule_conflict(self):
        """Check for time conflicts in the same theater room on the same date."""
        if not self.theater_room or not self.date or not self.start_time:
            return

        filters = {
            "theater_room": self.theater_room,
            "date": self.date,
            "status": ["not in", ["Cancelled", "Postponed"]],
            "name": ["!=", self.name],
        }

        existing = frappe.get_all(
            "OT Schedule",
            filters=filters,
            fields=["name", "start_time", "end_time", "estimated_duration", "patient_name"],
        )

        for schedule in existing:
            if self._has_time_overlap(schedule):
                frappe.throw(
                    _(
                        "Time conflict with {0} (Patient: {1}) in {2} on {3}. "
                        "Please choose a different time or theater."
                    ).format(
                        schedule.name,
                        schedule.patient_name,
                        self.theater_room,
                        self.date,
                    )
                )

    def _has_time_overlap(self, other) -> bool:
        """Check if this schedule overlaps with another."""
        from datetime import timedelta

        # Estimate end time from duration if not set
        my_start = self.start_time
        other_start = other.start_time

        # Use estimated duration (in seconds) or default 2 hours
        my_duration = self.estimated_duration or 7200
        other_duration = other.estimated_duration or 7200

        if isinstance(my_duration, str):
            # Duration field stores as seconds
            my_duration = int(my_duration) if my_duration.isdigit() else 7200

        if isinstance(other_duration, str):
            other_duration = int(other_duration) if other_duration.isdigit() else 7200

        from datetime import datetime, timedelta

        from frappe.utils import get_time

        my_start_dt = datetime.combine(datetime.today(), get_time(my_start))
        my_end_dt = my_start_dt + timedelta(seconds=my_duration)

        other_start_dt = datetime.combine(datetime.today(), get_time(other_start))
        other_end_dt = other_start_dt + timedelta(seconds=other_duration)

        return my_start_dt < other_end_dt and other_start_dt < my_end_dt
