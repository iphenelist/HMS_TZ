<template>
  <Dialog
    :model-value="localShowDialog"
    @update:model-value="updateDialogState"
    :options="{
      title: dialogTitle,
      size: '2xl',
      icon: {
        name: 'book',
        appearance: 'black',
      },
    }"
    :disable-outside-click-to-close="true"
    class="appointment-dialog-overlay z-[1050]"
  >

    <!-- <template #body-title>
      <div class="flex gap-36 items-center justify-center mb-0">
        <div class="w-112 mb-4 justify-center">
          <h3 class="flex justify-center text-2xl text-center font-semibold leading-6 text-gray-900">
            {{ dialogTitle }}
          </h3>
        </div>
      </div>
    </template> -->
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
            <FieldMap 
              v-if="sections" 
              :sections="sections" 
              :data="appointment" 
            />
            <div v-if="error" class="mt-4 text-lg font-bold text-red-600">{{ error }}</div>
          </div>
        </div>
      </div>
    </template>
    
    <template #actions>
      <div class="flex gap-2 justify-end">
        <template v-if="isViewMode">
          <Button 
            variant="outline" 
            size="sm"
            @click="closeDialog()"
          >
            Close
          </Button>
          
          <Button 
            v-if="appointment['Patient Appointment']['status'] !== 'cancelled'"
            variant="outline" 
            size="sm"
            @click="editAppointment()"
          >
            Edit
          </Button>
          
          <Button 
            v-if="appointment['Patient Appointment']['status'] === 'scheduled'"
            variant="solid" 
            size="sm"
            theme="green"
            @click="completeAppointment()"
          >
            Mark Complete
          </Button>
          
          <Button 
            v-if="appointment['Patient Appointment']['status'] !== 'cancelled'"
            variant="outline" 
            size="sm"
            theme="red"
            @click="showCancelConfirmation()"
          >
            Cancel
          </Button>
        </template>
        
        <template v-else>
          <Button 
            variant="subtle" 
            size="sm"
            theme="gray"
            @click="closeDialog()"
          >
            Cancel
          </Button>
          
          <Button 
            variant="solid" 
            size="sm"
            :loading="isCreating"
            @click="handleSubmit()"
          >
            {{ isCreateMode ? 'Create' : 'Update' }}
          </Button>
        </template>
      </div>
    </template>
  </Dialog>
</template>



<script setup>
import { computed, reactive, watch, ref, nextTick, onUnmounted } from 'vue'
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
const emit = defineEmits(['update:showDialog', 'closeDialog', 'appointmentCreated', 'editAppointment'])

const appointmentStore = useAppointmentStore()
const practitionerStore = usePractitionerStore()
const dateStore = useDateStore()

// Local dialog state for v-model approach
const localShowDialog = ref(props.showDialog)
const isCreating = ref(false)
const statusMessage = ref('')
const error = ref('')

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
      "card_no": "",
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

