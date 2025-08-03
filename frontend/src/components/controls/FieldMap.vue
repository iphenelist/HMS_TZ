<template>
    <div class="flex flex-col gap-6">
      <template v-for="section in sections" :key="section.label">
        <div
          v-if="shouldShowSection(section)"
          class="first:border-t-0 first:pt-0"
          :class="section.hideBorder ? '' : 'border-t pt-4'"
        >

          <!-- Section Label -->
          <div
            v-if="!section.hideLabel"
            class="flex h-7 mb-3 max-w-fit cursor-pointer items-center gap-2 text-xl font-bold text-blue-700 font-mono leading-5"
          >
            {{ section.label }}
          </div>

          <!-- Section Fields -->
          <div
            class="grid gap-4"
            :class="
              section.columns
                ? 'grid-cols-' + section.columns
                : 'grid-cols-2 sm:grid-cols-2'
            "
          >
            <Fields :section="section" :data="data" />
          </div>
        </div>
      </template>
    </div>
  </template>
  
  <script setup>
  import Fields from './Fields.vue';
  
  const props = defineProps({
    sections: Array,
    data: Object,
  })
  
  // Determine if a section should be shown based on business logic
  const shouldShowSection = (section) => {
    // Always show Initial Data section
    if (section.label === 'Initial Data') {
      return true
    }
    
    // Show Patient Details only if 'Is New Patient' equals 1 or true
    if (section.doctype === 'Patient') {
      const isNewPatient = props.data?.['Patient Appointment']?.['is_new_patient']
      return isNewPatient === 1 || isNewPatient === true
    }
    
    // Show Insurance Subscription only if 'Is New HIS' equals 1 or true
    if (section.doctype === 'Healthcare Insurance Subscription') {
      const isNewHis = props.data?.['Patient Appointment']?.['is_new_his']
      return isNewHis === 1 || isNewHis === true
    }
    
    // Show Patient Appointment sections (Appointment Details)
    if (section.doctype === 'Patient Appointment' && section.label !== 'Initial Data') {
      return true
    }
    
    return true // Default: show all other sections
  }
  
  </script>
  
  <style scoped>
  :deep(.form-control.prefix select) {
    padding-left: 2rem;
  }
  </style>
