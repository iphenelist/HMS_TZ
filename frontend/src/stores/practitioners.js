import { defineStore } from 'pinia'

export const usePractitionerStore = defineStore('practitioners', {
  state: () => ({
    practitioners: [],
    isLoading: false,
    error: null,
    searchQuery: '',
    filterType: 'all', // 'all', 'available', 'department'
    selectedDepartment: ''
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

    async fetchPractitioners() {
      this.isLoading = true
      this.error = null
      
      try {
        // Sample data for now - replace with actual API call
        const samplePractitioners = [
          {
            id: 1,
            name: "Dr. John Smith",
            specialty: "Cardiology",
            avatar: "JS",
            email: "john.smith@hospital.com",
            phone: "+255123456789",
            is_available: true,
            department: "Internal Medicine"
          },
          {
            id: 2,
            name: "Dr. Sarah Johnson",
            specialty: "Dermatology",
            avatar: "SJ",
            email: "sarah.johnson@hospital.com",
            phone: "+255987654321",
            is_available: true,
            department: "Dermatology"
          },
          {
            id: 3,
            name: "Dr. Michael Brown",
            specialty: "Pediatrics",
            avatar: "MB",
            email: "michael.brown@hospital.com",
            phone: "+255456789123",
            is_available: true,
            department: "Pediatrics"
          },
          {
            id: 4,
            name: "Dr. Emily Davis",
            specialty: "Orthopedics",
            avatar: "ED",
            email: "emily.davis@hospital.com",
            phone: "+255789123456",
            is_available: true,
            department: "Orthopedics"
          },
          {
            id: 5,
            name: "Dr. Robert Wilson",
            specialty: "Neurology",
            avatar: "RW",
            email: "robert.wilson@hospital.com",
            phone: "+255321654987",
            is_available: false,
            department: "Neurology"
          }
        ]
        
        this.practitioners = samplePractitioners
      } catch (error) {
        this.error = error.message
        console.error('Error fetching practitioners:', error)
      } finally {
        this.isLoading = false
      }
    },

    async updatePractitionerAvailability(practitionerId, isAvailable) {
      try {
        const practitioner = this.practitioners.find(p => p.id === practitionerId)
        if (practitioner) {
          practitioner.is_available = isAvailable
        }
        return { success: true }
      } catch (error) {
        this.error = error.message
        console.error('Error updating practitioner availability:', error)
        return { success: false, error: error.message }
      }
    }
  }
})
