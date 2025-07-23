import { defineStore } from 'pinia'
import { createResource } from 'frappe-ui'

export const usePractitionerStore = defineStore('practitioners', {
  state: () => ({
    practitioners: [],
    isLoading: false,
    error: null,
    searchQuery: '',
    filterType: 'all', // 'all', 'available', 'department'
    selectedDepartment: '',
    lastFetchDate: null,
    company: "Nephro One Dialysis Clinic" // Default company, can be set dynamically
  }),

  getters: {
    filteredPractitioners: (state) => {
      let filtered = state.practitioners

      // Apply department filter
      if (state.filterType === 'department' && state.selectedDepartment) {
        filtered = filtered.filter(p => p.department === state.selectedDepartment)
      }

      // Apply availability filter
      if (state.filterType === 'available') {
        filtered = filtered.filter(p => p.is_available)
      }

      // Apply search query
      if (state.searchQuery) {
        filtered = filtered.filter(practitioner =>
          practitioner.name.toLowerCase().includes(state.searchQuery.toLowerCase()) ||
          practitioner.specialty.toLowerCase().includes(state.searchQuery.toLowerCase()) ||
          practitioner.department.toLowerCase().includes(state.searchQuery.toLowerCase())
        )
      }

      return filtered
    },

    availablePractitioners: (state) => (date) => {
      return state.practitioners.filter(p => p.is_available)
    },

    departments: (state) => {
      const depts = [...new Set(state.practitioners.map(p => p.department))]
      return depts.sort()
    }
  },

  actions: {
    setSearchQuery(query) {
      this.searchQuery = query
    },

    setFilter(type, department = '') {
      this.filterType = type
      this.selectedDepartment = department
    },

    clearFilters() {
      this.searchQuery = ''
      this.filterType = 'all'
      this.selectedDepartment = ''
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
        console.log('🔄 Fetching practitioners from API...', { company, date: currentDate })
        
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
        
      } finally {
        this.isLoading = false
      }
    },
  }
})