// Computed property to reorder sections with "Initial Data" first
const sections = computed(() => {
  const paymentMode = appointment['Patient Appointment']['payment_mode']
  
  // Helper function to filter fields based on payment mode
  const filterFieldsByPaymentMode = (fields, doctype) => {
    if (!paymentMode) {
      // If payment mode is empty, only show payment_mode field
      return fields.filter(field => field.name === 'payment_mode')
    }
    
    if (paymentMode === 'Cash') {
      // Hide insurance-related fields when payment mode is Cash
      const insuranceFields = [
        'insurance_provider', 'card_no', 'national_id', 
        'insurance_company', 'healthcare_insurance_coverage_plan',
        'is_new_his', 'insurance_subscription', 'referral_no', 'remarks'
      ]
      return fields.filter(field => !insuranceFields.includes(field.name))
    }
    
    // For Insurance payment mode, show all fields
    return fields
  }
  
  const allSections = [
    // Initial Data section - always first
    {
      "label": "Initial Data",
      "doctype": "Patient Appointment",
      "fields": filterFieldsByPaymentMode([
        {
          "name": "payment_mode",
          "label": "Payment Mode",
          "type": "Select",
          "options": [
            { "label": "", "value": "" },
            { "label": "Cash", "value": "Cash" },
            { "label": "Insurance", "value": "Insurance" },
          ],
          "reqd": true
        },
        { 
          "name": "insurance_provider",
          "label": "Insurance Provider",
          "type": "Select",
          "options": [
            { "label": "", "value": "" },
            { "label": "NHIF", "value": "NHIF" },
            { "label": "Jubilee", "value": "Jubilee" },
          ],
          "placeholder": "for API triggering",
          "reqd": false
        },
        {
          "name": "card_no",
          "label": "Card No",
          "type": "Data",
          "placeholder": "Card No",
          "reqd": false
        },
        {
          "name": "national_id",
          "label": "National ID",
          "type": "Data",
          "placeholder": "National ID",
          "reqd": false
        }
      ], "Patient Appointment"),
      "columns": 2,
      "hideLabel": true,
    },
    // Other sections
    {
        "label":"Patient Details",
        "doctype":"Patient",
        "fields": filterFieldsByPaymentMode([
            {
              "name": "first_name",
              "label": "First Name",
              "type": "Data",
              "placeholder": "First Name",
              "reqd": true
            },
            {
              "name": "middle_name",
              "label": "Middle Name",
              "type": "Data",
              "placeholder": "Middle Name",
              "reqd": false
            },
            {
              "name": "last_name",
              "label": "Last Name",
              "type": "Data",
              "placeholder": "Last Name",
              "reqd": true
            },
            {
              "name": "sex",
              "label": "Sex",
              "type": "Select",
              "placeholder": "Sex",
              "options": [
                {"label": "Male", "value": "Male"},
                {"label": "Female", "value": "Female"},
              ],
              "reqd": true
            },
            {
              "name": "dob",
              "label": "Date of Birth",
              "type": "Date",
              "placeholder": "Date of Birth",
              "reqd": true
            },
            {
              "name": "mobile",
              "label": "Mobile",
              "type": "Int",
              "placeholder": "Mobile",
              "reqd": true
            },
            {
              "name": "next_to_kin_name",
              "label": "Next of Kin Name",
              "type": "Data",
              "placeholder": "Next of Kin Name",
              "reqd": false
            },
            {
              "name": "next_to_kin_mobile_no",
              "label": "Next of Kin Mobile",
              "type": "Data",
              "placeholder": "Next of Kin Mobile",
              "reqd": false
            },
            {
              "name": "next_to_kin_relationship",
              "label": "Next of Kin Relationship",
              "type": "Data",
              "placeholder": "Next of Kin Relationship",
              "reqd": false
            },
        ], "Patient"),
        "columns": 3,
        "hideLabel":false,
        "hideBorder":false
    },
    {
        "label":"Healthcare Insurance Subscription",
        "doctype":"Healthcare Insurance Subscription", 
        "fields": filterFieldsByPaymentMode([
            {
              "name": "insurance_company",
              "label": "Insurance Company",
              "type": "Link",
              "placeholder": "Insurance Company",
              "options": "Healthcare Insurance Company",
              "reqd": true
            },
            {
              "name": "healthcare_insurance_coverage_plan",
              "label": "Coverage Plan",
              "type": "Link",
              "placeholder": "Coverage Plan",
              "options": "Healthcare Insurance Coverage Plan",
              "reqd": true
            },
        ], "Healthcare Insurance Subscription"),
        "columns": 2,
        "hideLabel":false,
        "hideBorder":false
    },
    {
        "label":"Appointment Details",
        "doctype":"Patient Appointment",
        "fields": filterFieldsByPaymentMode([
            {
              "name": "is_new_patient",
              "label": "Is New Patient",
              "type": "Check",
              "placeholder": "Is New Patient",
              "reqd": false
            },
            {
              "name": "patient",
              "label": "Patient",
              "type": "Link",
              "placeholder": "Patient",
              "options": "Patient",
              "reqd": true
            },
            {
              "name": "patient_name",
              "label": "Patient Name",
              "type": "Data",
              "placeholder": "Patient Name",
              "reqd": false,
              "read_only": true
            },
            {
              "name": "practitioner",
              "label": "Practitioner",
              "type": "Link",
              "placeholder": "Practitioner",
              "options": "Healthcare Practitioner",
              "reqd": true
            },
            {
              "name": "appointment_type",
              "label": "Appointment Type",
              "type": "Link",
              "placeholder": "Appointment Type",
              "options": "Appointment Type",
              "reqd": true
            },
            {
              "name": "appointment_date",
              "label": "Appointment Date",
              "type": "Date",
              "placeholder": "Appointment Date",
              "reqd": true
            },
            {
              "name": "appointment_time",
              "label": "Appointment Time",
              "type": "Time",
              "placeholder": "Appointment Time",
              "reqd": true
            },
            {
              "name": "is_new_his",
              "label": "Is New HIS",
              "type": "Check",
              "placeholder": "Is New HIS",
              "reqd": false
            },
            {
              "name": "insurance_subscription",
              "label": "Insurance Subscription",
              "type": "Link",
              "placeholder": "Insurance Subscription",
              "options": "Healthcare Insurance Subscription",
              "reqd": false
            },
            {
              "name": "referral_no",
              "label": "Referral No",
              "type": "Data",
              "placeholder": "Referral No",
              "reqd": false
            },
            {
              "name": "remarks",
              "label": "Remarks",
              "type": "Small Text",
              "placeholder": "Remarks",
              "reqd": false
            }
        ], "Patient Appointment"),
        "columns": 3,
        "hideLabel":false,
        "hideBorder":false
    }
  ]
  
  // Filter sections based on payment mode
  if (!paymentMode) {
    // If payment mode is empty, only show Initial Data section
    return allSections.filter(section => section.label === "Initial Data")
  }
  
  if (paymentMode === 'Cash') {
    // For Cash payment mode, hide Healthcare Insurance Subscription section
    return allSections.filter(section => section.doctype !== "Healthcare Insurance Subscription")
  }
  
  // For Insurance payment mode, show all sections
  return allSections
})


