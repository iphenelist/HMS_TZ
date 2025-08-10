import { defineStore } from 'pinia'
import { createListResource } from 'frappe-ui'
import dayjs from 'dayjs'
import { useToast } from '../composables/useToast'

export const useAppointmentStore = defineStore('appointments', {
  state: () => ({
    appointments: [],
    selectedDate: dayjs().format('YYYY-MM-DD'),
    selectedCompany: '',
    isLoading: false,
    error: null,
    appointmentsResource: null
  }),

  getters: {
    appointmentsByTimeSlot: (state) => {
      const grouped = {}
      state.appointments.forEach(appointment => {
        const key = `${appointment.appointment_time}-${appointment.practitioner}`
        grouped[key] = appointment
      })
      return grouped
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
            'patient_sex',
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
            'invoiced',
            'referral_no',
            'remarks',
            'coverage_plan_name',
            'nhif_employer_name',
            'daily_limit',
            'apply_fasttrack_charge',
            'authorization_number',
            'poc_reference_no',
            'require_fingerprint',
            'require_facial_recognation',
            'biometric_method',
            'fpcode'
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
          patient: appointment.patient,
          patient_name: appointment.patient_name,
          patient_sex: appointment.patient_sex,
          practitioner: appointment.practitioner,
          appointment_time: dayjs(`2024-01-01 ${appointment.appointment_time}`).format('HH:mm'), // Normalize to HH:mm format
          appointment_date: appointment.appointment_date,
          status: appointment.status?.toLowerCase() || 'scheduled',
          appointment_type: appointment.appointment_type,
          department: appointment.department,
          company: appointment.company,
          insurance_company: appointment.insurance_company || 'Cash',
          insurance_subscription: appointment.insurance_subscription,
          billing_item: appointment.billing_item,
          paid_amount: appointment.paid_amount || 0,
          mode_of_payment: appointment.mode_of_payment,
          invoiced: appointment.invoiced,
          referral_no: appointment.referral_no,
          remarks: appointment.remarks,
          coverage_plan_name: appointment.coverage_plan_name,
          nhif_employer_name: appointment.nhif_employer_name,
          daily_limit: appointment.daily_limit,
          apply_fasttrack_charge: appointment.apply_fasttrack_charge,
          authorization_number: appointment.authorization_number,
          poc_reference_no: appointment.poc_reference_no,
          require_fingerprint: appointment.require_fingerprint,
          require_facial_recognation: appointment.require_facial_recognation,
          biometric_method: appointment.biometric_method,
          fpcode: appointment.fpcode,
        }))

      } catch (error) {
        this.error = error.message || 'Failed to fetch appointments'
        console.error('❌ Error fetching appointments:', error)
        const { notifications } = useToast()
        notifications.error.dataLoadFailed(error.message || 'appointments')
        this.appointments = []
        throw error
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

        return { success: true }
      } catch (error) {
        this.error = error.message
        console.error('Error updating appointment:', error)
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
