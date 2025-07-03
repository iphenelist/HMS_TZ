<template>
  <div class="appointment-grid-container min-h-screen bg-gray-100">
    <!-- Header with Date Controls -->
    <div class="sticky top-0 z-20 bg-white border-b border-gray-300 shadow-sm">
      <div class="px-6 py-4">
        <div class="flex items-center justify-between flex-wrap gap-4">
          <div class="flex items-center space-x-4">
            <h1 class="text-2xl font-semibold text-black">Appointments</h1>
            <div class="flex items-center space-x-2">
              <Button variant="ghost" @click="goToPreviousDay">
                <FeatherIcon name="chevron-left" class="h-4 w-4 text-black" />
              </Button>
              <div class="px-4 py-2 bg-gray-100 rounded-lg min-w-[200px] text-center">
                <span class="text-sm font-medium text-black">{{ formattedDate }}</span>
              </div>
              
              <Button variant="ghost" @click="goToNextDay">
                <FeatherIcon name="chevron-right" class="h-4 w-4 text-black" />
              </Button>
              <Button variant="outline" @click="goToToday">
                <span class="text-black">Today</span>
              </Button>
            </div>
          </div>
          
          <div class="flex items-center space-x-3">
            <div class="relative">
              <FeatherIcon name="search" class="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-600" />
              <TextInput
                placeholder="Search practitioners..."
                class="pl-10 w-64 text-black"
                v-model="searchQuery"
              />
            </div>
            
            <!-- Filter Dropdown - Simplified without Frappe UI -->
            <div class="relative">
              <Button 
                variant="outline" 
                @click="toggleFilterDropdown"
                class="min-w-[120px]"
              >
                <FeatherIcon name="filter" class="h-4 w-4 mr-2 text-black" />
                <span class="text-black">Filter</span>
                <FeatherIcon name="chevron-down" class="h-4 w-4 ml-2 text-black" :class="{ 'rotate-180': showFilterDropdown }" />
              </Button>
              
              <!-- Dropdown Menu -->
              <div 
                v-if="showFilterDropdown" 
                class="absolute right-0 mt-2 w-48 bg-white border border-gray-300 rounded-lg shadow-lg z-50"
              >
                <div class="py-1">
                  <button 
                    v-for="option in filterOptions" 
                    :key="option.value"
                    @click="handleFilterOption(option)"
                    class="block w-full text-left px-4 py-2 text-sm text-black hover:bg-gray-100"
                  >
                    {{ option.label }}
                  </button>
                </div>
              </div>
            </div>
            
            <Button @click="refreshData" :loading="isRefreshing">
              <FeatherIcon name="refresh-cw" class="h-4 w-4 mr-2 text-black" />
              <span class="text-black">Refresh</span>
            </Button>
          </div>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="appointmentStore.isLoading && !appointments.length" class="flex items-center justify-center h-64">
      <LoadingIndicator class="w-8 h-8" />
      <span class="ml-2 text-gray-600">Loading appointments...</span>
    </div>

    <!-- Error State -->
    <div v-else-if="appointmentStore.error" class="p-6">
      <Alert type="error" :title="appointmentStore.error" />
    </div>

    <!-- Main Grid Container -->
    <div v-else class="appointment-grid" ref="gridContainer">
      <!-- Fixed Time Column -->
      <div class="time-column">
        <div class="time-header">
          <div class="h-20 border-b-2 border-gray-200 bg-gray-50 flex items-center justify-center">
            <span class="text-sm font-semibold text-gray-600">Time Slots</span>
          </div>
        </div>
        <div class="time-slots">
          <div
            v-for="slot in dateStore.timeSlots"
            :key="slot.time"
            class="time-slot"
            :class="{ 
              'text-gray-400 bg-gray-50': slot.isPast,
              'current-time': isCurrentTimeSlot(slot),
              'border-b-2 border-blue-200': isCurrentTimeSlot(slot)
            }"
          >
            <div class="flex flex-col items-center">
              <span class="text-sm font-medium text-black">{{ slot.display }}</span>
              <!-- <span class="text-xs text-gray-600">{{ slot.time }}</span> -->
            </div>
          </div>
        </div>
      </div>

      <!-- Scrollable Practitioners Area -->
      <div class="practitioners-area" ref="practitionersArea">
        <!-- Practitioners Header -->
        <div class="practitioners-header" ref="practitionersHeader">
          <div class="flex">
            <div v-if="practitionerStore.filteredPractitioners.length === 0" class="flex items-center justify-center min-w-[240px] h-full border-b-2 border-gray-300">
              <span class="text-gray-500 text-sm">No practitioners found</span>
            </div>
            <div 
              v-for="practitioner in practitionerStore.filteredPractitioners"
              :key="practitioner.id"
              class="practitioner-header-cell"
            >
              <PractitionerCard :practitioner="practitioner" />
            </div>
          </div>
        </div>

        <!-- Appointments Grid -->
        <div class="appointments-grid" ref="appointmentsGrid">
          <div class="grid-content">
            <div
              v-for="slot in dateStore.timeSlots"
              :key="slot.time"
              class="grid-row"
              :class="{ 
                'current-time': isCurrentTimeSlot(slot),
                'opacity-60': slot.isPast 
              }"
            >
              <div
                v-for="practitioner in practitionerStore.filteredPractitioners"
                :key="`${slot.time}-${practitioner.id}`"
                class="grid-cell"
                :class="{ 
                  'opacity-50': slot.isPast,
                  'bg-gray-50': !practitioner.is_available
                }"
              >
                <!-- Existing Appointment -->
                <AppointmentCard
                  v-if="getAppointment(slot.time, practitioner.id)"
                  :appointment="getAppointment(slot.time, practitioner.id)"
                  @click="viewAppointment"
                  @complete="handleCompleteAppointment"
                  @cancel="handleCancelAppointment"
                />
                
                <!-- Break Time Slot -->
                <div
                  v-else-if="slot.isDuringBreak"
                  class="break-slot"
                  :title="slot.breakLabel"
                >
                  <span class="text-xs text-gray-500">{{ slot.breakLabel || 'Break' }}</span>
                </div>
                
                <!-- Empty Slot with Add Button -->
                <div
                  v-else-if="canAddAppointment(slot, practitioner)"
                  class="add-appointment-button group"
                  @click="createAppointment(slot.time, practitioner)"
                  :title="`Create appointment for ${practitioner.name} at ${slot.display}`"
                >
                  <div class="add-button-content">
                    <FeatherIcon name="plus" class="h-6 w-6 text-black group-hover:text-blue-600 transition-colors" />
                    <span class="add-text text-xs text-black group-hover:text-blue-600 transition-colors mt-1 font-medium">Add</span>
                  </div>
                </div>
                
                <!-- Unavailable Slot -->
                <div
                  v-else
                  class="unavailable-slot"
                  :title="getUnavailableReason(slot, practitioner)"
                >
                  <span class="text-xs text-gray-400">—</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Appointment Dialog -->
    <AppointmentDialog />
    
    <!-- Confirmation Dialog -->
    <Dialog v-model="showConfirmDialog" :options="confirmDialogOptions">
      <template #body-content>
        <p class="text-gray-600">{{ confirmMessage }}</p>
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import { onMounted, computed, ref, onUnmounted, nextTick, watch } from 'vue'
// All Frappe UI components are now globally available from main.js
import { useAppointmentStore } from '@/stores/appointments'
import { usePractitionerStore } from '@/stores/practitioners'
import { useDateStore } from '@/stores/date'
import PractitionerCard from './PractitionerCard.vue'
import AppointmentCard from './AppointmentCard.vue'
import AppointmentDialog from './AppointmentDialog.vue'
import { notifications } from '@/utils/notifications'
import dayjs from 'dayjs'