// Dialog state update handler
const updateDialogState = (newVal) => {
  if (localShowDialog.value === newVal) return // Prevent unnecessary updates
  
  localShowDialog.value = newVal
  emit('update:showDialog', newVal)
  
  if (newVal) {
    // Dialog is opening - ensure popovers appear above dialog
    ensurePopoverZIndex()
  } else {
    // Dialog is closing - restore normal popover z-index
    restorePopoverZIndex()
    emit('closeDialog')
    resetAppointment()
  }
}

// Utility functions to manage popover z-index
let popoverObserver = null

const ensurePopoverZIndex = () => {
  nextTick(() => {
    const popoverRoot = document.getElementById('frappeui-popper-root')
    if (popoverRoot) {
      popoverRoot.style.zIndex = '1080'
      // Also apply to any existing popover content
      const popoverElements = popoverRoot.querySelectorAll('*')
      popoverElements.forEach(el => {
        if (el.classList.contains('z-[100]') || el.style.zIndex) {
          el.style.zIndex = '1080'
        }
      })
      
      // Set up mutation observer to handle dynamically created popovers
      if (!popoverObserver) {
        popoverObserver = new MutationObserver((mutations) => {
          mutations.forEach((mutation) => {
            mutation.addedNodes.forEach((node) => {
              if (node.nodeType === Node.ELEMENT_NODE) {
                // Apply z-index to new popover elements
                if (node.classList?.contains('z-[100]')) {
                  node.style.zIndex = '1080'
                }
                // Also check children
                const childPopovers = node.querySelectorAll?.('.z-\\[100\\]')
                childPopovers?.forEach(child => {
                  child.style.zIndex = '1080'
                })
              }
            })
          })
        })
        
        popoverObserver.observe(popoverRoot, {
          childList: true,
          subtree: true
        })
      }
    }
    
    // Apply to any existing bootstrap popovers
    const bootstrapPopovers = document.querySelectorAll('.popover')
    bootstrapPopovers.forEach(el => {
      el.style.zIndex = '1080'
    })
  })
}

