<template>
  <div class="practitioner-card h-full">
    <div class="flex items-center space-x-2 p-2 bg-white h-full border-r border-gray-200 hover:bg-gray-50 transition-colors w-full">
      <!-- Avatar -->
      <div class="flex-shrink-0">
        <Avatar
          :label="practitioner.avatar"
          :image="practitioner.image"
          size="xs"
          :class="practitioner.is_available ? 'ring-2 ring-green-200' : 'ring-2 ring-red-200'"
        />
      </div>
      
      <!-- Practitioner Info -->
      <div class="flex-1 min-w-0">
        <h3 class="text-xs font-semibold text-black truncate">
          {{ practitioner.name }}
        </h3>
        <p class="text-xs text-gray-600 truncate">
          {{ practitioner.specialty }}
        </p>
        <div class="flex items-center mt-0.5">
          <Badge
            :label="practitioner.is_available ? 'Available' : 'Unavailable'"
            :theme="practitioner.is_available ? 'green' : 'red'"
            size="sm"
          />
        </div>
      </div>
      
      <!-- Actions Menu -->
      <div class="flex-shrink-0">
        <Dropdown :options="menuOptions" placement="bottom-end">
          <template #default="{ open }">
            <Button variant="ghost" size="sm">
              <FeatherIcon name="more-vertical" class="h-3 w-3 text-gray-600" />
            </Button>
          </template>
        </Dropdown>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { FeatherIcon, Avatar, Badge, Button, Dropdown, toast } from 'frappe-ui'
import { usePractitionerStore } from '@/stores/practitioners'

const props = defineProps({
  practitioner: {
    type: Object,
    required: true
  }
})

const practitionerStore = usePractitionerStore()

// Menu options
const menuOptions = computed(() => [
  {
    label: 'View Details',
    icon: 'user',
    handler: () => viewPractitionerDetails()
  },
  {
    label: props.practitioner.is_available ? 'Mark Unavailable' : 'Mark Available',
    icon: props.practitioner.is_available ? 'user-x' : 'user-check',
    handler: () => toggleAvailability()
  },
  {
    label: 'View Schedule',
    icon: 'calendar',
    handler: () => viewSchedule()
  },
  {
    label: 'Contact Info',
    icon: 'phone',
    handler: () => showContactInfo()
  }
])

const viewPractitionerDetails = () => {
  console.log('View practitioner details:', props.practitioner)
  toast.info(`Viewing details for ${props.practitioner.name}`)
  // TODO: Implement practitioner details modal
}

const toggleAvailability = async () => {
  try {
    const result = await practitionerStore.updatePractitionerAvailability(
      props.practitioner.id,
      !props.practitioner.is_available
    )
    
    if (result.success) {
      toast.success(
        `${props.practitioner.name} marked as ${!props.practitioner.is_available ? 'available' : 'unavailable'}`
      )
    } else {
      toast.error('Failed to update availability')
    }
  } catch (error) {
    toast.error('Error updating practitioner availability')
    console.error(error)
  }
}

const viewSchedule = () => {
  console.log('View practitioner schedule:', props.practitioner)
  toast.info(`Viewing schedule for ${props.practitioner.name}`)
  // TODO: Implement schedule view
}

const showContactInfo = () => {
  const contact = `${props.practitioner.name}\nEmail: ${props.practitioner.email}\nPhone: ${props.practitioner.phone}\nDepartment: ${props.practitioner.department}`
  alert(contact)
}
</script>

<style scoped>
.practitioner-card {
  @apply transition-all duration-200;
}

.practitioner-card:hover {
  @apply transform translate-y-[-1px];
}
</style>