const appointmentStore = useAppointmentStore()
const practitionerStore = usePractitionerStore()
const dateStore = useDateStore()

// Refs for DOM elements
const gridContainer = ref(null)
const practitionersArea = ref(null)
const practitionersHeader = ref(null)
const appointmentsGrid = ref(null)

// State
const isRefreshing = ref(false)
const showConfirmDialog = ref(false)
const confirmMessage = ref('')
const confirmAction = ref(null)
const searchQuery = ref('')
const showFilterDropdown = ref(false)

// Filter options
const filterOptions = computed(() => [
  {
    label: 'All Practitioners',
    value: 'all',
    handler: () => filterPractitioners('all')
  },
  {
    label: 'Available Only',
    value: 'available',
    handler: () => filterPractitioners('available')
  },
  {
    label: 'By Department',
    value: 'department',
    handler: () => filterPractitioners('department'),
    children: practitionerStore.departments.map(dept => ({
      label: dept,
      value: dept,
      handler: () => filterByDepartment(dept)
    }))
  },
  {
    label: 'Clear Filters',
    value: 'clear',
    handler: () => clearFilters()
  }
])

// Computed properties
const appointments = computed(() => appointmentStore.todaysAppointments)

const formattedDate = computed(() => {
  return dayjs(dateStore.selectedDate).format('dddd, MMMM D, YYYY')
})