const restorePopoverZIndex = () => {
  nextTick(() => {
    // Disconnect the mutation observer
    if (popoverObserver) {
      popoverObserver.disconnect()
      popoverObserver = null
    }
    
    const popoverRoot = document.getElementById('frappeui-popper-root')
    if (popoverRoot) {
      popoverRoot.style.zIndex = ''
      // Restore original z-index for popover content
      const popoverElements = popoverRoot.querySelectorAll('*')
      popoverElements.forEach(el => {
        if (el.style.zIndex === '1080') {
          el.style.zIndex = ''
        }
      })
    }
    
    // Restore bootstrap popovers
    const bootstrapPopovers = document.querySelectorAll('.popover')
    bootstrapPopovers.forEach(el => {
      if (el.style.zIndex === '1080') {
        el.style.zIndex = ''
      }
    })
  })
}

// Watch for dialog state changes - v-model approach
watch(() => props.showDialog, (newVal, oldVal) => {
  // Only update if there's an actual change and it's different from local state
  if (oldVal !== newVal && newVal !== localShowDialog.value) {
    localShowDialog.value = newVal
    if (newVal) {
      // Dialog is opening
      ensurePopoverZIndex()
      // Use nextTick for immediate opening
      nextTick(() => {
        resetAppointment()
        error.value = ''
        if (props.appointment && Object.keys(props.appointment).length > 0) {
        } else if (isCreateMode.value) {
          // Pre-fill data for create mode
          appointment['Patient Appointment']['appointment_time'] = props.timeSlot
          appointment['Patient Appointment']['practitioner'] = props.practitionerData?.name
          appointment['Patient Appointment']['appointment_date'] = dateStore.selectedDate
        }
      })
    } else {
      // Dialog is closing
      restorePopoverZIndex()
    }
  }
}, { immediate: false })

// Watch for dialog prop changes (v-model approach)


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
  // Switch to edit mode - handled by parent component
  emit('editAppointment')
}

const closeDialog = () => {
  updateDialogState(false)
}

const completeAppointment = async () => {
  try {
    const appointmentId = props.appointment?.id
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
    const appointmentId = props.appointment?.id
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

// Cleanup on component unmount
onUnmounted(() => {
  if (popoverObserver) {
    popoverObserver.disconnect()
    popoverObserver = null
  }
  // Restore popover z-index when component is destroyed
  restorePopoverZIndex()
})
</script>

<style scoped>
/*
 * Strategic z-index layering to ensure proper dialog visibility
 * while preserving dropdown functionality inside the dialog
 */

/* Base dialog styling - appears above page elements but below dropdowns */
:deep(.dialog) {
  z-index: 1050 !important;
}

:deep(.dialog-wrapper) {
  z-index: 1050 !important;
}

/* Dialog backdrop - below dialog content */
:deep(.dialog-overlay) {
  z-index: 1040 !important;
}

/* Dialog content - main dialog layer */
:deep(.dialog-content) {
  z-index: 1055 !important;
}

/* Additional targeting for Frappe UI dialog components */
:deep([role="dialog"]) {
  z-index: 1055 !important;
}

/* Fixed backdrop elements */
:deep(.fixed.inset-0) {
  z-index: 1040 !important;
}

/* Modal backdrop */
:deep(.modal-backdrop) {
  z-index: 1035 !important;
}

/* Ensure dialog container has proper layering */
:deep(.modal) {
  z-index: 1055 !important;
}

/* Frappe-specific dialog wrapper */
:deep(.frappe-dialog) {
  z-index: 1055 !important;
}

/* Base dialog wrapper styling */
.appointment-dialog-overlay {
  z-index: 1050 !important;
}

/* Custom actions styling */
:deep(.dialog .actions) {
  padding: 1rem !important;
}
</style>
