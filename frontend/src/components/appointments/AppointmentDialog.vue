<template>
  <Dialog
    v-model="localShowDialog"
    :options="{
      title: dialogTitle,
      size: 'lg',
      actions: dialogActions
    }"
    style="z-index: 10000;"
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
        <div v-if="isCreateMode">
          <label class="block text-sm font-medium text-gray-700 mb-2">
            Time Slot
          </label>
          <div class="p-3 bg-gray-50 rounded-lg border">
            <p class="text-sm font-medium text-gray-900">
              {{ formattedTimeSlot }}
            </p>
          </div>
        </div>
        <FormControl
          v-else
          type="select"
          label="Time Slot"
          v-model="formData.time_slot"
          :options="availableTimeSlots"
          :disabled="isViewMode || props.mode === 'edit'"
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
              :label="displayPractitioner?.name"
              :image="displayPractitioner?.image"
              size="sm"
            />
            <div>
              <p class="text-sm font-medium text-gray-900">
                {{ displayPractitioner?.name }}
              </p>
              <p class="text-xs text-gray-500">
                {{ displayPractitioner?.specialty }}
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
          v-if="props.mode !== 'create'"
          type="select"
          label="Status"
          v-model="formData.status"
          :options="statusOptions"
          :disabled="isViewMode"
        />

        <!-- Error Display for create mode -->
        <div v-if="error && isCreateMode" class="mt-4">
          <div class="bg-red-50 border border-red-200 rounded-md p-3">
            <p class="text-sm text-red-800">{{ error }}</p>
          </div>
        </div>

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
import { computed, reactive, watch, ref, nextTick } from 'vue'
import { 
  Dialog, 
  FormControl, 
  Avatar, 
  Badge, 
  Button
} from 'frappe-ui'
import { useAppointmentStore } from '@/stores/appointment'
import { usePractitionerStore } from '@/stores/practitioner'
import { useDateStore } from '@/stores/date'
import { notifications } from '@/utils/notifications'
import dayjs from 'dayjs'

// Props for v-model approach
const props = defineProps({
  showDialog: {
    type: Boolean,
    default: false
  },
  timeSlot: {
    type: String,
    default: ''
  },
  practitionerData: {
    type: Object,
    default: () => ({})
  },
  mode: {
    type: String,
    default: 'create' // 'create', 'edit', 'view'
  },
  appointment: {
    type: Object,
    default: () => ({})
  }
})

// Emits for v-model approach
const emit = defineEmits(['update:showDialog', 'closeDialog', 'appointmentCreated'])

const appointmentStore = useAppointmentStore()
const practitionerStore = usePractitionerStore()
const dateStore = useDateStore()

// Local dialog state for v-model approach
const localShowDialog = ref(props.showDialog)
const isCreating = ref(false)
const error = ref('')

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
const isViewMode = computed(() => props.mode === 'view')
const isCreateMode = computed(() => props.mode === 'create')

