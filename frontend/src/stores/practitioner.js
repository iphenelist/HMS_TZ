import { defineStore } from 'pinia'
import { createResource } from 'frappe-ui'
import { useToast } from '../composables/useToast'

export const usePractitionerStore = defineStore('practitioners', {
  state: () => ({
    practitioners: [],
    isLoading: false,
    error: null,
    searchQuery: '',
    lastFetchDate: null,
    company: ""
  }),

  getters: {
    filteredPractitioners: (state) => {
      let filtered = state.practitioners

      // Apply search query
      if (state.searchQuery) {
        filtered = filtered.filter(practitioner =>
          practitioner.name.toLowerCase().includes(state.searchQuery.toLowerCase()) ||
          practitioner.specialty.toLowerCase().includes(state.searchQuery.toLowerCase()) ||
          practitioner.department.toLowerCase().includes(state.searchQuery.toLowerCase())
        )
      }

      return filtered
    }
  },

  actions: {
    setSearchQuery(query) {
      this.searchQuery = query
    },

    async fetchPractitioners(company = null, date = null, forceRefresh = false) {
      // Check if we need to refetch
      const currentDate = date || new Date().toISOString().split('T')[0]
      
      if (!forceRefresh && 
          this.practitioners.length > 0 && 
          this.lastFetchDate === currentDate && 
          this.company === company) {
        return this.practitioners
      }

      this.isLoading = true
      this.error = null
      
      try {        
        // Call the backend API
        const resource = createResource({
          url: 'hms_tz.api.practitioner.get_practitioners',
          params: {
            company: company || this.company,
            date: currentDate
          },
          auto: false
        })

        await resource.fetch()

        if (resource.data) {
          this.practitioners = resource.data.practitioners || resource.data || []
          this.lastFetchDate = currentDate
          this.company = company || this.company
          
        } else {
          console.warn('⚠️ No practitioners data received from API')
          this.practitioners = []
        }
        
        return this.practitioners
        
      } catch (error) {
        console.warn('⚠️ API call failed, using sample data for testing:', error.message)
        const { notifications } = useToast()
        notifications.error.dataLoadFailed(error.message || 'practitioners')
        
      } finally {
        this.isLoading = false
      }
    },
  }
})
