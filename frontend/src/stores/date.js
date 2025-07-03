import { defineStore } from 'pinia'
import dayjs from 'dayjs'

// Using standard dayjs methods: isAfter(), isBefore(), isSame()

export const useDateStore = defineStore('date', {
  state: () => ({
    selectedDate: dayjs().format('YYYY-MM-DD'),
    timeSlots: [],
    workingHours: {
      start: '08:00',
      end: '07:50'
    },
    slotDuration: 10, // minutes
    bufferTime: 5, // minutes buffer for future bookings
  }),

  getters: {
    isToday: (state) => {
      return state.selectedDate === dayjs().format('YYYY-MM-DD')
    },

    isPastDate: (state) => {
      return dayjs(state.selectedDate).isBefore(dayjs(), 'day')
    },

    isFutureDate: (state) => {
      return dayjs(state.selectedDate).isAfter(dayjs(), 'day')
    },

    formattedSelectedDate: (state) => {
      return dayjs(state.selectedDate).format('dddd, MMMM D, YYYY')
    },

    currentTimeSlots: (state) => {
      return state.timeSlots
    }
  },

  actions: {
    setSelectedDate(date) {
      this.selectedDate = dayjs(date).format('YYYY-MM-DD')
      this.generateTimeSlots()
    },

    goToPreviousDay() {
      const previousDay = dayjs(this.selectedDate).subtract(1, 'day')
      this.setSelectedDate(previousDay)
    },

    goToNextDay() {
      const nextDay = dayjs(this.selectedDate).add(1, 'day')
      this.setSelectedDate(nextDay)
    },

    goToToday() {
      this.setSelectedDate(dayjs())
    },

    generateTimeSlots() {
      const slots = []
      const startTime = dayjs(`${this.selectedDate} ${this.workingHours.start}`)
      const endTime = dayjs(`${this.selectedDate} ${this.workingHours.end}`).add(1, 'day')
      const currentTime = dayjs()

      let startTimeSlot = startTime
      
      while (startTimeSlot.isBefore(endTime)) {
        const timeString = startTimeSlot.format('HH:mm')
        
        slots.push({
          time: timeString,
          display: startTimeSlot.format('h:mm A'),
          timestamp: startTimeSlot.valueOf(),
          isPast: startTimeSlot.isBefore(currentTime),
        })
        
        startTimeSlot = startTimeSlot.add(this.slotDuration, 'minute')
      }
      
      this.timeSlots = slots
    },

    canBookAppointment(timeSlot) {
      const slot = this.timeSlots.find(s => s.time === timeSlot)
      if (!slot) return false
      
      // Use the timestamp from the slot object which correctly handles cross-midnight scenarios
      const slotDateTime = dayjs(slot.timestamp)
      const currentTime = dayjs()
      
      // Allow booking only if the slot time is equal to or greater than current time
      // This prevents backdated appointments while allowing all future slots
      return slotDateTime.isAfter(currentTime) || slotDateTime.isSame(currentTime, 'minute')
    },

    setWorkingHours(start, end) {
      this.workingHours.start = start
      this.workingHours.end = end
      this.generateTimeSlots()
    },

    setSlotDuration(duration) {
      this.slotDuration = duration
      this.generateTimeSlots()
    }
  }
})