const confirmDialogOptions = computed(() => ({
  title: 'Confirm Action',
  actions: [
    {
      label: 'Cancel',
      variant: 'outline'
    },
    {
      label: 'Confirm',
      variant: 'solid',
      theme: 'red',
      handler: () => {
        if (confirmAction.value) {
          confirmAction.value()
        }
        showConfirmDialog.value = false
      }
    }
  ]
}))

// Close dropdown when clicking outside
const handleClickOutside = (event) => {
  if (showFilterDropdown.value && !event.target.closest('.relative')) {
    showFilterDropdown.value = false
  }
}

// Initialize data
onMounted(async () => {
  // Add click outside listener
  document.addEventListener('click', handleClickOutside)
  
  try {
    console.log('🔄 Initializing appointment grid...')
    
    await Promise.all([
      dateStore.generateTimeSlots(),
      practitionerStore.fetchPractitioners(),
      appointmentStore.fetchAppointments()
    ])
    
    setupSynchronizedScrolling()

  } catch (error) {
    console.error('❌ Error initializing appointment grid:', error)
    notifications.error.dataLoadFailed(error.message)
  }
})

onUnmounted(() => {
  cleanupSynchronizedScrolling()
  // Remove click outside listener
  document.removeEventListener('click', handleClickOutside)
})

// Watch for date changes
watch(
  () => dateStore.selectedDate,
  async () => {
    practitionerStore.fetchPractitioners()
    await appointmentStore.fetchAppointments()
  }
)

// Watch for search query changes
watch(
  searchQuery,
  (newQuery) => {
    practitionerStore.setSearchQuery(newQuery)
  }
)

// Synchronized scrolling setup
let scrollListeners = []

const setupSynchronizedScrolling = () => {
  nextTick(() => {
    if (practitionersHeader.value && appointmentsGrid.value) {
      const syncScroll = (source, target) => {
        return () => {
          if (target) {
            target.scrollLeft = source.scrollLeft
          }
        }
      }
      
      const headerScrollListener = syncScroll(practitionersHeader.value, appointmentsGrid.value)
      const gridScrollListener = syncScroll(appointmentsGrid.value, practitionersHeader.value)
      
      practitionersHeader.value.addEventListener('scroll', headerScrollListener)
      appointmentsGrid.value.addEventListener('scroll', gridScrollListener)
      
      scrollListeners.push(
        () => practitionersHeader.value?.removeEventListener('scroll', headerScrollListener),
        () => appointmentsGrid.value?.removeEventListener('scroll', gridScrollListener)
      )
    }
  })
}

const cleanupSynchronizedScrolling = () => {
  scrollListeners.forEach(cleanup => cleanup())
  scrollListeners = []
}

// Helper functions
const getAppointment = (timeSlot, practitionerId) => {
  const key = `${timeSlot}-${practitionerId}`
  return appointmentStore.appointmentsByTimeSlot[key]
}

const canAddAppointment = (slot, practitioner) => {
  return (
    practitioner.is_available &&
    !slot.isPast &&
    dateStore.canBookAppointment(slot.time) &&
    !getAppointment(slot.time, practitioner.id)
  )
}

const isCurrentTimeSlot = (slot) => {
  if (!dateStore.isToday) return false
  
  const now = dayjs()
  const slotTime = dayjs(`${dateStore.selectedDate} ${slot.time}`)
  const nextSlotTime = slotTime.add(dateStore.slotDuration, 'minute')
  
  return now.isAfter(slotTime) && now.isBefore(nextSlotTime)
}

const getUnavailableReason = (slot, practitioner) => {
  if (slot.isPast) return 'Past time slot'
  if (slot.isDuringBreak) return `${slot.breakLabel || 'Break time'}`
  if (!practitioner.is_available) return 'Practitioner unavailable'
  if (!dateStore.canBookAppointment(slot.time)) return 'Booking not allowed'
  return 'Unavailable'
}

// Date navigation functions
const goToPreviousDay = () => {
  dateStore.goToPreviousDay()
}

const goToNextDay = () => {
  dateStore.goToNextDay()
}

const goToToday = () => {
  dateStore.goToToday()
}

// Event handlers
const createAppointment = (timeSlot, practitioner) => {
  appointmentStore.openAppointmentDialog('create', {
    time_slot: timeSlot,
    practitioner_id: practitioner.id,
    practitioner_name: practitioner.name
  })
}

const viewAppointment = (appointment) => {
  appointmentStore.openAppointmentDialog('view', appointment)
}

