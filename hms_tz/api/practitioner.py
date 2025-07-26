import frappe
import datetime
from frappe import _
from frappe.query_builder import DocType
from frappe.utils import getdate, nowdate, get_time, time_diff_in_seconds
from erpnext.setup.doctype.employee.employee import is_holiday


@frappe.whitelist()
def get_practitioners(company=None, date=None):
    """
    Get all available practitioners for a company on a specific date
    Filters out practitioners who are:
    - Not available based on schedules and availability
    - On leave or unavailable
    - Have no practitioner schedules
    
    Returns practitioners with their availability data
    """
    if not date:
        date = nowdate()
    
    date = getdate(date)
    weekday = date.strftime("%A")
    
    try:
        # Base query for practitioners
        practitioners_query = f"""
            SELECT 
                hp.name,
                hp.practitioner_name,
                hp.first_name,
                hp.middle_name,
                hp.last_name,
                hp.department,
                hp.mobile_phone,
                hp.op_consulting_charge,
                hp.inpatient_visit_charge,
                hp.image,
                hp.status,
                hp.hms_tz_company,
                hp.healthcare_practitioner_type,
                md.department as department_name
            FROM `tabHealthcare Practitioner` hp
            LEFT JOIN `tabMedical Department` md ON hp.department = md.name
            WHERE hp.status = 'Active'
        """
        
        # Add company filter if provided
        if company:
            practitioners_query += f" AND hp.hms_tz_company = '{company}'"
            
        practitioners_query += " ORDER BY hp.practitioner_name"
        
        practitioners = frappe.db.sql(practitioners_query, as_dict=True)
        
        available_practitioners = []
        
        for practitioner in practitioners:
            try:
                # Check if practitioner has schedules
                if not has_practitioner_schedules(practitioner.name):
                    continue
                
                # Check employee availability (holidays, leaves)
                if not check_practitioner_employee_availability(practitioner.name, date):
                    continue
                
                # Check practitioner availability based on schedules
                availability_data = get_practitioner_availability(practitioner.name, date, weekday)
                
                if not availability_data or not availability_data.get('available_slots'):
                    continue
                
                # Transform practitioner data to match frontend schema
                practitioner_data = {
                    'name': practitioner.name,
                    'department': practitioner.department_name or 'General',
                    'avatar': get_practitioner_avatar(practitioner.practitioner_name or practitioner.first_name),
                    'is_available': True,
                    'mobile_phone': practitioner.mobile_phone,
                    'image': practitioner.image,
                    'timeslots': availability_data.get('available_slots', []),
                    'present_events': availability_data.get('present_events', []),
                }
                
                available_practitioners.append(practitioner_data)
                
            except Exception as e:
                continue
        
        return {
            'practitioners': available_practitioners,
            'total_count': len(available_practitioners),
            'date': date,
            'company': company
        }
        
    except Exception as e:
        pass


def has_practitioner_schedules(practitioner):
    """Check if practitioner has any schedules configured"""
    schedules = frappe.db.sql("""
        SELECT COUNT(*) as count
        FROM `tabPractitioner Service Unit Schedule`
        WHERE parent = %s AND parenttype = 'Healthcare Practitioner'
    """, (practitioner,), as_dict=True)
    
    return schedules[0].count > 0 if schedules else False


def check_practitioner_employee_availability(practitioner, date):
    """
    Check if practitioner is available based on employee status
    Returns False if on holiday or leave
    """
    try:
        practitioner_doc = frappe.get_cached_doc("Healthcare Practitioner", practitioner)
        
        employee = None
        if practitioner_doc.employee:
            employee = practitioner_doc.employee
        elif practitioner_doc.user_id:
            employee = frappe.get_cached_value("Employee", {"user_id": practitioner_doc.user_id}, "name")
        
        if employee:
            # Check holiday
            if is_holiday(employee, date):
                return False
            
            # Check leave status
            if "hrms" in frappe.get_installed_apps():
                leave_record = frappe.db.sql("""
                    SELECT half_day 
                    FROM `tabLeave Application`
                    WHERE employee = %s 
                    AND %s BETWEEN from_date AND to_date
                    AND docstatus = 1
                """, (employee, date), as_dict=True)
                
                if leave_record:
                    return False
        
        return True
        
    except Exception as e:
        return False


