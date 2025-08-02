<template>
  <Dialog
    v-model="localShowDialog"
    :options="{
      title: dialogTitle,
      actions: dialogActions,
      size: '4xl'
    }"
    :disable-outside-click-to-close="true"
    style="z-index: 10000;"
  >
    <!-- 'Create New Appointment' -->
    <template #body-content>
      <div class="space-y-4">
        <div class="bg-white px-2 pb-6 pt-1 sm:px-2">
          <div class="mb-5 flex gap-36 items-center justify-around">
            <!-- <div class="w-112 mb-4">
              <h3 class="text-2xl text-center font-semibold leading-6 text-gray-900">
                {{ dialogTitle }}
              </h3>
            </div> -->
          </div>
          <div v-if="isCreating" class="text-center py-4 text-gray-500">{{ statusMessage }}</div>
          <div>
            <FieldMap v-if="sections" :sections="sections" :data="appointment" />
            <div v-if="error" class="mt-4 text-lg font-bold text-red-600">{{ error }}</div>
          </div>
        </div>
      </div>
    </template>
  </Dialog>
</template>



<script setup>
import { computed, reactive, watch, ref, nextTick } from 'vue'
import {  createResource } from 'frappe-ui'
import { useAppointmentStore } from '@/stores/appointment'
import { usePractitionerStore } from '@/stores/practitioner'
import { useDateStore } from '@/stores/date'
import { notifications } from '@/utils/notifications'
import FieldMap from '@/components/controls/FieldMap.vue'
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
const statusMessage = ref('')
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


const appointment = reactive({
    "Patient Appointment": {
      "payment_mode": "",
      "insurance_provider": "",
      "is_new_patient": false,
      "patient": "",
      "patient_name": "",
      "practitioner": "",
      "appointment_type": "",
      "appointment_date": "",
      "appointment_time": "",
      "referral_no": "",
      "remarks": "",
      "is_new_his": false,
      "insurance_subscription": "",
      "coverage_plan_card_number": "",
      "national_id": "",
      "authorization_number": "",
      "require_fingerprint": "",
      "require_facial_recognation": "",
      "biometric_method": "",
      "fpcode": "",
      "poc_reference_no": "",
      "mode_of_payment": "",
      "billing_item": "",
      "paid_amount": "",
    },
    "Patient": {
      "first_name": "",
      "middle_name": "",
      "last_name": "",
      "sex": "",
      "dob": "",
      "mobile": "",
      "product_code": "",
      "scheme_id": "",
      "membership_no": "",
      "card_no": "",
      "national_id": "",
      "next_to_kin_name": "",
      "next_to_kin_mobile_no": "",
      "next_to_kin_relationship": "",
    },
    "Healthcare Insurance Subscription": {
      "patient": "",
      "patient_name": "",
      "insurance_company": "",
      "healthcare_insurance_coverage_plan": "",
      "coverage_plan_card_number": "",
      "national_id": "",
    }
})

