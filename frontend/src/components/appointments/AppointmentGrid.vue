<template>
  <div class="appointment-grid-container min-h-screen bg-gray-100">
    <!-- Header with Date Controls -->
    <div class="sticky top-0 z-20 bg-white border-b border-gray-300 shadow-sm">
      <div class="px-6 py-4">
        <div class="flex items-center justify-between flex-wrap gap-4">
          <div class="flex items-center space-x-6">
            <h1 class="text-2xl font-semibold text-black">Appointments</h1>
            
            <!-- Company Selector -->
            <div class="flex items-center">
              <Link
                class="form-control min-w-[240px]"
                :value="selectedCompany || ''"
                doctype="Company"
                placeholder="Select Company"
                @change="handleCompanyChange"
                variant="outline"
              />
            </div>
            
            <!-- Date Controls -->
            <div class="flex items-center space-x-2">
              <Button variant="ghost" @click="goToPreviousDay">
                <FeatherIcon name="chevron-left" class="h-4 w-4 text-black" />
              </Button>
              
              <DatePicker
                v-model="selectedDateForPicker"
                variant="outline"
                placeholder="Select Date"
                @change="handleDateChange"
                class="min-w-[200px]"
              />
              
              <Button variant="ghost" @click="goToNextDay">
                <FeatherIcon name="chevron-right" class="h-4 w-4 text-black" />
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
            <Button @click="refreshData" :loading="isRefreshing">
              <FeatherIcon name="refresh-cw" class="h-4 w-4 mr-2 text-black" />
              <span class="text-black">Refresh</span>
            </Button>
          </div>
        </div>
        
        <div class="py-2">
          <div class="text-sm text-gray-500">
            {{ formattedDate }}
          </div>
        </div>
      </div>
    </div>

    <!-- Main Grid Container -->
    <div class="appointment-grid">
      <!-- Time Column -->
      <div class="time-column">
        <!-- Time Slots Header -->
        <div class="time-header">
          <div class="h-20 border-b-2 border-gray-200 bg-gray-50 flex items-center justify-center sticky top-0 z-40">
            <span class="text-sm font-semibold text-gray-600">Time Slots</span>
          </div>
        </div>

        <!-- Time Slots Body - Scrollable -->
        <div class="time-slots" ref="timeSlots">
          <div
            v-for="slot in dateStore.timeSlots"
            :key="slot.time"
            class="time-slot"
            :class="{ 
              'current-time': isCurrentTimeSlot(slot),
              'opacity-60': slot.isPast 
            }"
          >
            <div class="flex flex-col items-center">
              <span class="text-sm font-medium text-black">{{ slot.display }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Practitioners Area -->
      <div class="practitioners-area" ref="practitionersArea">
        <!-- Practitioners Header with Navigation Controls -->
        <div class="practitioners-header-container">
          <!-- Left Scroll Button -->
          <button
            v-if="canScrollLeft"
            @click="scrollHorizontally('left')"
            class="scroll-control scroll-control-left"
            :disabled="!canScrollLeft"
            title="Scroll left"
          >
            <FeatherIcon name="chevron-left" class="h-5 w-5 text-white drop-shadow-sm" />
          </button>

          <!-- Practitioners Header - Fixed -->
          <div class="practitioners-header-fixed" ref="practitionersHeader">
            <div class="flex">
              <div v-if="practitionerStore.filteredPractitioners.length === 0" class="flex items-center justify-center min-w-[240px] h-full border-b-2 border-gray-300">
                <span class="text-gray-500 text-sm">No practitioners found</span>
              </div>
              <div 
                v-for="practitioner in practitionerStore.filteredPractitioners"
                :key="practitioner.name"
                class="practitioner-header-cell"
              >
                <PractitionerCard :practitioner="practitioner" />
              </div>
            </div>
          </div>

          <!-- Right Scroll Button -->
          <button
            v-if="canScrollRight"
            @click="scrollHorizontally('right')"
            class="scroll-control scroll-control-right"
            :disabled="!canScrollRight"
            title="Scroll right"
          >
            <FeatherIcon name="chevron-right" class="h-5 w-5 text-white drop-shadow-sm" />
          </button>
        </div>

        <!-- Scrollable Appointments Grid -->
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
                :key="`${slot.time}-${practitioner.name}`"
                class="grid-cell"
                :class="{ 
                  'opacity-50': slot.isPast,
                  'bg-gray-50': !practitioner.is_available
                }"
              >
                <!-- Existing Appointment -->
                <AppointmentCard
                  v-if="getAppointment(slot.time, practitioner.name)"
                  :appointment="getAppointment(slot.time, practitioner.name)"
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
                    <FeatherIcon name="plus" class="h-4 w-4 text-black group-hover:text-blue-600 transition-colors" />
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
import { useAppointmentStore } from '@/stores/appointment'
import { usePractitionerStore } from '@/stores/practitioner'
import { useDateStore } from '@/stores/date'
import PractitionerCard from './PractitionerCard.vue'
import AppointmentCard from './AppointmentCard.vue'
import AppointmentDialog from './AppointmentDialog.vue'
import Link from '../controls/Link.vue'
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
const timeSlots = ref(null)

