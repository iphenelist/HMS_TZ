<template>
    <div class="flex flex-col gap-6">
      <div
        v-for="section in sections"
        :key="section.label"
        class="first:border-t-0 first:pt-0"
        :class="section.hideBorder ? '' : 'border-t pt-4'"
      >
        <div
          v-if="!section.hideLabel && section.doctype == 'Patient Appointment'"
          class="flex h-7 mb-3 max-w-fit cursor-pointer items-center gap-2 text-xl font-bold text-blue-700 font-mono leading-5"
        >
          {{ section.label }}
        </div>
        <div
          class="grid gap-6"
          :class="
            section.columns
              ? 'grid-cols-' + section.columns
              : 'grid-cols-3 sm:grid-cols-3'
          "
          v-if="section.doctype == 'Patient Appointment'"
        >
          <Fields :section="section" :data="data" />
        </div>
        <div
          v-if="!section.hideLabel && section.doctype == 'Patient' && data['Patient Appointment']['is_new_patient']"
          class="flex h-7 mb-3 max-w-fit cursor-pointer items-center gap-2 text-xl font-bold text-blue-700 font-mono leading-5"
        >
          {{ section.label }}
        </div>
        <div
          class="grid gap-4"
          :class="
            section.columns
              ? 'grid-cols-' + section.columns
              : 'grid-cols-3 sm:grid-cols-3'
          "
          v-if="section.doctype == 'Patient' && data['Patient Appointment']['is_new_patient']"
        >
          <Fields :section="section" :data="data" />
        </div>
        <div
          v-if="!section.hideLabel && section.doctype == 'Healthcare Insurance Subscription' && data['Patient Appointment']['is_new_his']"
          class="flex h-7 mb-3 max-w-fit cursor-pointer items-center gap-2 text-xl font-bold text-blue-700 font-mono leading-5"
        >
          {{ section.label }}
        </div>
        <div
          class="grid gap-4"
          :class="
            section.columns
              ? 'grid-cols-' + section.columns
              : 'grid-cols-3 sm:grid-cols-3'
          "
          v-if="section.doctype == 'Healthcare Insurance Subscription' && data['Patient Appointment']['is_new_his']"
        >
          <Fields :section="section" :data="data" />
        </div>
      </div>
    </div>
  </template>
  
  <script setup>
  import Fields from './Fields.vue';
  
  const props = defineProps({
    sections: Array,
    data: Object,
  })
  
  </script>
  
  <style scoped>
  :deep(.form-control.prefix select) {
    padding-left: 2rem;
  }
  </style>
