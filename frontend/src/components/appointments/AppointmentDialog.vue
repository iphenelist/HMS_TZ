<template>
  <Dialog
    v-model="appointmentStore.showAppointmentDialog"
    :options="{
      title: dialogTitle,
      size: 'md',
      actions: dialogActions
    }"
  >
    <template #body-content>
      <!-- Form Content -->
      <div class="space-y-4">
        <!-- Patient Name -->
        <FormControl
          label="Patient Name"
          v-model="formData.patient_name"
          placeholder="Enter patient name"
          :disabled="isViewMode"
          :required="!isViewMode"
          :error="errors.patient_name"
        />

        <!-- Contact Number -->
        <FormControl
          label="Contact Number"
          v-model="formData.contact"
          placeholder="+255XXXXXXXXX"
          :disabled="isViewMode"
          :required="!isViewMode"
          :error="errors.contact"
        />

        <!-- Appointment Type -->
        <FormControl
          type="select"
          label="Appointment Type"
          v-model="formData.appointment_type"
          :options="appointmentTypes"
          :disabled="isViewMode"
          :required="!isViewMode"
          :error="errors.appointment_type"
        />

        <!-- Time Slot -->
        <FormControl
          type="select"
          label="Time Slot"
          v-model="formData.time_slot"
          :options="availableTimeSlots"
          :disabled="isViewMode || appointmentStore.dialogMode === 'edit'"
          :required="!isViewMode"
          :error="errors.time_slot"
        />

        <!-- Practitioner (Display only) -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">
            Practitioner
          </label>
          <div class="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg border">
            <Avatar
              :label="selectedPractitioner?.avatar"
              :image="selectedPractitioner?.image"
              size="sm"
            />
            <div>
              <p class="text-sm font-medium text-gray-900">
                {{ selectedPractitioner?.name }}
              </p>
              <p class="text-xs text-gray-500">
                {{ selectedPractitioner?.specialty }}
              </p>
            </div>
          </div>
        </div>

        <!-- Notes -->
        <FormControl
          type="textarea"
          label="Notes"
          v-model="formData.notes"
          placeholder="Additional notes..."
          :disabled="isViewMode"
          :rows="3"
        />

        <!-- Status (for edit/view mode) -->
        <FormControl
          v-if="appointmentStore.dialogMode !== 'create'"
          type="select"
          label="Status"
          v-model="formData.status"
          :options="statusOptions"
          :disabled="isViewMode"
        />

        <!-- Appointment Details (for view mode) -->
        <div v-if="isViewMode" class="space-y-3 pt-4 border-t border-gray-200">
          <div class="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span class="text-gray-500">Date:</span>
              <span class="ml-2 font-medium">{{ formatDate(formData.date) }}</span>
            </div>
            <div>
              <span class="text-gray-500">Time:</span>
              <span class="ml-2 font-medium">{{ formatTime(formData.time_slot) }}</span>
            </div>
            <div>
              <span class="text-gray-500">Duration:</span>
              <span class="ml-2 font-medium">{{ dateStore.slotDuration }} minutes</span>
            </div>
            <div>
              <span class="text-gray-500">Status:</span>
              <Badge
                :label="formatStatus(formData.status)"
                :theme="getStatusTheme(formData.status)"
                class="ml-2"
              />
            </div>
          </div>
        </div>
      </div>
    </template>
  </Dialog>
</template>



<script setup>
import { computed, reactive, watch } from 'vue'
import { 
  Dialog, 
  FormControl, 
  Avatar, 
  Badge, 
  Button
} from 'frappe-ui'
import { useAppointmentStore } from '@/stores/appointments'
import { usePractitionerStore } from '@/stores/practitioner'
import { useDateStore } from '@/stores/date'
import { notifications } from '@/utils/notifications'
import dayjs from 'dayjs'

const appointmentStore = useAppointmentStore()
const practitionerStore = usePractitionerStore()
const dateStore = useDateStore()

// Form data
const formData = reactive({
  patient_name: '',
  contact: '',
  appointment_type: '',
  time_slot: '',
  practitioner_id: null,
  notes: '',
  status: 'scheduled',
  date: ''
})

// Form validation errors
const errors = reactive({})

// Dialog computed properties
const isViewMode = computed(() => appointmentStore.dialogMode === 'view')

const dialogTitle = computed(() => {
  switch (appointmentStore.dialogMode) {
    case 'create':
      return 'Create New Appointment'
    case 'edit':
      return 'Edit Appointment'
    case 'view':
      return 'Appointment Details'
    default:
      return 'Appointment'
  }
})

const dialogActions = computed(() => {
  const actions = []
  
  if (isViewMode.value) {
    actions.push({
      label: 'Close',
      variant: 'outline'
    })
    
    if (formData.status !== 'cancelled') {
      actions.push({
        label: 'Edit',
        variant: 'outline',
        handler: editAppointment
      })
    }
    
    if (formData.status === 'scheduled') {
      actions.push({
        label: 'Mark Complete',
        variant: 'solid',
        theme: 'green',
        handler: completeAppointment
      })
    }
    
    if (formData.status !== 'cancelled') {
      actions.push({
        label: 'Cancel',
        variant: 'outline',
        theme: 'red',
        handler: () => showCancelConfirmation()
      })
    }
  } else {
    actions.push({
      label: 'Cancel',
      variant: 'outline'
    })
    
    actions.push({
      label: appointmentStore.dialogMode === 'create' ? 'Create Appointment' : 'Update Appointment',
      variant: 'solid',
      loading: appointmentStore.isLoading,
      handler: handleSubmit
    })
  }
  
  return actions
})