// State
const isRefreshing = ref(false)
const showConfirmDialog = ref(false)
const confirmMessage = ref('')
const confirmAction = ref(null)
const searchQuery = ref('')
const selectedCompany = ref('')
const selectedDateForPicker = ref('')
const userCompanies = ref([])

// Horizontal scroll control state
const canScrollLeft = ref(false)
const canScrollRight = ref(false)
const scrollAmount = 256 // 2 practitioner cards width (128px each)

// Initialize selectedDateForPicker with current date
onMounted(() => {
  selectedDateForPicker.value = dateStore.selectedDate
  // Ensure selectedCompany has a default value
  if (!selectedCompany.value) {
    selectedCompany.value = ''
  }
})

// Company options for Select component  
const companyOptions = computed(() => {
  return userCompanies.value.map(company => ({
    label: company.name,
    value: company.name
  }))
})

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

// Initialize data
onMounted(async () => {
  try {
    console.log('🔄 Initializing appointment grid...')

    // Fetch user companies first
    await fetchUserCompanies()

    // Sync dates between stores initially
    appointmentStore.setSelectedDate(dateStore.selectedDate)
    selectedDateForPicker.value = dateStore.selectedDate

    // Set initial company in appointment store if one is selected
    if (selectedCompany.value) {
      appointmentStore.setSelectedCompany(selectedCompany.value)
    }

    await Promise.all([
      dateStore.generateTimeSlots(),
      selectedCompany.value ? practitionerStore.fetchPractitioners(selectedCompany.value, dateStore.selectedDate) : Promise.resolve()
    ])
    
    setupSynchronizedScrolling()

    // Add window resize listener for scroll button states
    window.addEventListener('resize', updateScrollButtonStates)

  } catch (error) {
    console.error('❌ Error initializing appointment grid:', error)
    notifications.error.dataLoadFailed(error.message)
  }
})

onUnmounted(() => {
  cleanupSynchronizedScrolling()
  window.removeEventListener('resize', updateScrollButtonStates)
})

// Watch for date changes
watch(
  () => dateStore.selectedDate,
  async (newDate) => {
    console.log('🔍 DateStore date changed to:', newDate)
    selectedDateForPicker.value = newDate
    appointmentStore.setSelectedDate(newDate) // Update appointment store date
    if (selectedCompany.value && selectedCompany.value.trim()) {
      practitionerStore.fetchPractitioners(selectedCompany.value, dateStore.selectedDate)
    }
  }
)

// Watch for company changes
watch(
  selectedCompany,
  async (newCompany) => {
    if (newCompany && newCompany.trim()) {
      appointmentStore.setSelectedCompany(newCompany)
      await Promise.all([
        practitionerStore.fetchPractitioners(newCompany, dateStore.selectedDate),
        appointmentStore.fetchAppointments()
      ])
    }
  }
)

// Watch for search query changes
watch(
  searchQuery,
  (newQuery) => {
    practitionerStore.setSearchQuery(newQuery)
  }
)

// Watch for practitioners changes to update scroll states
watch(
  () => practitionerStore.filteredPractitioners,
  () => {
    nextTick(() => {
      updateScrollButtonStates()
    })
  }
)

// Synchronized scrolling setup (vertical only)
let scrollListeners = []

