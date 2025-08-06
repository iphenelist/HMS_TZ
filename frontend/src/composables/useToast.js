import { useToast as useVueToastification } from 'vue-toastification';

export const useToast = () => {
  const toast = useVueToastification();

  const showToast = (message, type = 'info', options = {}) => {
    const defaultOptions = {
      timeout: options.timeout || 5000, // Default to 5 seconds for better readability
      position: options.position || 'bottom-right',
      hideProgressBar: true,
      closeOnClick: true,
      pauseOnHover: true,
      draggable: true,
      icon: true,
      ...options
    };

    switch (type) {
      case 'success':
        toast.success(message, defaultOptions);
        break;
      case 'error':
        toast.error(message, { ...defaultOptions, timeout: options.timeout || 5000 }); // Longer timeout for errors
        break;
      case 'warning':
        toast.warning(message, defaultOptions);
        break;
      case 'info':
        toast.info(message, defaultOptions);
        break;
      default:
        toast(message, defaultOptions);
    }
  };

  const showSuccess = (message, options = {}) => {
    showToast(message, 'success', options);
  };

  const showError = (message, options = {}) => {
    showToast(message, 'error', options);
  };

  const showWarning = (message, options = {}) => {
    showToast(message, 'warning', options);
  };

  const showInfo = (message, options = {}) => {
    showToast(message, 'info', options);
  };

  const clear = () => {
    toast.clear();
  };

  // Patient Appointment specific toast notifications for HMS TZ
  const notifySuccess = {
    appointmentCreated: () => showSuccess('Appointment created successfully!'),
    appointmentUpdated: () => showSuccess('Appointment updated successfully!'),
    appointmentCancelled: () => showSuccess('Appointment cancelled successfully!'),
    appointmentCompleted: () => showSuccess('Appointment marked as completed!'),
    appointmentRescheduled: () => showSuccess('Appointment rescheduled successfully!'),
    patientCreated: () => showSuccess('Patient created successfully!'),
    dataRefreshed: () => showSuccess('Data refreshed successfully!')
  };

  // Appointment error messages
  const notifyError = {
    appointmentCreateFailed: (error = '') => showError(`Failed to create appointment${error ? ': ' + error : ''}`),
    appointmentUpdateFailed: (error = '') => showError(`Failed to update appointment${error ? ': ' + error : ''}`),
    appointmentDeleteFailed: (error = '') => showError(`Failed to cancel appointment${error ? ': ' + error : ''}`),
    dataLoadFailed: (error = '') => showError(`Failed to load data${error ? ': ' + error : ''}`),
    patientCreateFailed: (error = '') => showError(`Failed to create patient${error ? ': ' + error : ''}`),
    validationFailed: () => showError('Please fix the form errors'),
    networkError: () => showError('Network error. Please check your connection'),
    serverError: () => showError('Server error. Please try again later')
  };

  // Appointment warning messages
  const notifyWarning = {
    pastTimeSlot: () => showWarning('Cannot book appointments in the past'),
    practitionerUnavailable: () => showWarning('Practitioner is not available at this time'),
    duplicateAppointment: () => showWarning('An appointment already exists at this time'),
    insufficientBuffer: () => showWarning('Appointments must be booked at least 15 minutes in advance'),
    unsavedChanges: () => showWarning('You have unsaved changes')
  };

  // Appointment info messages
  const notifyInfo = {
    loadingData: () => showInfo('Loading appointments...'),
    savingData: () => showInfo('Saving appointment...'),
    processingRequest: () => showInfo('Processing your request...')
  };

  // Handle Frappe createResource errors (specific to appointment operations)
  const handleResourceError = (error) => {
    if (error.messages && Array.isArray(error.messages)) {
      showError(error.messages.join('\n'))
    } else if (error.message) {
      showError(error.message)
    } else {
      showError('An error occurred while processing your request.')
    }
  };

  // Handle API errors specific to appointment operations
  const handleApiError = (error) => {
    console.error('API Error:', error) // For debugging
    
    if (error.response) {
      const status = error.response.status
      const message = error.response.data?.message || error.message
      
      switch (status) {
        case 400:
          showError(`Bad Request: ${message}`)
          break
        case 401:
          showError('Unauthorized. Please log in again.')
          break
        case 403:
          showError('You do not have permission to perform this action.')
          break
        case 404:
          showError('Resource not found.')
          break
        case 409:
          showError('Conflict: ' + message)
          break
        case 422:
          showError('Validation Error: ' + message)
          break
        case 500:
          showError('Server error. Please try again later.')
          break
        default:
          showError(message || 'An error occurred.')
      }
    } else if (error.request) {
      showError('Network error. Please check your connection')
    } else if (error.messages && Array.isArray(error.messages)) {
      showError(error.messages.join('\n'))
    } else if (error.message) {
      showError(error.message)
    } else {
      showError('An unexpected error occurred.')
    }
  };

  // Convenience object for easy access to notification methods
  const notifications = {
    success: notifySuccess,
    error: notifyError,
    warning: notifyWarning,
    info: notifyInfo
  };

  return {
    showToast,
    showSuccess,
    showError,
    showWarning,
    showInfo,
    clear,
    toast,
    notifySuccess,
    notifyError,
    notifyWarning,
    notifyInfo,
    handleResourceError,
    handleApiError,
    notifications
  };
};
