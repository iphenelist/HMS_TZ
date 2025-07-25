<template>
  <div 
    class="appointment-card cursor-pointer transition-all duration-200 hover:shadow-md"
    :class="cardStyleClasses"
    @click="$emit('click', appointment)"
  >
    <div class="p-3 h-full">
      <!-- Patient Name -->
      <h4 class="text-sm font-semibold text-gray-900 truncate mb-1">
        {{ appointment.patient_name }}
      </h4>
      
      <!-- Insurance Company -->
      <div class="flex items-center text-xs text-gray-600 mb-1">
        <FeatherIcon name="shield" class="h-3 w-3 mr-1" />
        <span class="truncate">{{ appointment.insurance_company || 'Cash' }}</span>
      </div>
      
      <!-- Billing Item -->
      <div v-if="appointment.billing_item" class="flex items-center text-xs text-gray-600 mb-1">
        <FeatherIcon name="file-text" class="h-3 w-3 mr-1" />
        <span class="truncate">{{ appointment.billing_item }}</span>
      </div>
      
      <!-- Paid Amount / Item Rate -->
      <div class="flex items-center text-xs text-gray-600 mb-2">
        <FeatherIcon name="dollar-sign" class="h-3 w-3 mr-1" />
        <span>{{ formatAmount(appointment.paid_amount || appointment.item_rate || 0) }}</span>
      </div>
      
      <!-- Time Display -->
      <div class="flex items-center text-xs text-gray-500 mb-2">
        <FeatherIcon name="clock" class="h-3 w-3 mr-1" />
        <span>{{ formatTime(appointment.time_slot) }}</span>
      </div>
      
      <!-- Status Badge -->
      <div class="flex items-center justify-between">
        <Badge
          :label="formatStatus(appointment.status)"
          :theme="getStatusTheme(appointment.status)"
          size="sm"
        />
        
        <!-- Quick Actions -->
        <div class="flex items-center space-x-1 opacity-0 group-hover:opacity-100 transition-opacity">
          <Tooltip 
            v-if="appointment.status === 'scheduled'"
            text="Mark as completed"
            placement="top"
          >
            <Button
              variant="ghost"
              size="sm"
              @click.stop="$emit('complete', appointment)"
              class="p-1"
            >
              <FeatherIcon name="check" class="h-3 w-3 text-green-600" />
            </Button>
          </Tooltip>
          
          <Tooltip 
            v-if="appointment.status !== 'cancelled'"
            text="Cancel appointment"
            placement="top"
          >
            <Button
              variant="ghost"
              size="sm"
              @click.stop="$emit('cancel', appointment)"
              class="p-1"
            >
              <FeatherIcon name="x" class="h-3 w-3 text-red-600" />
            </Button>
          </Tooltip>
        </div>
      </div>
      
      <!-- Notes Preview -->
      <div v-if="appointment.notes" class="mt-2 pt-2 border-t border-gray-200">
        <p class="text-xs text-gray-500 truncate" :title="appointment.notes">
          {{ appointment.notes }}
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { FeatherIcon, Badge, Button, Tooltip } from 'frappe-ui'
import dayjs from 'dayjs'

const props = defineProps({
  appointment: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['click', 'complete', 'cancel'])

// Status-based styling
const cardStyleClasses = computed(() => {
  const baseClasses = 'w-full h-full rounded-lg border-2 group'
  
  switch (props.appointment.status) {
    case 'open':
      return `${baseClasses} bg-gray-100 border-gray-300 hover:bg-gray-200`
    case 'completed':
      return `${baseClasses} bg-green-100 border-green-400 hover:bg-green-200`
    case 'scheduled':
      return `${baseClasses} bg-orange-100 border-orange-400 hover:bg-orange-200`
    case 'cancelled':
      return `${baseClasses} bg-red-100 border-red-400 hover:bg-red-200`
    default:
      return `${baseClasses} bg-gray-100 border-gray-300 hover:bg-gray-200`
  }
})

const getStatusTheme = (status) => {
  const themeMap = {
    open: 'gray',
    completed: 'green',
    scheduled: 'orange',
    cancelled: 'red'
  }
  return themeMap[status] || 'gray'
}

// Helper functions
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

const formatAmount = (amount) => {
  if (!amount || amount === 0) return 'TZS 0'
  return `TZS ${Number(amount).toLocaleString()}`
}
</script>

<style scoped>
.appointment-card {
  min-height: 100%;
}
</style>