// Simplified vertical-only synchronized scrolling
const setupSynchronizedScrolling = () => {
  nextTick(() => {
    if (appointmentsGrid.value && timeSlots.value) {
      let isScrolling = false

      // Vertical sync: appointments grid to time slots
      const handleAppointmentsGridScroll = () => {
        if (isScrolling) return
        isScrolling = true
        
        const scrollTop = appointmentsGrid.value.scrollTop
        
        // Sync vertical with time slots only
        if (timeSlots.value.scrollTop !== scrollTop) {
          timeSlots.value.scrollTop = scrollTop
        }
        
        // Update horizontal scroll button states
        updateScrollButtonStates()
        
        isScrolling = false
      }

      // Vertical sync: time slots to appointments grid
      const handleTimeSlotsScroll = () => {
        if (isScrolling) return
        isScrolling = true
        
        const scrollTop = timeSlots.value.scrollTop
        if (appointmentsGrid.value.scrollTop !== scrollTop) {
          appointmentsGrid.value.scrollTop = scrollTop
        }
        
        isScrolling = false
      }

      // Add event listeners with passive: true for better performance
      appointmentsGrid.value.addEventListener('scroll', handleAppointmentsGridScroll, { passive: true })
      timeSlots.value.addEventListener('scroll', handleTimeSlotsScroll, { passive: true })

      scrollListeners.push(
        () => appointmentsGrid.value?.removeEventListener('scroll', handleAppointmentsGridScroll),
        () => timeSlots.value?.removeEventListener('scroll', handleTimeSlotsScroll)
      )

      // Initial scroll button state check
      updateScrollButtonStates()
    }
  })
}

// Horizontal scroll control functions
const scrollHorizontally = (direction) => {
  if (!practitionersHeader.value || !appointmentsGrid.value) return

  const currentScrollLeft = practitionersHeader.value.scrollLeft
  const newScrollLeft = direction === 'left' 
    ? Math.max(0, currentScrollLeft - scrollAmount)
    : currentScrollLeft + scrollAmount

  // Smooth scroll both elements simultaneously
  practitionersHeader.value.scrollTo({
    left: newScrollLeft,
    behavior: 'smooth'
  })
  
  appointmentsGrid.value.scrollTo({
    left: newScrollLeft,
    top: appointmentsGrid.value.scrollTop,
    behavior: 'smooth'
  })

  // Update button states after scroll animation
  setTimeout(updateScrollButtonStates, 300)
}

const updateScrollButtonStates = () => {
  if (!practitionersHeader.value) return

  const scrollLeft = practitionersHeader.value.scrollLeft
  const maxScrollLeft = practitionersHeader.value.scrollWidth - practitionersHeader.value.clientWidth

  canScrollLeft.value = scrollLeft > 0
  canScrollRight.value = scrollLeft < maxScrollLeft - 1 // -1 for precision issues
}

const cleanupSynchronizedScrolling = () => {
  scrollListeners.forEach(cleanup => cleanup())
  scrollListeners = []
}

// Helper functions
const getAppointment = (timeSlot, practitionerId) => {
  const key = `${timeSlot}-${practitionerId}`
  const appointment = appointmentStore.appointmentsByTimeSlot[key]
  
  return appointment
}