def get_practitioner_availability(practitioner, date, weekday):
    """
    Get detailed availability data for a practitioner on a specific date
    """
    try:
        practitioner_doc = frappe.get_cached_doc("Healthcare Practitioner", practitioner)
        
        # Get present events from Practitioner Availability
        present_events = get_present_events(practitioner, date)
        
        # Get scheduled slots
        slot_details = get_scheduled_slots(practitioner_doc, date, weekday)
        
        # Process present events into slots
        present_event_slots = process_present_event_slots(present_events, date, practitioner)
        
        # Combine all available slots
        all_slots = slot_details + present_event_slots
        
        # Remove duplicate slots and sort
        unique_slots = remove_duplicate_slots(all_slots)
        
        return {
            'available_slots': unique_slots,
            'present_events': present_events,
            'total_slots': len(unique_slots)
        }
        
    except Exception as e:
        return {'available_slots': [], 'present_events': []}


def get_present_events(practitioner, date):
    """Get present events from Practitioner Availability"""
    try:
        date = getdate(date)
        present_events = frappe.db.sql(f"""
            SELECT
                name, availability, from_time, to_time, from_date, to_date, 
                duration, service_unit, repeat_this_event, repeat_on, repeat_till,
                monday, tuesday, wednesday, thursday, friday, saturday, sunday
            FROM `tabPractitioner Availability`
            WHERE practitioner = '{practitioner}' 
            AND present = 1 
            AND (
                (repeat_this_event = 1 AND (from_date <= '{date}' AND IFNULL(repeat_till, '3000-01-01') >= '{date}'))
                OR
                (repeat_this_event != 1 AND (from_date <= '{date}' AND to_date >= '{date}'))
            )
            ORDER BY from_date, from_time
        """, as_dict=True)
        
        return present_events if present_events else []
        
    except Exception as e:
        return []


def get_scheduled_slots(practitioner_doc, date, weekday):
    """Get available slots based on practitioner schedules"""
    try:
        slot_details = []
        
        for schedule_entry in practitioner_doc.practitioner_schedules:
            if not schedule_entry.schedule:
                continue
                
            practitioner_schedule = frappe.get_cached_doc("Practitioner Schedule", schedule_entry.schedule)
            
            if not practitioner_schedule:
                continue
            
            # Get time slots for the specific weekday
            available_slots = []
            for time_slot in practitioner_schedule.time_slots:
                if weekday.lower() == time_slot.day.lower():
                    available_slots.append(time_slot)
            
            if not available_slots:
                continue
            
            # Get existing appointments for this schedule/service unit
            appointments = get_existing_appointments(practitioner_doc.name, date, schedule_entry)
            
            # Generate available time slots
            for slot in available_slots:
                slot_times = generate_slot_times(slot, appointments, schedule_entry)
                slot_details.extend(slot_times)
        
        return slot_details
        
    except Exception as e:
        return []


def get_existing_appointments(practitioner, date, schedule_entry):
    """Get existing appointments for a practitioner on a specific date"""
    try:
        filters = {
            "practitioner": practitioner,
            "appointment_date": date,
            "status": ["not in", ["Cancelled"]]
        }
        
        if schedule_entry.service_unit:
            filters["service_unit"] = schedule_entry.service_unit
        
        appointments = frappe.get_all(
            "Patient Appointment",
            filters=filters,
            fields=["name", "appointment_time", "duration", "status"]
        )
        
        return appointments
        
    except Exception as e:
        return []