const sections = [
    {
        "label":"Appointment Details",
        "doctype":"Patient Appointment",
        "fields":[
            {"name": "is_new_patient", "label": "Is New Patient", "type": "Check", "placeholder": "Is New Patient", "reqd": false},
            {"name": "patient", "label": "Patient", "type": "Link", "placeholder": "Patient", "options": "Patient", "reqd": true},
            {"name": "patient_name", "label": "Patient Name", "type": "Data", "placeholder": "Patient Name", "reqd": false},
            {"name": "practitioner", "label": "Practitioner", "type": "Link", "placeholder": "Practitioner", "options": "Healthcare Practitioner", "reqd": true},
            {"name": "appointment_type", "label": "Appointment Type", "type": "Select", "placeholder": "Appointment Type", 
                "options": [
                    {"label": "Consultation", "value": "Consultation"},
                    {"label": "Follow-up", "value": "Follow-up"},
                    {"label": "Emergency", "value": "Emergency"},
                    {"label": "Checkup", "value": "Checkup"},
                    {"label": "Surgery", "value": "Surgery"},
                    {"label": "Therapy", "value": "Therapy"},
                    {"label": "Laboratory", "value": "Laboratory"},
                    {"label": "Radiology", "value": "Radiology"}
                ], "reqd": true
            },
            {"name": "appointment_date", "label": "Appointment Date", "type": "Date", "placeholder": "Appointment Date", "reqd": true},
            {"name": "appointment_time", "label": "Appointment Time", "type": "Time", "placeholder": "Appointment Time", "reqd": true},
            {"name": "payment_mode", "label": "Payment Mode", "type": "Select", "placeholder": "Payment Mode",
                "options": [
                    {"label": "Cash", "value": "Cash"},
                    {"label": "Insurance", "value": "Insurance"},
                    {"label": "Credit", "value": "Credit"}
                ], "reqd": false
            },
            {"name": "is_new_his", "label": "Is New Insurance", "type": "Check", "placeholder": "Is New Insurance", "reqd": false},
            {"name": "insurance_subscription", "label": "Insurance Subscription", "type": "Link", "placeholder": "Insurance Subscription", "options": "Healthcare Insurance Subscription", "reqd": false},
            {"name": "referral_no", "label": "Referral No", "type": "Data", "placeholder": "Referral No", "reqd": false},
            {"name": "remarks", "label": "Remarks", "type": "Small Text", "placeholder": "Remarks", "reqd": false},
        ],
        "hideLabel":false
    },
    {
        "label":"Patient Details",
        "doctype":"Patient",
        "fields":[
            {"name": "first_name", "label": "First Name", "type": "Data", "placeholder": "First Name", "reqd": true},
            {"name": "middle_name", "label": "Middle Name", "type": "Data", "placeholder": "Middle Name", "reqd": false},
            {"name": "last_name", "label": "Last Name", "type": "Data", "placeholder": "Last Name", "reqd": true},
            {"name": "sex", "label": "Sex", "type": "Select", "placeholder": "Sex",
                "options": [
                    {"label": "Male", "value": "Male"},
                    {"label": "Female", "value": "Female"},
                    {"label": "Other", "value": "Other"}
                ], "reqd": true
            },
            {"name": "dob", "label": "Date of Birth", "type": "Date", "placeholder": "Date of Birth", "reqd": true},
            {"name": "mobile", "label": "Mobile", "type": "Data", "placeholder": "Mobile", "reqd": false},
            {"name": "national_id", "label": "National ID", "type": "Data", "placeholder": "National ID", "reqd": false},
            {"name": "next_to_kin_name", "label": "Next of Kin Name", "type": "Data", "placeholder": "Next of Kin Name", "reqd": false},
            {"name": "next_to_kin_mobile_no", "label": "Next of Kin Mobile", "type": "Data", "placeholder": "Next of Kin Mobile", "reqd": false},
            {"name": "next_to_kin_relationship", "label": "Next of Kin Relationship", "type": "Data", "placeholder": "Next of Kin Relationship", "reqd": false},
        ],
        "hideLabel":false,
        "hideBorder":false
    },
    {
        "label":"Healthcare Insurance Subscription",
        "doctype":"Healthcare Insurance Subscription", 
        "fields":[
            {"name": "insurance_company", "label": "Insurance Company", "type": "Link", "placeholder": "Insurance Company", "options": "Healthcare Insurance Company", "reqd": true},
            {"name": "healthcare_insurance_coverage_plan", "label": "Coverage Plan", "type": "Link", "placeholder": "Coverage Plan", "options": "Healthcare Insurance Coverage Plan", "reqd": true},
            {"name": "coverage_plan_card_number", "label": "Card Number", "type": "Data", "placeholder": "Card Number", "reqd": false},
            {"name": "national_id", "label": "National ID", "type": "Data", "placeholder": "National ID", "reqd": false},
        ],
        "hideLabel":false,
        "hideBorder":false
    }
]


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
      resetAppointment()
      error.value = ''
      if (props.appointment && Object.keys(props.appointment).length > 0) {
        // populateForm(props.appointment) - TODO: implement populate for appointment object
      } else if (isCreateMode.value) {
        // Pre-fill data for create mode
        appointment['Patient Appointment']['appointment_time'] = props.timeSlot
        appointment['Patient Appointment']['practitioner'] = props.practitionerData?.name
        appointment['Patient Appointment']['appointment_date'] = dateStore.selectedDate
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
      resetAppointment()
      if (appointmentStore.selectedAppointment) {
        // populateForm(appointmentStore.selectedAppointment) - TODO: implement populate for appointment object
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

const resetAppointment = () => {
  appointment["Patient Appointment"] = {
    "payment_mode": "",
    "insurance_provider": "",
    "is_new_patient": false,
    "patient": "",
    "patient_name": "",
    "practitioner": "",
    "appointment_type": "",
    "appointment_date": "",
    "appointment_time": "",
    "referral_no": "",
    "remarks": "",
    "is_new_his": false,
    "insurance_subscription": "",
    "coverage_plan_card_number": "",
    "national_id": "",
    "authorization_number": "",
    "require_fingerprint": "",
    "require_facial_recognation": "",
    "biometric_method": "",
    "fpcode": "",
    "poc_reference_no": "",
    "mode_of_payment": "",
    "billing_item": "",
    "paid_amount": "",
  }

  appointment["Patient"] = {
    "first_name": "",
    "middle_name": "",
    "last_name": "",
    "sex": "",
    "dob": "",
    "mobile": "",
    "product_code": "",
    "scheme_id": "",
    "membership_no": "",
    "card_no": "",
    "national_id": "",
    "next_to_kin_name": "",
    "next_to_kin_mobile_no": "",
    "next_to_kin_relationship": "",
  }

  appointment["Healthcare Insurance Subscription"] = {
    "patient": "",
    "patient_name": "",
    "insurance_company": "",
    "healthcare_insurance_coverage_plan": "",
    "coverage_plan_card_number": "",
    "national_id": "",
  }
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
  // Validate appointment form based on sections
  Object.keys(errors).forEach(key => delete errors[key])
  
  const appointmentData = appointment["Patient Appointment"]
  
  if (!appointmentData.patient_name?.trim() && appointmentData.is_new_patient) {
    errors.patient_name = 'Patient name is required'
  }
  
  if (!appointmentData.patient && !appointmentData.is_new_patient) {
    errors.patient = 'Patient is required'
  }
  
  if (!appointmentData.practitioner) {
    errors.practitioner = 'Practitioner is required'
  }
  
  if (!appointmentData.appointment_type) {
    errors.appointment_type = 'Appointment type is required'
  }
  
  if (!appointmentData.appointment_date) {
    errors.appointment_date = 'Appointment date is required'
  }
  
  if (!appointmentData.appointment_time) {
    errors.appointment_time = 'Appointment time is required'
  }
  
  return Object.keys(errors).length === 0
}

// Create resources for document creation
const appointment_doc = createResource({
  url: 'frappe.client.insert',
  method: 'POST',
  makeParams() {
    return {
      doc: {
        doctype: 'Patient Appointment',
        ...appointment['Patient Appointment']
      }
    }
  },
  validate(params) {
    error.value = null
    if (!params.doc.patient_name && !params.doc.patient) {
      error.value = 'Patient or Patient Name is required'
      return error.value
    }
    if (!params.doc.practitioner) {
      error.value = 'Practitioner is required'
      return error.value
    }
    if (!params.doc.appointment_type) {
      error.value = 'Appointment Type is required'
      return error.value
    }
    if (!params.doc.appointment_date) {
      error.value = 'Appointment Date is required'
      return error.value
    }
    if (!params.doc.appointment_time) {
      error.value = 'Appointment Time is required'
      return error.value
    }
    isCreating.value = true
  },
  onSuccess: (data) => {
    isCreating.value = false
    notifications.success.appointmentCreated()
    closeDialog()
    resetAppointment()
    emit('appointmentCreated')
  },
  onError: (err) => {
    isCreating.value = false
    if (!err.messages) {
      error.value = err.message
      return
    }
    error.value = err.messages.join('\n')
  }
})

const patient_doc = createResource({
  url: 'frappe.client.insert',
  method: 'POST',
  makeParams() {
    return {
      doc: {
        doctype: 'Patient',
        ...appointment['Patient']
      }
    }
  },
  validate(params) {
    error.value = null
    if (!params.doc.first_name) {
      error.value = 'First Name is required'
      return error.value
    }
    if (!params.doc.last_name) {
      error.value = 'Last Name is required'
      return error.value
    }
    if (!params.doc.sex) {
      error.value = 'Sex is required'
      return error.value
    }
    if (!params.doc.dob) {
      error.value = 'Date of Birth is required'
      return error.value
    }
  },
  onSuccess: (data) => {
    appointment['Patient Appointment']['patient'] = data.name
    appointment['Patient Appointment']['patient_name'] = `${data.first_name} ${data.last_name}`
    appointment['Healthcare Insurance Subscription']['patient'] = data.name
    appointment['Healthcare Insurance Subscription']['patient_name'] = `${data.first_name} ${data.last_name}`
    console.log('Patient created successfully')
  },
  onError: (err) => {
    if (!err.messages) {
      error.value = err.message
      return
    }
    error.value = err.messages.join('\n')
  }
})

const insurance_doc = createResource({
  url: 'frappe.client.insert',
  method: 'POST',
  makeParams() {
    return {
      doc: {
        doctype: 'Healthcare Insurance Subscription',
        ...appointment['Healthcare Insurance Subscription']
      }
    }
  },
  validate(params) {
    error.value = null
    if (!params.doc.patient) {
      error.value = 'Patient is required'
      return error.value
    }
    if (!params.doc.insurance_company) {
      error.value = 'Insurance Company is required'
      return error.value
    }
    if (!params.doc.healthcare_insurance_coverage_plan) {
      error.value = 'Coverage Plan is required'
      return error.value
    }
  },
  onSuccess: (data) => {
    appointment['Patient Appointment']['insurance_subscription'] = data.name
    console.log('Insurance subscription created successfully')
  },
  onError: (err) => {
    if (!err.messages) {
      error.value = err.message
      return
    }
    error.value = err.messages.join('\n')
  }
})

async function create_appointment_docs() {
  isCreating.value = true
  error.value = null

  try {
    if (appointment['Patient Appointment']['is_new_patient']) {
      statusMessage.value = 'Creating patient...'
      await patient_doc.submit()
    }

    if (appointment['Patient Appointment']['is_new_his']) {
      statusMessage.value = 'Creating insurance subscription...'
      await insurance_doc.submit()
    }

    statusMessage.value = 'Creating appointment...'
    await appointment_doc.submit()

  } catch (err) {
    error.value = 'Error while creating appointment documents'
  } finally {
    isCreating.value = false
  }
}

const handleSubmit = async () => {
  error.value = ''
  
  if (!validateForm()) {
    error.value = 'Please fill in all required fields correctly.'
    return
  }
  
  await create_appointment_docs()
}

const editAppointment = () => {
  // For legacy support
  if (appointmentStore.dialogMode) {
    appointmentStore.dialogMode = 'edit'
  }
}

const closeDialog = () => {
  localShowDialog.value = false
  resetAppointment()
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

