// import { toast } from 'frappe-ui'

/**
 * Notification utilities for HMS TZ
 * Provides consistent toast notifications throughout the app
 */

// TEMPORARILY DISABLE FRAPPE TOAST FOR TESTING
const mockToast = {
  success: (message) => console.log('✅ SUCCESS:', message),
  error: (message) => console.log('❌ ERROR:', message),
  info: (message) => console.log('ℹ️ INFO:', message),
  warning: (message) => console.log('⚠️ WARNING:', message)
}

export const notifications = {
  // Success notifications
  success: {
    appointmentCreated: () => mockToast.success('Appointment created successfully'),
    appointmentUpdated: () => mockToast.success('Appointment updated successfully'),
    appointmentCancelled: () => mockToast.success('Appointment cancelled'),
    appointmentCompleted: () => mockToast.success('Appointment marked as completed'),
    appointmentRescheduled: () => mockToast.success('Appointment rescheduled'),
    dataRefreshed: () => mockToast.success('Data refreshed'),
    filtersCleared: () => mockToast.success('All filters cleared')
  },

  // Error notifications
  error: {
    appointmentCreateFailed: (error) => mockToast.error(`Failed to create appointment: ${error}`),
    appointmentUpdateFailed: (error) => mockToast.error(`Failed to update appointment: ${error}`),
    appointmentDeleteFailed: (error) => mockToast.error(`Failed to delete appointment: ${error}`),
    dataLoadFailed: (error) => mockToast.error(`Failed to load data: ${error}`),
    validationFailed: () => mockToast.error('Please fix the form errors'),
    networkError: () => mockToast.error('Network error. Please check your connection'),
    unauthorized: () => mockToast.error('You are not authorized to perform this action'),
    serverError: () => mockToast.error('Server error. Please try again later')
  },

  // Info notifications
  info: {
    filterApplied: (filter) => mockToast.info(`Filter applied: ${filter}`),
    searchCleared: () => mockToast.info('Search cleared'),
    noResults: () => mockToast.info('No results found'),
    loadingData: () => mockToast.info('Loading data...'),
    savingData: () => mockToast.info('Saving...')
  },

  // Warning notifications
  warning: {
    unsavedChanges: () => mockToast.warning('You have unsaved changes'),
    pastTimeSlot: () => mockToast.warning('Cannot book appointments in the past'),
    practitionerUnavailable: () => mockToast.warning('Practitioner is not available at this time'),
    duplicateAppointment: () => mockToast.warning('An appointment already exists at this time'),
    insufficientBuffer: () => mockToast.warning('Appointments must be booked at least 15 minutes in advance')
  }
}

// Batch notification helper
export const showBatchNotifications = (notifications) => {
  notifications.forEach(({ type, message }) => {
    switch (type) {
      case 'success':
        toast.success(message)
        break
      case 'error':
        toast.error(message)
        break
      case 'info':
        toast.info(message)
        break
      case 'warning':
        toast.warning(message)
        break
      default:
        toast(message)
    }
  })
}

// Validation notification helper
export const showValidationErrors = (errors) => {
  const errorMessages = Object.values(errors).filter(Boolean)
  if (errorMessages.length > 0) {
    toast.error(`Please fix the following errors: ${errorMessages.join(', ')}`)
  }
}

// Network error handler
export const handleNetworkError = (error) => {
  if (error?.response?.status === 401) {
    notifications.error.unauthorized()
  } else if (error?.response?.status >= 500) {
    notifications.error.serverError()
  } else if (error?.code === 'NETWORK_ERROR') {
    notifications.error.networkError()
  } else {
    notifications.error.serverError()
  }
}

export default notifications