const handleCompleteAppointment = (appointment) => {
  confirmMessage.value = `Mark appointment with ${appointment.patient_name} as completed?`
  confirmAction.value = () => completeAppointment(appointment)
  showConfirmDialog.value = true
}

const handleCancelAppointment = (appointment) => {
  confirmMessage.value = `Cancel appointment with ${appointment.patient_name}?`
  confirmAction.value = () => cancelAppointment(appointment)
  showConfirmDialog.value = true
}

const completeAppointment = async (appointment) => {
  try {
    const result = await appointmentStore.completeAppointment(appointment.id)
    if (result.success) {
      notifications.success.appointmentCompleted()
    } else {
      notifications.error.appointmentUpdateFailed(result.error || 'Unknown error')
    }
  } catch (error) {
    notifications.error.appointmentUpdateFailed('Error completing appointment')
    console.error(error)
  }
}

const cancelAppointment = async (appointment) => {
  try {
    const result = await appointmentStore.cancelAppointment(appointment.id)
    if (result.success) {
      notifications.success.appointmentCancelled()
    } else {
      notifications.error.appointmentUpdateFailed(result.error || 'Unknown error')
    }
  } catch (error) {
    notifications.error.appointmentUpdateFailed('Error cancelling appointment')
    console.error(error)
  }
}

const refreshData = async () => {
  if (isRefreshing.value) return
  
  isRefreshing.value = true
  try {
    await Promise.all([
      dateStore.generateTimeSlots(),
      practitionerStore.fetchPractitioners(),
      appointmentStore.fetchAppointments()
    ])
    notifications.success.dataRefreshed()
  } catch (error) {
    notifications.error.dataLoadFailed(error.message)
    console.error(error)
  } finally {
    isRefreshing.value = false
  }
}

const filterPractitioners = (type) => {
  practitionerStore.setFilter(type)
  switch (type) {
    case 'all':
      notifications.info.filterApplied('All practitioners')
      break
    case 'available':
      notifications.info.filterApplied('Available practitioners only')
      break
    case 'department':
      notifications.info.filterApplied('Filter by department - select a department')
      break
    default:
      break
  }
}

const filterByDepartment = (department) => {
  practitionerStore.setFilter('department', department)
  notifications.info.filterApplied(`${department} department`)
}

const clearFilters = () => {
  practitionerStore.clearFilters()
  notifications.success.filtersCleared()
}

// Dropdown methods
const toggleFilterDropdown = () => {
  showFilterDropdown.value = !showFilterDropdown.value
}

const handleFilterOption = (option) => {
  showFilterDropdown.value = false
  if (option.handler) {
    option.handler()
  }
}
</script>


<style scoped>
.appointment-grid {
  @apply flex h-full overflow-hidden border-t border-gray-300 bg-white;
}

.time-column {
  @apply w-24 flex-shrink-0 bg-gray-50 border-r border-gray-300;
}

.time-header {
  @apply sticky top-0 z-10;
}

.time-slots {
  @apply space-y-0 bg-gray-50;
}

.time-slot {
  @apply h-14 flex items-center justify-center border-b border-gray-200 px-3 text-center transition-colors bg-gray-50;
  min-height: 64px;
}

.time-slot.current-time {
  @apply bg-blue-100 text-blue-800 font-semibold border-blue-300;
}

.grid-row.current-time {
  @apply bg-blue-50;
}

.practitioners-area {
  @apply flex-1 overflow-hidden;
}

.practitioners-header {
  @apply sticky top-0 z-10 bg-white border-b border-gray-300 h-20 overflow-x-auto shadow-sm;
  scroll-behavior: smooth;
  scrollbar-width: thin;
  scrollbar-color: #cbd5e1 #f1f5f9;
}

.practitioners-header::-webkit-scrollbar {
  height: 6px;
}

.practitioners-header::-webkit-scrollbar-track {
  background: #f1f5f9;
  border-radius: 3px;
}

.practitioners-header::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}

.practitioners-header::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

.practitioner-header-cell {
  @apply w-56 flex-shrink-0 border-r border-gray-200 h-full bg-white;
}

