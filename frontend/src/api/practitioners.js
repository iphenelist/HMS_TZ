import { createResource } from 'frappe-ui'

/**
 * HMS TZ Practitioners API
 * This file contains all practitioner-related API calls
 */

// Get all practitioners
export const getPractitioners = (options = {}) => {
  return createResource({
    url: 'hms_tz.api.practitioners.get_practitioners',
    params: {
      department: options.department || null,
      speciality: options.speciality || null,
      is_active: options.isActive !== undefined ? options.isActive : true,
      include_unavailable: options.includeUnavailable || false
    },
    auto: false
  })
}

// Get practitioner details
export const getPractitioner = (practitionerId) => {
  return createResource({
    url: 'hms_tz.api.practitioners.get_practitioner',
    params: { id: practitionerId },
    auto: false
  })
}

// Get practitioner availability
export const getPractitionerAvailability = (practitionerId, date) => {
  return createResource({
    url: 'hms_tz.api.practitioners.get_availability',
    params: {
      practitioner_id: practitionerId,
      date
    },
    auto: false
  })
}

// Update practitioner availability
export const updatePractitionerAvailability = (practitionerId, availability) => {
  return createResource({
    url: 'hms_tz.api.practitioners.update_availability',
    params: {
      practitioner_id: practitionerId,
      availability
    },
    auto: false
  })
}

// Get practitioner schedule
export const getPractitionerSchedule = (practitionerId, fromDate, toDate) => {
  return createResource({
    url: 'hms_tz.api.practitioners.get_schedule',
    params: {
      practitioner_id: practitionerId,
      from_date: fromDate,
      to_date: toDate
    },
    auto: false
  })
}

// Get departments
export const getDepartments = () => {
  return createResource({
    url: 'hms_tz.api.practitioners.get_departments',
    auto: false
  })
}

// Get specialties
export const getSpecialties = (department = null) => {
  return createResource({
    url: 'hms_tz.api.practitioners.get_specialties',
    params: { department },
    auto: false
  })
}

// Block practitioner time
export const blockPractitionerTime = (practitionerId, date, fromTime, toTime, reason) => {
  return createResource({
    url: 'hms_tz.api.practitioners.block_time',
    params: {
      practitioner_id: practitionerId,
      date,
      from_time: fromTime,
      to_time: toTime,
      reason
    },
    auto: false
  })
}

// Unblock practitioner time
export const unblockPractitionerTime = (blockId) => {
  return createResource({
    url: 'hms_tz.api.practitioners.unblock_time',
    params: { block_id: blockId },
    auto: false
  })
}
