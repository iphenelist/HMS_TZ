<template>
  <div v-for="field in visibleFields" :key="field.name">
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
      @change="(v) => (data[section.doctype][field.name] = v)"
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
import Link from './Link.vue';

const props = defineProps({
  section: Object,
  data: Object,
})

// Computed property to filter visible fields based on payment mode
const visibleFields = computed(() => {
  const paymentMode = props.data?.['Patient Appointment']?.['payment_mode']
  
  if (!paymentMode) {
    // If payment mode is empty, only show payment_mode field
    return props.section.fields.filter(field => field.name === 'payment_mode')
  }
  
  if (paymentMode === 'Cash') {
    // Hide insurance-related fields when payment mode is Cash
    const insuranceFields = [
      'insurance_provider', 'card_no', 'national_id', 
      'insurance_company', 'healthcare_insurance_coverage_plan',
      'is_new_his', 'insurance_subscription', 'referral_no', 'remarks'
    ]
    return props.section.fields.filter(field => !insuranceFields.includes(field.name))
  }
  
  // For Insurance payment mode, show all fields
  return props.section.fields
})

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