// Form options
const appointmentTypes = [
  { label: 'Consultation', value: 'Consultation' },
  { label: 'Follow-up', value: 'Follow-up' },
  { label: 'Emergency', value: 'Emergency' },
  { label: 'Checkup', value: 'Checkup' },
  { label: 'Surgery', value: 'Surgery' },
  { label: 'Therapy', value: 'Therapy' },
  { label: 'Laboratory', value: 'Laboratory' },
  { label: 'Radiology', value: 'Radiology' }
]

const statusOptions = [
  { label: 'Open', value: 'open' },
  { label: 'Scheduled', value: 'scheduled' },
  { label: 'Completed', value: 'completed' },
  { label: 'Cancelled', value: 'cancelled' }
]

const availableTimeSlots = computed(() => {
  return dateStore.timeSlots
    .filter(slot => {
      // For create mode, only show future slots
      if (appointmentStore.dialogMode === 'create') {
        return !slot.isPast
      }
      // For edit/view mode, show all slots
      return true
    })
    .map(slot => ({
      label: slot.display,
      value: slot.time
    }))
})

const selectedPractitioner = computed(() => {
  return practitionerStore.practitioners.find(
    p => p.id === formData.practitioner_id
  )
})

// Watch for dialog state changes
watch(
  () => appointmentStore.showAppointmentDialog,
  (isOpen) => {
    if (isOpen) {
      resetForm()
      if (appointmentStore.selectedAppointment) {
        populateForm(appointmentStore.selectedAppointment)
      }
    }
  }
)

// Form methods
const resetForm = () => {
  Object.assign(formData, {
    patient_name: '',
    contact: '',
    appointment_type: '',
    time_slot: '',
    practitioner_id: null,
    notes: '',
    status: 'scheduled',
    date: dateStore.selectedDate
  })
  Object.keys(errors).forEach(key => delete errors[key])
}

const populateForm = (appointment) => {
  Object.assign(formData, {
    patient_name: appointment.patient_name || '',
    contact: appointment.contact || '',
    appointment_type: appointment.appointment_type || '',
    time_slot: appointment.time_slot || '',
    practitioner_id: appointment.practitioner_id || null,
    notes: appointment.notes || '',
    status: appointment.status || 'scheduled',
    date: appointment.date || dateStore.selectedDate
  })
}

const validateForm = () => {
  Object.keys(errors).forEach(key => delete errors[key])
  
  if (!formData.patient_name?.trim()) {
    errors.patient_name = 'Patient name is required'
  }
  
  if (!formData.contact?.trim()) {
    errors.contact = 'Contact number is required'
  } else if (!/^\+255\d{9}$/.test(formData.contact)) {
    errors.contact = 'Please enter a valid Tanzanian phone number (+255XXXXXXXXX)'
  }
  
  if (!formData.appointment_type) {
    errors.appointment_type = 'Appointment type is required'
  }
  
  if (!formData.time_slot) {
    errors.time_slot = 'Time slot is required'
  }
  
  if (!formData.practitioner_id) {
    errors.practitioner_id = 'Practitioner is required'
  }
  
  return Object.keys(errors).length === 0
}

const handleSubmit = async () => {
  if (!validateForm()) {
    notifications.error.validationFailed()
    return
  }
  
  try {
    let result
    
    if (appointmentStore.dialogMode === 'create') {
      result = await appointmentStore.createAppointment(formData)
    } else if (appointmentStore.dialogMode === 'edit') {
      result = await appointmentStore.updateAppointment(
        appointmentStore.selectedAppointment.id,
        formData
      )
    }
    
    if (result?.success) {
      if (appointmentStore.dialogMode === 'create') {
        notifications.success.appointmentCreated()
      } else {
        notifications.success.appointmentUpdated()
      }
    } else {
      notifications.error.appointmentCreateFailed(result?.error || 'Unknown error')
    }
  } catch (error) {
    notifications.error.appointmentCreateFailed('An error occurred while saving')
    console.error(error)
  }
}

const editAppointment = () => {
  appointmentStore.dialogMode = 'edit'
}

const completeAppointment = async () => {
  try {
    const result = await appointmentStore.completeAppointment(
      appointmentStore.selectedAppointment.id
    )
    
    if (result?.success) {
      notifications.success.appointmentCompleted()
      appointmentStore.closeAppointmentDialog()
    } else {
      notifications.error.appointmentUpdateFailed('Failed to update appointment status')
    }
  } catch (error) {
    notifications.error.appointmentUpdateFailed('Error updating appointment')
    console.error(error)
  }
}

const showCancelConfirmation = () => {
  if (confirm('Are you sure you want to cancel this appointment?')) {
    cancelAppointment()
  }
}

const cancelAppointment = async () => {
  try {
    const result = await appointmentStore.cancelAppointment(
      appointmentStore.selectedAppointment.id
    )
    
    if (result?.success) {
      notifications.success.appointmentCancelled()
      appointmentStore.closeAppointmentDialog()
    } else {
      notifications.error.appointmentUpdateFailed('Failed to cancel appointment')
    }
  } catch (error) {
    notifications.error.appointmentUpdateFailed('Error cancelling appointment')
    console.error(error)
  }
}

// Utility functions
const formatDate = (dateString) => {
  return dayjs(dateString).format('dddd, MMMM D, YYYY')
}

const formatTime = (timeSlot) => {
  return dayjs(`2024-01-01 ${timeSlot}`).format('h:mm A')
}

const formatStatus = (status) => {
  const statusMap = {
    open: 'Open',
    completed: 'Completed',
    scheduled: 'Scheduled',
    cancelled: 'Cancelled'
  }
  return statusMap[status] || status
}

const getStatusTheme = (status) => {
  const themeMap = {
    open: 'gray',
    completed: 'green',
    scheduled: 'orange',
    cancelled: 'red'
  }
  return themeMap[status] || 'gray'
}
</script>