const canAddAppointment = (slot, practitioner) => {
  return (
    practitioner.is_available &&
    !slot.isPast &&
    dateStore.canBookAppointment(slot.time) &&
    !getAppointment(slot.time, practitioner.name)
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

// Handle date change from DatePicker
const handleDateChange = async(selectedDate) => {
  if (selectedDate) {
    console.log('🔍 Date picker changed to:', selectedDate)
    dateStore.setSelectedDate(selectedDate)

    await Promise.all([
      practitionerStore.fetchPractitioners(selectedCompany.value, selectedDate),
      appointmentStore.fetchAppointments()
    ])

    selectedDateForPicker.value = selectedDate
  }
}

// Handle company change from Link component
const handleCompanyChange = async (selectedCompanyValue) => {
  if (selectedCompanyValue && typeof selectedCompanyValue === 'string') {
    selectedCompany.value = selectedCompanyValue

    await Promise.all([
      practitionerStore.fetchPractitioners(selectedCompanyValue, dateStore.selectedDate),
      appointmentStore.setSelectedCompany(selectedCompanyValue)
    ])

    console.log('Company changed to:', selectedCompanyValue)
  } else if (selectedCompanyValue && selectedCompanyValue.name) {
    // Handle if Link component returns an object
    selectedCompany.value = selectedCompanyValue.name

    await Promise.all([
      practitionerStore.fetchPractitioners(selectedCompanyValue.name, dateStore.selectedDate),
      appointmentStore.setSelectedCompany(selectedCompanyValue.name)
    ])

    console.log('Company changed to:', selectedCompanyValue.name)
  }
}

// Fetch user companies function
const fetchUserCompanies = async () => {
  try {
    // Mock data for now - replace with actual API call
    userCompanies.value = [
      // { name: 'Nephro One Dialysis Clinic' },
      { name: 'Shree Hindu Mandal Hospital - Mwanza' },
    ]
    
    // Set default company if none selected
    if (userCompanies.value.length > 0 && !selectedCompany.value) {
      selectedCompany.value = userCompanies.value[0].name
    }
  } catch (error) {
    console.error('Error fetching user companies:', error)
    userCompanies.value = [{ name: 'Default Company' }]
    selectedCompany.value = 'Default Company'
  }
}

// Event handlers
const createAppointment = (timeSlot, practitioner) => {
  appointmentStore.openAppointmentDialog('create', {
    time_slot: timeSlot,
    practitioner_id: practitioner.name,
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
    const result = await appointmentStore.completeAppointment(appointment.name)
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
    const result = await appointmentStore.cancelAppointment(appointment.name)
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
      (selectedCompany.value && selectedCompany.value.trim()) ? practitionerStore.fetchPractitioners(selectedCompany.value, dateStore.selectedDate) : Promise.resolve(),
      (selectedCompany.value && selectedCompany.value.trim()) ? appointmentStore.fetchAppointments() : Promise.resolve(),
    ])
    notifications.success.dataRefreshed()
  } catch (error) {
    notifications.error.dataLoadFailed(error.message)
    console.error(error)
  } finally {
    isRefreshing.value = false
  }
}
</script>


<style scoped>
.appointment-grid {
  @apply flex h-full border-t border-gray-300 bg-white;
  position: relative;
  min-height: calc(80vh - 80px);
  height: calc(100vh - 100px);
}

.time-column {
  @apply w-24 flex-shrink-0 bg-gray-50 border-r border-gray-300;
  position: relative;
  display: flex;
  flex-direction: column;
}

.time-header {
  @apply sticky top-0 z-40 bg-gray-50;
  flex-shrink: 0;
}

.practitioners-header-fixed {
  @apply bg-white border-b border-gray-300 h-20 shadow-sm;
  position: sticky;
  top: 0;
  z-index: 50;
  flex-shrink: 0;
  overflow-x: auto;
  overflow-y: hidden;
  scroll-behavior: auto; /* Remove smooth scrolling for instant sync */
  scrollbar-width: none; /* Firefox */
  -ms-overflow-style: none; /* Internet Explorer 10+ */
}

.practitioners-header-fixed::-webkit-scrollbar {
  display: none; /* WebKit */
}

.time-slots {
  @apply space-y-0 bg-gray-50;
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  scroll-behavior: auto; /* Remove smooth scrolling for instant sync */
  scrollbar-width: none; /* Firefox */
  -ms-overflow-style: none; /* Internet Explorer 10+ */
}

.time-slots::-webkit-scrollbar {
  display: none; /* WebKit */
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
  @apply flex-1;
  position: relative;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.practitioners-header-container {
  position: relative;
  display: flex;
  align-items: center;
  background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
  border-bottom: 2px solid #e5e7eb;
  height: 80px;
  flex-shrink: 0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.scroll-control {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  z-index: 60;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(96, 165, 250, 0.25), 0 2px 4px rgba(0, 0, 0, 0.1);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  backdrop-filter: blur(8px);
  background: linear-gradient(135deg, rgba(96, 165, 250, 0.9) 0%, rgba(59, 130, 246, 0.9) 100%);
  border: 2px solid #60a5fa;
}

.scroll-control:hover:not(:disabled) {
  box-shadow: 0 8px 25px rgba(96, 165, 250, 0.35), 0 4px 12px rgba(0, 0, 0, 0.15);
  transform: translateY(-50%) scale(1.1);
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.95) 0%, rgba(37, 99, 235, 0.95) 100%);
  border-color: #3b82f6;
}

.scroll-control:disabled {
  opacity: 0.4;
  cursor: not-allowed;
  background: #9ca3af;
  border-color: #6b7280;
}



.scroll-control:active:not(:disabled) {
  transform: translateY(-50%) scale(0.95);
  box-shadow: 0 2px 8px rgba(96, 165, 250, 0.3);
}

.scroll-control:focus {
  outline: none;
  box-shadow: 0 4px 12px rgba(96, 165, 250, 0.25), 0 2px 4px rgba(0, 0, 0, 0.1), 0 0 0 2px #3b82f6, 0 0 0 4px rgba(96, 165, 250, 0.2);
}

/* Subtle pulse animation to draw attention */
@keyframes pulse-blue {
  0%, 100% {
    box-shadow: 0 4px 12px rgba(96, 165, 250, 0.25), 0 2px 4px rgba(0, 0, 0, 0.1);
  }
  50% {
    box-shadow: 0 4px 12px rgba(96, 165, 250, 0.4), 0 2px 4px rgba(0, 0, 0, 0.1);
  }
}

.scroll-control:not(:disabled) {
  animation: pulse-blue 3s ease-in-out infinite;
}

/* Entrance animation */
@keyframes slideIn {
  0% {
    opacity: 0;
    transform: translateY(-50%) scale(0.5);
  }
  100% {
    opacity: 1;
    transform: translateY(-50%) scale(1);
  }
}

.scroll-control {
  animation: slideIn 0.3s ease-out;
}

.scroll-control-left {
  left: 12px;
}

.scroll-control-left::before {
  content: '';
  position: absolute;
  top: -4px;
  left: -4px;
  right: -4px;
  bottom: -4px;
  background: linear-gradient(135deg, rgba(96, 165, 250, 0.1) 0%, rgba(59, 130, 246, 0.1) 100%);
  border-radius: 50%;
  z-index: -1;
}

.scroll-control-right {
  right: 12px;
}

.scroll-control-right::before {
  content: '';
  position: absolute;
  top: -4px;
  left: -4px;
  right: -4px;
  bottom: -4px;
  background: linear-gradient(135deg, rgba(96, 165, 250, 0.1) 0%, rgba(59, 130, 246, 0.1) 100%);
  border-radius: 50%;
  z-index: -1;
}

.practitioners-header-fixed {
  @apply bg-white h-20;
  flex: 1;
  margin: 0 60px; /* Increased space for larger scroll buttons */
  overflow-x: auto;
  overflow-y: hidden;
  scroll-behavior: smooth;
  scrollbar-width: none; /* Firefox */
  -ms-overflow-style: none; /* Internet Explorer 10+ */
  border-radius: 8px;
  box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.05);
}

.practitioners-header-fixed::-webkit-scrollbar {
  display: none; /* WebKit */
}

.appointments-grid-wrapper {
  flex: 1;
  overflow: hidden;
  position: relative;
}

.practitioner-header-cell {
  @apply w-32 flex-shrink-0 border-r border-gray-200 h-full bg-white;
}

.appointments-grid {
  @apply overflow-y-auto;
  overflow-x: auto;
  scroll-behavior: smooth;
  background: 
    linear-gradient(to right, #f3f4f6 1px, transparent 1px),
    linear-gradient(to bottom, #d1d5db 1px, transparent 1px);
  background-size: 128px 64px; /* Match practitioner card width (w-32) and cell height */
  height: 100%;
  width: 100%;
}

.appointments-grid::-webkit-scrollbar-horizontal {
  display: none; /* Hide horizontal scrollbar */
}

.appointments-grid::-webkit-scrollbar:vertical {
  @apply w-2;
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
  @apply w-32 h-16 flex-shrink-0 border-r border-gray-200 relative flex items-center justify-center p-2 transition-all bg-white;
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

.practitioners-header-fixed:focus,
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
.practitioners-header-fixed,
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
    @apply w-32 h-14;
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
    @apply w-32 h-12;
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
