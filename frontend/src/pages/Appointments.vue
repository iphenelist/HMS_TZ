<template>
  <div class="appointment-page min-h-screen bg-gray-50">
    <AppointmentGrid />
  </div>
</template>

<script setup>
import AppointmentGrid from '@/components/appointments/AppointmentGrid.vue'
import { usePageMeta } from 'frappe-ui'


usePageMeta(() => {
  return {
    title: 'Appointments - HMS TZ',
    description: 'Manage appointments and practitioner schedules'
  }
})
</script>
