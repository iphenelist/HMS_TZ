import { defineStore } from 'pinia'
import { createListResource } from 'frappe-ui'
import dayjs from 'dayjs'

export const useAppointmentStore = defineStore('appointments', {
  state: () => ({
    appointments: [],
    selectedDate: dayjs().format('YYYY-MM-DD'),
    selectedCompany: '',
    selectedAppointment: null,
    isLoading: false,
    error: null,
    showAppointmentDialog: false,
    dialogMode: 'create', // 'create', 'edit', 'view'
    appointmentsResource: null
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
    initializeResource() {
      if (!this.appointmentsResource) {
        this.appointmentsResource = createListResource({
          doctype: 'Patient Appointment',
          fields: [
            'name',
            'patient',
            'patient_name',
            'practitioner',
            'appointment_time',
            'appointment_date',
            'status',
            'appointment_type',
            'department',
            'company',
            'insurance_company',
            'mode_of_payment',
            'billing_item',
            'paid_amount',
            'invoiced'
          ],
          filters: {},
          orderBy: 'appointment_time asc',
          pageLength: 999,
          auto: false
        })
      }
    },

    setSelectedDate(date) {
      // Ensure date is in YYYY-MM-DD format for Frappe
      const formattedDate = dayjs(date).format('YYYY-MM-DD')
      this.selectedDate = formattedDate
      this.fetchAppointments()
    },

    setSelectedCompany(company) {
      this.selectedCompany = company
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
      this.initializeResource()
      this.isLoading = true
      this.error = null

      try {
        // Build filters - start with date filter
        const filters = {
          appointment_date: this.selectedDate
        }

        // Only add company filter if a specific company is selected
        if (this.selectedCompany && this.selectedCompany.trim() && this.selectedCompany !== '') {
          filters.company = this.selectedCompany
        }

        // Update resource filters
        this.appointmentsResource.update({
          filters: filters
        })

        // Fetch data
        await this.appointmentsResource.reload()

        // Transform the data to match our expected format
        this.appointments = (this.appointmentsResource.data || []).map(appointment => ({
          id: appointment.name,
          name: appointment.name,
          patient_name: appointment.patient_name,
          patient_id: appointment.patient,
          practitioner_id: appointment.practitioner,
          time_slot: dayjs(`2024-01-01 ${appointment.appointment_time}`).format('HH:mm'), // Normalize to HH:mm format
          date: appointment.appointment_date,
          status: appointment.status?.toLowerCase() || 'scheduled',
          appointment_type: appointment.appointment_type,
          department: appointment.department,
          company: appointment.company,
          insurance_company: appointment.insurance_company || 'Cash',
          billing_item: appointment.billing_item,
          paid_amount: appointment.paid_amount || 0,
          item_rate: appointment.paid_amount || 0,
          mode_of_payment: appointment.mode_of_payment,
          invoiced: appointment.invoiced,
        }))

        console.log('✅ Appointments loaded:', this.appointments.length)
        console.log('✅ Transformed appointments:', this.appointments)
        console.log('✅ Appointments by time slot keys:', Object.keys(this.appointmentsByTimeSlot))

      } catch (error) {
        this.error = error.message || 'Failed to fetch appointments'
        console.error('❌ Error fetching appointments:', error)
        this.appointments = []
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
