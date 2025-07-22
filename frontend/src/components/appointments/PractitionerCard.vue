<template>
  <div class="practitioner-card">
    <div class="flex flex-col items-center p-2 bg-white border border-gray-200 
      rounded-lg hover:bg-gray-50 transition-colors w-32 h-auto overflow-hidden">
      <!-- Avatar on top -->
      <div class="mb-2 flex-shrink-0">
        <Avatar
          :label="practitioner.avatar"
          :image="practitioner.image"
          size="md"
          :class="practitioner.image ? 'ring-2 ring-green-300 !w-10 !h-10' : 'ring-2 ring-sky-300 !w-10 !h-10'"
        />
      </div>
      
      <!-- Practitioner Info -->
      <div class="text-center w-full flex-1 min-h-0">
        <h3 class="text-xs font-semibold text-black truncate mb-1 leading-tight">
          {{ practitioner.name }}
        </h3>
        <p class="text-xs text-gray-600 truncate leading-tight">
          {{ practitioner.specialty }}
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { Avatar, Badge } from 'frappe-ui'

const props = defineProps({
  practitioner: {
    type: Object,
    required: true
  }
})
</script>

<style scoped>
.practitioner-card {
  @apply transition-all duration-200;
}

.practitioner-card:hover {
  @apply transform translate-y-[-1px];
}
</style>
