import { createResource } from 'frappe-ui'

/**
 * HMS TZ Appointments API
 * This file contains all appointment-related API calls
 */

// Get appointments for a specific date
export const getAppointments = (date, options = {}) => {
  return createResource({
    url: 'hms_tz.api.appointments.get_appointments',
    params: {
      date,
      include_cancelled: options.includeCancelled || false,
      practitioner_id: options.practitionerId || null
    },
    auto: false
  })
}

// Create a new appointment
export const createAppointment = (appointmentData) => {
  return createResource({
    url: 'hms_tz.api.appointments.create_appointment',
    params: appointmentData,
    auto: false
  })
}

// Update an existing appointment
export const updateAppointment = (appointmentId, updates) => {
  return createResource({
    url: 'hms_tz.api.appointments.update_appointment',
    params: {
      id: appointmentId,
      ...updates
    },
    auto: false
  })
}

// Delete an appointment
export const deleteAppointment = (appointmentId) => {
  return createResource({
    url: 'hms_tz.api.appointments.delete_appointment',
    params: { id: appointmentId },
    auto: false
  })
}

// Cancel an appointment
export const cancelAppointment = (appointmentId, reason = '') => {
  return createResource({
    url: 'hms_tz.api.appointments.cancel_appointment',
    params: {
      id: appointmentId,
      reason
    },
    auto: false
  })
}

// Complete an appointment
export const completeAppointment = (appointmentId, notes = '') => {
  return createResource({
    url: 'hms_tz.api.appointments.complete_appointment',
    params: {
      id: appointmentId,
      notes
    },
    auto: false
  })
}

// Get appointment statistics
export const getAppointmentStats = (fromDate, toDate) => {
  return createResource({
    url: 'hms_tz.api.appointments.get_statistics',
    params: {
      from_date: fromDate,
      to_date: toDate
    },
    auto: false
  })
}

// Check appointment availability
export const checkAvailability = (practitionerId, date, timeSlot) => {
  return createResource({
    url: 'hms_tz.api.appointments.check_availability',
    params: {
      practitioner_id: practitionerId,
      date,
      time_slot: timeSlot
    },
    auto: false
  })
}

// Get patient appointments
export const getPatientAppointments = (patientId, options = {}) => {
  return createResource({
    url: 'hms_tz.api.appointments.get_patient_appointments',
    params: {
      patient_id: patientId,
      status: options.status || null,
      limit: options.limit || 50
    },
    auto: false
  })
}

// Reschedule appointment
export const rescheduleAppointment = (appointmentId, newDate, newTimeSlot) => {
  return createResource({
    url: 'hms_tz.api.appointments.reschedule_appointment',
    params: {
      id: appointmentId,
      new_date: newDate,
      new_time_slot: newTimeSlot
    },
    auto: false
  })
}
