<template>
  <td
    class="relative border border-dashed border-gray-400 rounded-lg px-1 py-1 text-center"
    :class="cellClasses"
    @click="handleCellClick"
  >
    <!-- Existing assignment (read-only pill) -->
    <div
      v-if="assignment && !showDialog"
      class="flex items-center justify-center gap-1"
    >
      <span
        class="inline-flex max-w-[100px] items-center truncate rounded-full px-2 py-1 text-xs font-medium"
        :class="pillClasses"
        :title="displayValue"
      >
        {{ displayValue }}
      </span>
      <!-- Edit button: only shown for future/today dates -->
      <button
        v-if="!isPastDate"
        class="flex h-6 w-6 shrink-0 items-center justify-center rounded-md border border-gray-300 bg-white text-gray-500 shadow-sm hover:border-blue-300 hover:bg-blue-50 hover:text-blue-600"
        @click.stop="openEditDialog"
        title="Edit assignment"
      >
        <svg
          class="h-3.5 w-3.5"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          stroke-width="2"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"
          />
        </svg>
      </button>
    </div>

    <!-- Empty cell (+): only clickable for future/today dates -->
    <div
      v-else-if="!assignment && !showDialog"
      class="flex h-8 items-center justify-center rounded border border-dashed transition-colors"
      :class="
        isPastDate
          ? 'border-gray-100 text-gray-200'
          : 'border-gray-200 text-gray-400 hover:border-blue-400 hover:bg-blue-50/50 hover:text-blue-500'
      "
    >
      <svg
        class="h-3.5 w-3.5"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        stroke-width="2.5"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          d="M12 4v16m8-8H4"
        />
      </svg>
    </div>

    <!-- Assignment Dialog -->
    <Dialog
      :options="{
        title: assignment ? 'Edit Assignment' : 'New Assignment',
        size: 'sm',
        actions: dialogActions,
      }"
      v-model="showDialog"
      @close="cancelEdit"
    >
      <template #body-content>
        <div class="flex flex-col gap-4">
          <!-- Nurse & Date info -->
          <div
            class="flex items-center gap-3 rounded-lg bg-gray-50 px-3 py-2"
          >
            <div class="text-sm">
              <span class="text-gray-500">Nurse:</span>
              <span class="ml-1 font-medium text-gray-800">{{
                nurse
              }}</span>
            </div>
            <div class="text-sm">
              <span class="text-gray-500">Date:</span>
              <span class="ml-1 font-medium text-gray-800">{{ date }}</span>
            </div>
          </div>

          <!-- Assignment Based On -->
          <div>
            <FormControl
              type="select"
              label="Assignment Based On"
              :options="assignBasedOnOptions"
              v-model="editAssignBasedOn"
            />
          </div>

          <!-- Service Unit Type (searchable autocomplete) -->
          <div v-if="editAssignBasedOn === 'Service Unit Type'">
            <FormControl
              type="autocomplete"
              label="Service Unit Type"
              :options="serviceUnitTypeOptions"
              v-model="selectedServiceUnitType"
              placeholder="Search service unit type..."
            />
          </div>

          <!-- Service Unit (searchable autocomplete) -->
          <div v-if="editAssignBasedOn === 'Service Unit'">
            <FormControl
              type="autocomplete"
              label="Service Unit"
              :options="serviceUnitOptions"
              v-model="selectedServiceUnit"
              placeholder="Search service unit..."
            />
          </div>

          <!-- Remove button for existing assignments -->
          <div v-if="assignment && assignment.name" class="border-t pt-3">
            <Button
              variant="subtle"
              theme="red"
              class="w-full"
              @click="removeAssignment"
            >
              <template #prefix>
                <svg
                  class="h-4 w-4"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  stroke-width="2"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                  />
                </svg>
              </template>
              Remove Assignment
            </Button>
          </div>
        </div>
      </template>
    </Dialog>
  </td>
</template>

<script setup>
import { computed, ref } from "vue";

const props = defineProps({
  nurse: { type: String, required: true },
  date: { type: String, required: true },
  isWeekend: { type: Boolean, default: false },
  isPastDate: { type: Boolean, default: false },
  assignment: { type: Object, default: null },
  serviceUnitTypes: { type: Array, default: () => [] },
  serviceUnits: { type: Array, default: () => [] },
});