const dialogTitle = computed(() => {
  switch (props.mode) {
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
      variant: 'outline',
      handler: () => closeDialog()
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
      variant: 'outline',
      handler: () => closeDialog()
    })
    
    actions.push({
      label: isCreateMode.value ? 'Create Appointment' : 'Update Appointment',
      variant: 'solid',
      loading: isCreating.value,
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
      if (isCreateMode.value) {
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

const displayPractitioner = computed(() => {
  // For create mode, use practitionerData prop
  if (isCreateMode.value) {
    return props.practitionerData
  }
  // For edit/view mode, find from store
  return practitionerStore.practitioners.find(
    p => p.id === formData.practitioner_id
  )
})

// Computed property for formatted time slot in create mode
const formattedTimeSlot = computed(() => {
  if (!props.timeSlot) return ''
  return dayjs(`2024-01-01 ${props.timeSlot}`).format('h:mm A')
})

// Watch for dialog state changes - v-model approach
watch(() => props.showDialog, (newVal) => {
  localShowDialog.value = newVal
  if (newVal) {
    // Use nextTick for immediate opening
    nextTick(() => {
      resetForm()
      error.value = ''
      if (props.appointment && Object.keys(props.appointment).length > 0) {
        populateForm(props.appointment)
      } else if (isCreateMode.value) {
        // Pre-fill data for create mode
        formData.time_slot = props.timeSlot
        formData.practitioner_id = props.practitionerData?.name
        formData.date = dateStore.selectedDate
      }
    })
  }
})

watch(localShowDialog, (newVal) => {
  emit('update:showDialog', newVal)
  if (!newVal) {
    emit('closeDialog')
  }
})

// Legacy watch for backward compatibility with old store-based approach
watch(
  () => appointmentStore.showAppointmentDialog,
  (isOpen) => {
    if (isOpen && !localShowDialog.value) {
      localShowDialog.value = true
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
  error.value = ''
  
  if (!validateForm()) {
    error.value = 'Please fill in all required fields correctly.'
    return
  }
  
  isCreating.value = true
  
  try {
    let result
    
    if (isCreateMode.value) {
      const appointmentData = {
        patient_name: formData.patient_name,
        contact: formData.contact,
        appointment_type: formData.appointment_type,
        time_slot: props.timeSlot || formData.time_slot,
        practitioner_id: props.practitionerData?.name || formData.practitioner_id,
        practitioner_name: props.practitionerData?.name || formData.practitioner_name,
        notes: formData.notes,
        date: dateStore.selectedDate,
        status: 'scheduled'
      }
      result = await appointmentStore.createAppointment(appointmentData)
    } else if (props.mode === 'edit') {
      result = await appointmentStore.updateAppointment(
        props.appointment.id || appointmentStore.selectedAppointment?.id,
        formData
      )
    }
    
    if (result?.success) {
      if (isCreateMode.value) {
        notifications.success.appointmentCreated()
        emit('appointmentCreated')
      } else {
        notifications.success.appointmentUpdated()
      }
      closeDialog()
    } else {
      error.value = result?.error || 'Failed to save appointment'
    }
  } catch (err) {
    error.value = 'An error occurred while saving the appointment'
    console.error('Error saving appointment:', err)
  } finally {
    isCreating.value = false
  }
}

const editAppointment = () => {
  // For legacy support
  if (appointmentStore.dialogMode) {
    appointmentStore.dialogMode = 'edit'
  }
}

const closeDialog = () => {
  localShowDialog.value = false
  // Close legacy store dialog if open
  if (appointmentStore.showAppointmentDialog) {
    appointmentStore.closeAppointmentDialog()
  }
}

const completeAppointment = async () => {
  try {
    const appointmentId = props.appointment?.id || appointmentStore.selectedAppointment?.id
    const result = await appointmentStore.completeAppointment(appointmentId)
    
    if (result?.success) {
      notifications.success.appointmentCompleted()
      closeDialog()
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
    const appointmentId = props.appointment?.id || appointmentStore.selectedAppointment?.id
    const result = await appointmentStore.cancelAppointment(appointmentId)
    
    if (result?.success) {
      notifications.success.appointmentCancelled()
      closeDialog()
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

<style scoped>
/* Ensure dialog appears above everything with highest z-index */
:deep(.dialog) {
  z-index: 10000 !important;
}

:deep(.modal) {
  z-index: 10000 !important;
}

:deep(.modal-backdrop) {
  z-index: 9999 !important;
}

:deep(.modal-dialog) {
  z-index: 10001 !important;
}

:deep(.dialog-wrapper) {
  z-index: 10000 !important;
}

:deep(.dialog-overlay) {
  z-index: 9999 !important;
}

:deep(.dialog-content) {
  z-index: 10001 !important;
}

/* Additional specific targeting for frappe-ui dialog */
:deep([role="dialog"]) {
  z-index: 10000 !important;
}

:deep(.fixed.inset-0) {
  z-index: 9999 !important;
}
</style>

