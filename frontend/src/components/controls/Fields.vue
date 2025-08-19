<template>
  <div v-for="field in props.section.fields" :key="field.name">
    <div
      v-if="field.type != 'Check'"
      class="mb-2 text-base text-gray-900 font-semibold"
    >
      {{ field.label}}
      <span 
        class="text-red-500 text-xl"
        v-if="field.reqd && !((field.name === 'patient' && data['Patient Appointment']['is_new_patient']) || (field.name === 'insurance_subscription' && data['Patient Appointment']['is_new_his']))"
      >
        *
      </span>
    </div>
    <FormControl
      v-if="field.read_only && field.type !== 'Check'"
      type="text"
      :placeholder="field.placeholder || field.label"
      v-model="data[section.doctype][field.name]"
      :disabled="true"
      variant="outline"
    />
    <Select
      v-else-if="field.type === 'Select'"
      :options="field.options"
      v-model="data[section.doctype][field.name]"
      :placeholder="field.placeholder || field.label"
    />
    <Checkbox
      v-else-if="field.type === 'Check'"
      v-model="data[section.doctype][field.name]"
      :label="field.label"
      :disabled="Boolean(field.read_only)"
      @change="(e) => updateCheckValue(section.doctype, field.name, e.target.checked)"
      :required="field.reqd"
    />
    <Link
      v-else-if="field.type === 'Link' "
      class="form-control"
      :value="data[section.doctype][field.name]"
      :doctype="field.options"
      @change="(v) => handleLinkChange(section.doctype, field.name, field.options, v)"
      :placeholder="field.placeholder || field.label"
      :onCreate="field.create"
      :disabled="(field.name === 'patient' && data['Patient Appointment']['is_new_patient']) || (field.name === 'insurance_subscription' && data['Patient Appointment']['is_new_his'])"
    />
    <DatePicker
      v-else-if="field.type === 'Date'"
      v-model="data[section.doctype][field.name]"
      :placeholder="field.placeholder || field.label"
    />
    <FormControl
      v-else-if="field.type === 'Time'"
      type="time"
      :placeholder="field.placeholder || field.label"
      v-model="data[section.doctype][field.name]"
    />
    <FormControl
      v-else-if="
        ['Small Text', 'Text', 'Long Text'].includes(field.type)
      "
      type="textarea"
      :placeholder="field.placeholder || field.label"
      v-model="data[section.doctype][field.name]"
      :value="data[section.doctype][field.name]"
      @input="(e) => updateField(section.doctype, field.name, e.target.value)"
    />
    <FormControl
      v-else-if="['Int'].includes(field.type)"
      type="number"
      :placeholder="field.placeholder || field.label"
      v-model="data[section.doctype][field.name]"
      @input="(e) => updateField(section.doctype, field.name, e.target.value)"
    />
    <FormControl
      v-else
      type="text"
      :placeholder="field.placeholder || field.label"
      :value="data[section.doctype][field.name]"
      v-model="data[section.doctype][field.name]"
      @input="(e) => updateField(section.doctype, field.name, e.target.value)"
      :disabled="Boolean(field.read_only)"
    />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { createResource } from 'frappe-ui'
import Link from './Link.vue';

const props = defineProps({
  section: Object,
  data: Object,
})


// Resource to fetch patient details
const patientResource = createResource({
  url: 'frappe.client.get',
  method: 'GET',
  onSuccess: (data) => {
    if (data && data.patient_name) {
      // Set the patient_name field in the Patient Appointment doctype
      if (props.data['Patient Appointment']) {
        props.data['Patient Appointment']['patient_name'] = data.patient_name
      }
      // Also set in Healthcare Insurance Subscription if it exists
      if (props.data['Healthcare Insurance Subscription']) {
        props.data['Healthcare Insurance Subscription']['patient_name'] = data.patient_name
      }
    }
  },
  onError: (error) => {
    console.error('Error fetching patient details:', error)
  }
})


// Handle Link field changes with special logic for patient field
function handleLinkChange(doctype, fieldName, linkDoctype, value) {
  // Update the field value
  const data = props.data;
  if (data[doctype]) {
    data[doctype][fieldName] = value;
  }
  
  // Special handling for patient field
  if (fieldName === 'patient' && linkDoctype === 'Patient') {
    if (value) {
      // Fetch patient details to get patient_name
      patientResource.submit({
        doctype: 'Patient',
        name: value
      })
      
      // Sync patient field to Healthcare Insurance Subscription if selecting from Patient Appointment
      if (doctype === 'Patient Appointment' && data['Healthcare Insurance Subscription']) {
        data['Healthcare Insurance Subscription']['patient'] = value
      }
    } else {
      // Clear patient_name when patient is cleared
      if (data['Patient Appointment']) {
        data['Patient Appointment']['patient_name'] = ''
      }
      if (data['Healthcare Insurance Subscription']) {
        data['Healthcare Insurance Subscription']['patient_name'] = ''
        // Also clear the patient field in Healthcare Insurance Subscription if clearing from Patient Appointment
        if (doctype === 'Patient Appointment') {
          data['Healthcare Insurance Subscription']['patient'] = ''
        }
      }
    }
  }
}

function updateField(doctype, name, value) {
  const data = props.data;
  if (data[doctype]) {  
    data[doctype][name] = value;
  }
}

function updateCheckValue(doctype, name, value) {
  const data = props.data;
  if (data[doctype]) {
    data[doctype][name] = value;
  }
  if (data['Patient Appointment']['is_new_patient']) {
    data['Patient Appointment']['patient'] = '';
  }
  if (data['Patient Appointment']['is_new_his']) {
    data['Patient Appointment']['insurance_subscription'] = '';
  }
}
</script>

<style scoped>
:deep(.form-control.prefix select) {
  padding-left: 2rem;
}
</style>
