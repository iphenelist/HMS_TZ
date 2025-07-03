import { defineStore } from 'pinia'
import { createResource } from 'frappe-ui'
import dayjs from 'dayjs'

export const useAppointmentStore = defineStore('appointments', {
  state: () => ({
    appointments: [],
    selectedDate: dayjs().format('YYYY-MM-DD'),
    selectedAppointment: null,
    isLoading: false,
    error: null,
    showAppointmentDialog: false,
    dialogMode: 'create' // 'create', 'edit', 'view'
  }),

  getters: {
    appointmentsByPractitioner: (state) => {
      const grouped = {}
      state.appointments.forEach(appointment => {
        if (!grouped[appointment.practitioner_id]) {
          grouped[appointment.practitioner_id] = []
        }
        grouped[appointment.practitioner_id].push(appointment)
      })
      return grouped
    },

    appointmentsByTimeSlot: (state) => {
      const grouped = {}
      state.appointments.forEach(appointment => {
        const key = `${appointment.time_slot}-${appointment.practitioner_id}`
        grouped[key] = appointment
      })
      return grouped
    },

    todaysAppointments: (state) => {
      return state.appointments.filter(
        appointment => appointment.date === state.selectedDate
      )
    }
  },

  actions: {
    setSelectedDate(date) {
      this.selectedDate = date
      this.fetchAppointments()
    },

    openAppointmentDialog(mode = 'create', appointment = null) {
      this.dialogMode = mode
      this.selectedAppointment = appointment
      this.showAppointmentDialog = true
    },

    closeAppointmentDialog() {
      this.showAppointmentDialog = false
      this.selectedAppointment = null
      this.dialogMode = 'create'
    },

    async fetchAppointments() {
      this.isLoading = true
      this.error = null
      
      try {
        // TODO: Replace with actual API call
        /*
        const appointmentsResource = createResource({
          url: 'hms_tz.api.appointments.get_appointments',
          params: { 
            date: this.selectedDate,
            include_cancelled: true 
          },
          auto: false
        })
        
        const response = await appointmentsResource.fetch()
        this.appointments = response.message || []
        */
        
        // Enhanced sample data for now
        const sampleAppointments = [
          {
            id: 1,
            practitioner_id: 1,
            patient_name: "John Doe",
            contact: "+255123456789",
            time_slot: "09:00",
            status: "scheduled",
            appointment_type: "Consultation",
            notes: "Regular checkup - patient reports mild headaches",
            date: this.selectedDate,
            created_at: new Date().toISOString(),
            modified_at: new Date().toISOString(),
            created_by: "Reception",
            patient_id: "PAT-001"
          },
          {
            id: 2,
            practitioner_id: 2,
            patient_name: "Jane Smith",
            contact: "+255987654321",
            time_slot: "10:30",
            status: "completed",
            appointment_type: "Follow-up",
            notes: "Post-surgery checkup - wound healing well",
            date: this.selectedDate,
            created_at: new Date().toISOString(),
            modified_at: new Date().toISOString(),
            created_by: "Dr. Sarah Johnson",
            patient_id: "PAT-002"
          },
          {
            id: 3,
            practitioner_id: 1,
            patient_name: "Alice Brown",
            contact: "+255456789123",
            time_slot: "14:00",
            status: "open",
            appointment_type: "Emergency",
            notes: "Urgent care needed - chest pain",
            date: this.selectedDate,
            created_at: new Date().toISOString(),
            modified_at: new Date().toISOString(),
            created_by: "Emergency",
            patient_id: "PAT-003"
          },
          {
            id: 4,
            practitioner_id: 3,
            patient_name: "Robert Wilson",
            contact: "+255321654987",
            time_slot: "11:20",
            status: "scheduled",
            appointment_type: "Checkup",
            notes: "Annual physical examination",
            date: this.selectedDate,
            created_at: new Date().toISOString(),
            modified_at: new Date().toISOString(),
            created_by: "Reception",
            patient_id: "PAT-004"
          },
          {
            id: 5,
            practitioner_id: 4,
            patient_name: "Maria Garcia",
            contact: "+255789456123",
            time_slot: "15:40",
            status: "cancelled",
            appointment_type: "Therapy",
            notes: "Physical therapy session - patient cancelled due to illness",
            date: this.selectedDate,
            created_at: new Date().toISOString(),
            modified_at: new Date().toISOString(),
            created_by: "Dr. Emily Davis",
            patient_id: "PAT-005"
          }
        ]
        
        // Remove artificial delay for faster loading
        this.appointments = sampleAppointments
        console.log('✅ Appointments loaded:', sampleAppointments.length)
        
      } catch (error) {
        this.error = error.message || 'Failed to fetch appointments'
        console.error('❌ Error fetching appointments:', error)
        throw error
      } finally {
        this.isLoading = false
      }
    },

    async createAppointment(appointmentData) {
      this.isLoading = true
      this.error = null
      
      try {
        // Validate required fields
        if (!appointmentData.patient_name || !appointmentData.contact || !appointmentData.time_slot) {
          throw new Error('Missing required fields')
        }

        // TODO: Replace with actual API call
        /*
        const createResource = createResource({
          url: 'hms_tz.api.appointments.create_appointment',
          params: {
            ...appointmentData,
            date: this.selectedDate
          },
          auto: false
        })
        
        const response = await createResource.fetch()
        const newAppointment = response.message
        */
        
        // Create new appointment - sample implementation
        const newAppointment = {
          id: Date.now(), // Temporary ID generation
          ...appointmentData,
          date: this.selectedDate,
          status: 'scheduled',
          created_at: new Date().toISOString(),
          modified_at: new Date().toISOString(),
          created_by: 'Reception',
          patient_id: `PAT-${String(Date.now()).slice(-3)}`
        }
        
        // Simulate network delay
        await new Promise(resolve => setTimeout(resolve, 500))
        
        this.appointments.push(newAppointment)
        this.closeAppointmentDialog()
        
        return { success: true, data: newAppointment }
      } catch (error) {
        this.error = error.message || 'Failed to create appointment'
        console.error('Error creating appointment:', error)
        return { success: false, error: error.message }
      } finally {
        this.isLoading = false
      }
    },

    async updateAppointment(appointmentId, updates) {
      this.isLoading = true
      this.error = null
      
      try {
        // TODO: Replace with actual API call
        // const response = await createResource({
        //   url: 'hms_tz.api.appointments.update_appointment',
        //   params: { id: appointmentId, ...updates }
        // }).fetch()
        
        const index = this.appointments.findIndex(app => app.id === appointmentId)
        if (index !== -1) {
          this.appointments[index] = { 
            ...this.appointments[index], 
            ...updates,
            modified_at: new Date().toISOString()
          }
        }
        
        this.closeAppointmentDialog()
        return { success: true }
      } catch (error) {
        this.error = error.message
        console.error('Error updating appointment:', error)
        return { success: false, error: error.message }
      } finally {
        this.isLoading = false
      }
    },

    async deleteAppointment(appointmentId) {
      this.isLoading = true
      this.error = null
      
      try {
        // TODO: Replace with actual API call
        // const response = await createResource({
        //   url: 'hms_tz.api.appointments.delete_appointment',
        //   params: { id: appointmentId }
        // }).fetch()
        
        this.appointments = this.appointments.filter(app => app.id !== appointmentId)
        return { success: true }
      } catch (error) {
        this.error = error.message
        console.error('Error deleting appointment:', error)
        return { success: false, error: error.message }
      } finally {
        this.isLoading = false
      }
    },

    async cancelAppointment(appointmentId) {
      return this.updateAppointment(appointmentId, { status: 'cancelled' })
    },

    async completeAppointment(appointmentId) {
      return this.updateAppointment(appointmentId, { status: 'completed' })
    }
  }
})
