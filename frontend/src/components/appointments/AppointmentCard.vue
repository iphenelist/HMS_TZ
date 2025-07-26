<template>
  <div 
    class="appointment-card cursor-pointer transition-all duration-200 hover:shadow-md w-full h-full"
    :class="cardStyleClasses"
    @click="$emit('click', appointment)"
  >
    <div class="p-2 h-full flex flex-col justify-between">
      <!-- Patient Name -->
      <h4 class="text-sm font-bold text-gray-900 truncate mb-1 leading-tight">
        {{ appointment.patient_name }}
      </h4>
      
      <!-- Insurance Company -->
      <div class="flex items-center text-xs text-gray-800 mb-1">
        <FeatherIcon name="shield" class="h-3 w-3 mr-1 flex-shrink-0" />
        <span class="truncate text-xs font-semibold">{{ appointment.insurance_company || 'Cash' }}</span>
      </div>
      
      <!-- Billing Item -->
      <div v-if="appointment.billing_item" class="flex items-center text-xs text-gray-800 mb-1">
        <FeatherIcon name="file-text" class="h-3 w-3 mr-1 flex-shrink-0" />
        <span class="truncate text-xs font-semibold">{{ appointment.billing_item }}</span>
      </div>
      
      <!-- Paid Amount / Item Rate -->
      <div class="flex items-center text-xs text-gray-800 mb-1">
        <FeatherIcon name="dollar-sign" class="h-3 w-3 mr-1 flex-shrink-0" />
        <span class="text-xs font-bold">{{ formatAmount(appointment.paid_amount || appointment.item_rate || 0) }}</span>
      </div>
      
      <!-- Time Display -->
      <div class="flex items-center text-xs text-gray-700 mb-2">
        <FeatherIcon name="clock" class="h-3 w-3 mr-1 flex-shrink-0" />
        <span class="text-xs font-semibold">{{ formatTime(appointment.time_slot) }}</span>
      </div>
      
      <!-- Status Badge and Actions -->
      <div class="flex items-center justify-between">
        <Badge
          :label="formatStatus(appointment.status)"
          :theme="getStatusTheme(appointment.status)"
          size="sm"
          class="text-xs font-bold"
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
      <div v-if="appointment.notes" class="mt-1 pt-1 border-t border-gray-400">
        <p class="text-xs text-gray-800 truncate font-medium" :title="appointment.notes">
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
  const baseClasses = 'rounded-md border-2 group shadow-sm'
  
  switch (props.appointment.status) {
    case 'open':
      return `${baseClasses} bg-yellow-200 border-yellow-500 hover:bg-yellow-300`
    case 'completed':
    case 'closed':
      return `${baseClasses} bg-green-200 border-green-500 hover:bg-green-300`
    case 'scheduled':
      return `${baseClasses} bg-orange-200 border-orange-500 hover:bg-orange-300`
    case 'cancelled':
      return `${baseClasses} bg-red-200 border-red-500 hover:bg-red-300`
    default:
      return `${baseClasses} bg-gray-200 border-gray-400 hover:bg-gray-300`
  }
})

const getStatusTheme = (status) => {
  const themeMap = {
    open: 'yellow',
    completed: 'green',
    closed: 'green',
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
    closed: 'Closed',
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