def generate_slot_times(time_slot, appointments, schedule_entry):
    """Generate available time slots considering existing appointments"""
    try:
        slots = []
        
        # Convert start and end times
        start_time = get_time(time_slot.from_time)
        end_time = get_time(time_slot.to_time)
        
        # Default slot duration (15 minutes)
        slot_duration = 15
        
        current_time = datetime.datetime.combine(datetime.date.today(), start_time)
        end_datetime = datetime.datetime.combine(datetime.date.today(), end_time)
        
        while current_time < end_datetime:
            slot_time = current_time.time()
            
            # Check if this slot conflicts with existing appointments
            is_available = True
            for appointment in appointments:
                if appointment.appointment_time:
                    appt_time = get_time(appointment.appointment_time)
                    appt_duration = appointment.duration or 15
                    
                    appt_end = (datetime.datetime.combine(datetime.date.today(), appt_time) + 
                               datetime.timedelta(minutes=appt_duration)).time()
                    
                    if slot_time >= appt_time and slot_time < appt_end:
                        is_available = False
                        break
            
            if is_available:
                slots.append({
                    'time': slot_time.strftime('%H:%M'),
                    'display': slot_time.strftime('%H:%M'),
                    'available': True,
                    'service_unit': schedule_entry.service_unit,
                    'schedule': schedule_entry.schedule
                })
            
            current_time += datetime.timedelta(minutes=slot_duration)
        
        return slots
        
    except Exception as e:
        return []


def process_present_event_slots(present_events, date, practitioner):
    """Process present events into available slots"""
    try:
        slots = []
        
        if not present_events:
            return slots
        
        # Filter events based on repeat settings
        filtered_events = filter_events_by_repeat(present_events, date)
        
        for event in filtered_events:
            if not event.from_time or not event.to_time:
                continue
            
            # Generate slots for this event
            event_slots = generate_event_slots(event, date, practitioner)
            slots.extend(event_slots)
        
        return slots
        
    except Exception as e:
        return []


def filter_events_by_repeat(events, date):
    """Filter events based on repeat settings and weekday"""
    try:
        filtered_events = []
        weekday = date.strftime("%A").lower()
        
        for event in events:
            if event.repeat_this_event:
                # Check if event repeats on this weekday
                if hasattr(event, weekday) and getattr(event, weekday):
                    filtered_events.append(event)
            else:
                # Non-repeating event, check date range
                if event.from_date <= date <= event.to_date:
                    filtered_events.append(event)
        
        return filtered_events
        
    except Exception as e:
        return events


def generate_event_slots(event, date, practitioner):
    """Generate time slots from a practitioner availability event"""
    try:
        slots = []
        
        start_time = get_time(event.from_time)
        end_time = get_time(event.to_time)
        duration = event.duration or 15
        
        current_time = datetime.datetime.combine(date, start_time)
        end_datetime = datetime.datetime.combine(date, end_time)
        
        while current_time < end_datetime:
            slots.append({
                'time': current_time.time().strftime('%H:%M'),
                'display': current_time.time().strftime('%H:%M'),
                'available': True,
                'service_unit': event.service_unit,
                'event': event.name
            })
            
            current_time += datetime.timedelta(minutes=duration)
        
        return slots
        
    except Exception as e:
        return []


def remove_duplicate_slots(slots):
    """Remove duplicate slots and sort by time"""
    try:
        unique_slots = {}
        
        for slot in slots:
            slot_key = slot['time']
            if slot_key not in unique_slots:
                unique_slots[slot_key] = slot
        
        # Sort by time
        sorted_slots = sorted(unique_slots.values(), key=lambda x: x['time'])
        
        return sorted_slots
        
    except Exception as e:
        return slots


def get_practitioner_avatar(name):
    """Generate avatar initials from practitioner name"""
    if not name:
        return "P"
    
    parts = name.split()
    if len(parts) >= 2:
        return f"{parts[0][0]}{parts[1][0]}".upper()
    elif len(parts) == 1:
        return parts[0][:2].upper()
    else:
        return "P"


@frappe.whitelist()
def get_practitioner_availability_summary(practitioner, date=None):
    """
    Get availability summary for a specific practitioner
    """
    if not date:
        date = nowdate()
    
    date = getdate(date)
    weekday = date.strftime("%A")
    
    try:
        availability_data = get_practitioner_availability(practitioner, date, weekday)
        employee_available = check_practitioner_employee_availability(practitioner, date)
        
        return {
            'practitioner': practitioner,
            'date': date,
            'is_available': employee_available and len(availability_data.get('available_slots', [])) > 0,
            'total_slots': len(availability_data.get('available_slots', [])),
            'available_slots': availability_data.get('available_slots', []),
            'employee_available': employee_available
        }
        
    except Exception as e:
        return {
            'practitioner': practitioner,
            'date': date,
            'is_available': False,
            'total_slots': 0,
            'available_slots': [],
            'employee_available': False
        }