const emit = defineEmits(["assign", "edit", "remove"]);

const showDialog = ref(false);
const editAssignBasedOn = ref("Service Unit Type");
const selectedServiceUnitType = ref(null);
const selectedServiceUnit = ref(null);

const assignBasedOnOptions = [
  { label: "Service Unit Type", value: "Service Unit Type" },
  { label: "Service Unit", value: "Service Unit" },
];

const displayValue = computed(() => {
  if (!props.assignment) return "";
  if (props.assignment.assign_based_on === "Service Unit") {
    return props.assignment.service_unit || "";
  }
  return props.assignment.service_unit_type || "";
});

// Options formatted for autocomplete
const serviceUnitTypeOptions = computed(() =>
  props.serviceUnitTypes.map((s) => ({ label: s, value: s })),
);

const serviceUnitOptions = computed(() =>
  props.serviceUnits.map((s) => ({
    label: s.name,
    value: s.name,
  })),
);

// The currently selected value string
const currentEditValue = computed(() => {
  if (editAssignBasedOn.value === "Service Unit Type") {
    return selectedServiceUnitType.value?.value || "";
  }
  return selectedServiceUnit.value?.value || "";
});

const pillClasses = computed(() => {
  if (props.assignment?._pending) return "bg-yellow-100 text-yellow-800";
  return "bg-blue-100 text-blue-800";
});

const cellClasses = computed(() => ({
  "bg-orange-50/50": props.isWeekend && !showDialog.value,
  "cursor-pointer": !showDialog.value && !props.assignment && !props.isPastDate,
  "bg-blue-50/30": props.assignment && !props.assignment._pending,
  "bg-yellow-50/50": props.assignment?._pending,
}));

const dialogActions = computed(() => [
  {
    label: "Cancel",
    variant: "subtle",
    onClick: () => cancelEdit(),
  },
  {
    label: props.assignment ? "Update" : "Assign",
    variant: "solid",
    disabled: !currentEditValue.value,
    onClick: () => confirmEdit(),
  },
]);

function handleCellClick() {
  // Do not allow opening dialog for past dates
  if (props.isPastDate) return;
  if (!props.assignment && !showDialog.value) {
    openNewDialog();
  }
}

function openNewDialog() {
  editAssignBasedOn.value = "Service Unit Type";
  selectedServiceUnitType.value = null;
  selectedServiceUnit.value = null;
  showDialog.value = true;
}

function openEditDialog() {
  // Do not allow editing past dates
  if (props.isPastDate) return;

  if (props.assignment) {
    editAssignBasedOn.value =
      props.assignment.assign_based_on || "Service Unit Type";
    if (props.assignment.assign_based_on === "Service Unit") {
      const val = props.assignment.service_unit || "";
      selectedServiceUnit.value = val ? { label: val, value: val } : null;
      selectedServiceUnitType.value = null;
    } else {
      const val = props.assignment.service_unit_type || "";
      selectedServiceUnitType.value = val
        ? { label: val, value: val }
        : null;
      selectedServiceUnit.value = null;
    }
  }
  showDialog.value = true;
}

function confirmEdit() {
  const val = currentEditValue.value;
  if (!val) return;

  if (props.assignment?.name) {
    emit("edit", {
      nurse: props.nurse,
      date: props.date,
      assignBasedOn: editAssignBasedOn.value,
      value: val,
      existingName: props.assignment.name,
    });
  } else {
    emit("assign", {
      nurse: props.nurse,
      date: props.date,
      assignBasedOn: editAssignBasedOn.value,
      value: val,
    });
  }
  showDialog.value = false;
}

function cancelEdit() {
  showDialog.value = false;
  selectedServiceUnitType.value = null;
  selectedServiceUnit.value = null;
}

function removeAssignment() {
  emit("remove", {
    nurse: props.nurse,
    date: props.date,
    existingName: props.assignment?.name || props.assignment?.existing_name,
  });
  showDialog.value = false;
}
</script>