.appointments-grid {
  @apply h-full overflow-auto border-l-2 border-gray-400;
  scroll-behavior: smooth;
  background: 
    linear-gradient(to right, #f3f4f6 1px, transparent 1px),
    linear-gradient(to bottom, #d1d5db 1px, transparent 1px);
  background-size: 224px 64px; /* Match updated cell width and height */
}

.appointments-grid::-webkit-scrollbar {
  @apply w-2 h-2;
}

.appointments-grid::-webkit-scrollbar-track {
  @apply bg-gray-100;
}

.appointments-grid::-webkit-scrollbar-thumb {
  @apply bg-gray-400 rounded-full;
}

.appointments-grid::-webkit-scrollbar-thumb:hover {
  @apply bg-gray-500;
}

.grid-content {
  @apply space-y-0;
}

.grid-row {
  @apply flex transition-colors bg-white;
  min-height: 64px;
}

.grid-cell {
  @apply w-56 h-16 flex-shrink-0 border-r border-gray-200 relative flex items-center justify-center p-2 transition-all bg-white;
  min-height: 64px;
  border-bottom: 1px solid #f3f4f6;
}

.grid-cell:hover {
  @apply bg-blue-50;
}

.add-appointment-button {
  @apply w-full h-full flex items-center justify-center cursor-pointer hover:bg-blue-100 transition-all rounded-md border border-dashed border-gray-400 hover:border-blue-500;
  min-height: 60px;
  background-color: #fafafa;
}

.add-appointment-button:hover {
  @apply shadow-md;
}

.add-appointment-button:hover .add-button-content {
  @apply transform scale-110;
}

.add-appointment-button:active {
  @apply scale-95;
}

.add-button-content {
  @apply flex flex-col items-center justify-center text-center;
}

.add-button-content .add-text {
  @apply text-xs font-medium;
}

.unavailable-slot {
  @apply w-full h-full flex items-center justify-center text-gray-400 bg-gray-100 border border-gray-300;
}

.break-slot {
  @apply w-full h-full flex items-center justify-center bg-orange-100 text-orange-600 border-2 border-orange-300;
}

/* Enhanced visual elements for better grid visibility */
.current-time-indicator {
  @apply absolute left-0 right-0 h-0.5 bg-red-500 z-20;
  box-shadow: 0 0 4px rgba(239, 68, 68, 0.5);
}

/* Focus styles for accessibility */
.add-appointment-button:focus {
  @apply outline-none ring-2 ring-blue-500 ring-offset-2;
}

.practitioners-header:focus,
.appointments-grid:focus {
  @apply outline-none ring-2 ring-blue-500 ring-offset-2;
}

/* Current time slot highlighting */
.time-slot.current-time {
  @apply bg-red-100 border-red-300 text-red-700 font-bold;
  box-shadow: inset 3px 0 0 #ef4444;
}

.grid-row.current-time {
  @apply bg-red-50 border-red-300;
}

.grid-row.current-time .grid-cell {
  @apply border-red-200;
}

/* Synchronized scrolling */
.practitioners-header,
.appointments-grid {
  scroll-behavior: smooth;
}

/* Mobile responsive adjustments */
@media (max-width: 768px) {
  .appointment-grid-container {
    @apply text-sm;
  }
  
  .time-column {
    @apply w-20;
  }
  
  .grid-cell, .practitioner-header-cell {
    @apply w-48 h-14;
    min-height: 56px;
  }
  
  .time-slot {
    @apply h-14;
    min-height: 56px;
  }
  
  .practitioners-header {
    @apply h-16;
  }
}

@media (max-width: 640px) {
  .grid-cell, .practitioner-header-cell {
    @apply w-40 h-12;
    min-height: 48px;
  }
  
  .time-slot {
    @apply h-12 text-xs;
    min-height: 48px;
  }
  
  .time-column {
    @apply w-24;
  }
  
  .practitioners-header {
    @apply h-14;
  }
  
  .appointment-grid-container .px-6 {
    @apply px-4;
  }
  
  .appointment-grid-container .py-4 {
    @apply py-3;
  }
}

/* Loading and error states */
.loading-overlay {
  @apply absolute inset-0 bg-white bg-opacity-75 flex items-center justify-center z-20;
}

/* Smooth transitions */
.appointment-card {
  @apply transition-all duration-200 ease-in-out;
}

.appointment-card:hover {
  @apply scale-105 shadow-md;
}

/* High contrast mode support */
@media (prefers-contrast: high) {
  .grid-cell {
    @apply border-gray-400;
  }
  
  .time-slot {
    @apply border-gray-400;
  }
  
  .appointment-card {
    @apply border-2;
  }
}

/* Reduced motion support */
@media (prefers-reduced-motion: reduce) {
  .appointment-card,
  .add-appointment-button,
  .time-slot,
  .grid-row,
  .grid-cell {
    @apply transition-none;
  }
  
  .practitioners-header,
  .appointments-grid {
    scroll-behavior: auto;
  }
}
</style>
