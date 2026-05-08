<template>
  <td
    class="relative border border-dashed border-gray-300 px-1 py-1 align-top"
    :class="cellClasses"
  >
    <!-- On Leave cell -->
    <div
      v-if="isOnLeave"
      class="flex h-10 items-center justify-center"
      title="Nurse is on leave"
    >
      <span
        class="inline-flex items-center gap-1 rounded-full bg-orange-100/80 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wide text-orange-700"
      >
        <svg
          class="h-3 w-3"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          stroke-width="2"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728L5.636 5.636"
          />
        </svg>
        On Leave
      </span>
    </div>

    <!-- Assignments list + add button -->
    <div v-else class="flex flex-col gap-1">
      <!-- Existing / pending assignments -->
      <div
        v-for="(asgn, idx) in assignments"
        :key="asgn.name || asgn._temp_id || idx"
        class="group/pill relative flex items-center gap-1"
      >
        <div
          class="flex min-w-0 flex-1 cursor-default flex-col rounded-md px-2 py-1 text-[10px] leading-tight shadow-sm transition-all"
          :class="
            asgn._pending
              ? 'bg-amber-50 border border-amber-300 text-amber-800'
              : 'bg-blue-50 border border-blue-200 text-blue-800'
          "
          :title="getTooltip(asgn)"
        >
          <!-- Location -->
          <span class="truncate font-semibold">
            {{
              asgn.assign_based_on === "Room"
                ? asgn.room || ""
                : asgn.ward || ""
            }}
          </span>
          <!-- Shift type + times -->
          <span class="truncate text-[9px] opacity-75">
            {{ asgn.shift_type || "" }}
            <template v-if="asgn.shift_start_time">
              · {{ formatTime(asgn.shift_start_time) }}-{{
                formatTime(asgn.shift_end_time)
              }}
            </template>
          </span>
        </div>
        <!-- Edit button -->
        <button
          v-if="!isPastDate && asgn.name"
          class="flex h-5 w-5 shrink-0 items-center justify-center rounded border border-gray-200 bg-white text-gray-400 opacity-0 transition-all hover:border-blue-400 hover:bg-blue-50 hover:text-blue-600 group-hover/pill:opacity-100"
          @click.stop="openEditDialog(asgn)"
          title="Edit assignment"
        >
          <svg
            class="h-2.5 w-2.5"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            stroke-width="2.5"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"
            />
          </svg>
        </button>
      </div>

      <!-- Add button (always visible for non-past, non-leave cells) -->
      <button
        v-if="!isPastDate"
        class="flex h-7 items-center justify-center rounded-md border border-dashed border-gray-200 text-gray-400 transition-all hover:border-blue-400 hover:bg-blue-50/60 hover:text-blue-500"
        @click.stop="openNewDialog"
        title="Add shift assignment"
      >
        <svg
          class="h-3 w-3"
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
      </button>

      <!-- Empty state for past cells with no assignments -->
      <div
        v-if="isPastDate && assignments.length === 0"
        class="flex h-8 items-center justify-center text-[10px] text-gray-300"
      >
        —
      </div>
    </div>

    <!-- Assignment Dialog -->
    <Dialog
      :options="{
        title: editingAssignment
          ? 'Edit Shift Assignment'
          : 'New Shift Assignment',
        size: 'md',
        actions: dialogActions,
      }"
      v-model="showDialog"
      @close="cancelEdit"
    >
      <template #body-content>
        <div class="flex flex-col gap-3">
          <!-- Nurse info bar -->
          <div
            class="flex items-center gap-2 rounded-lg bg-gradient-to-r from-blue-50 to-indigo-50 px-3 py-2"
          >
            <div
              class="flex h-7 w-7 items-center justify-center rounded-md bg-blue-100"
            >
              <svg
                class="h-3.5 w-3.5 text-blue-600"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                stroke-width="2"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
                />
              </svg>
            </div>
            <div class="min-w-0">
              <p class="truncate text-sm font-semibold text-gray-800">
                {{ nurse }}
              </p>
            </div>
          </div>

          <!-- Shift Type + Times (inline row) -->
          <div class="rounded-lg border border-gray-100 bg-gray-50/50 p-3">
            <div
              class="grid gap-3"
              :class="resolvedShiftTimes.start ? 'grid-cols-2' : 'grid-cols-1'"
            >
              <FormControl
                type="autocomplete"
                label="Shift Type *"
                :options="shiftTypeOptions"
                v-model="selectedShiftType"
                placeholder="Select shift..."
              />
              <div
                v-if="resolvedShiftTimes.start"
                class="flex items-center gap-2 self-end rounded-md bg-white px-3 py-[7px] shadow-sm"
              >
                <svg
                  class="h-3.5 w-3.5 shrink-0 text-indigo-500"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  stroke-width="2"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
                <span class="text-sm font-medium text-gray-700">{{
                  resolvedShiftTimes.start
                }}</span>
                <span class="text-gray-400">→</span>
                <span class="text-sm font-medium text-gray-700">{{
                  resolvedShiftTimes.end
                }}</span>
              </div>
            </div>
          </div>

          <!-- Date Range (side-by-side) -->
          <div class="rounded-lg border border-gray-100 bg-gray-50/50 p-3">
            <div class="grid grid-cols-2 gap-3">
              <FormControl
                type="date"
                label="Start Date *"
                v-model="editStartDate"
                :disabled="!!editingAssignment"
              />
              <FormControl
                type="date"
                label="End Date *"
                v-model="editEndDate"
                :disabled="!!editingAssignment"
              />
            </div>
            <div
              v-if="!editingAssignment && dateRangeCount > 1"
              class="mt-2 flex items-center gap-2 rounded-md bg-blue-50 px-2.5 py-1.5 text-[11px] text-blue-700"
            >
              <svg
                class="h-3 w-3 shrink-0"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                stroke-width="2"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              <span>
                Creates <strong>{{ dateRangeCount }}</strong> schedule{{
                  dateRangeCount > 1 ? "s" : ""
                }}
              </span>
            </div>
          </div>

          <!-- Location: Assign Based On + Ward/Room side-by-side -->
          <div
            class="grid grid-cols-2 gap-3 rounded-lg border border-gray-100 bg-gray-50/50 p-3"
          >
            <FormControl
              type="select"
              label="Assign Based On"
              :options="assignBasedOnOptions"
              v-model="editAssignBasedOn"
            />
            <div v-if="editAssignBasedOn === 'Ward'">
              <FormControl
                type="autocomplete"
                label="Ward *"
                :options="wardOptions"
                v-model="selectedWard"
                placeholder="Search ward..."
              />
            </div>
            <div v-if="editAssignBasedOn === 'Room'">
              <FormControl
                type="autocomplete"
                label="Room *"
                :options="roomOptions"
                v-model="selectedRoom"
                placeholder="Search room..."
              />
            </div>
          </div>

          <!-- Remove button for existing assignments -->
          <div
            v-if="editingAssignment && editingAssignment.name"
            class="border-t border-red-100 pt-3"
          >
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
import dayjs from "dayjs";
import { computed, ref } from "vue";

const props = defineProps({
  nurse: { type: String, required: true },
  date: { type: String, required: true },
  isWeekend: { type: Boolean, default: false },
  isPastDate: { type: Boolean, default: false },
  isOnLeave: { type: Boolean, default: false },
  assignments: { type: Array, default: () => [] },
  wards: { type: Array, default: () => [] },
  rooms: { type: Array, default: () => [] },
  shiftTypes: { type: Array, default: () => [] },
});

const emit = defineEmits(["assign", "edit", "remove"]);

const showDialog = ref(false);
const editingAssignment = ref(null); // null = new, object = editing

const editAssignBasedOn = ref("Ward");
const selectedWard = ref(null);
const selectedRoom = ref(null);
const selectedShiftType = ref(null);
const editStartDate = ref("");
const editEndDate = ref("");

const assignBasedOnOptions = [
  { label: "Ward", value: "Ward" },
  { label: "Room", value: "Room" },
];

// Autocomplete options
const wardOptions = computed(() =>
  props.wards.map((w) => ({ label: w, value: w }))
);

const roomOptions = computed(() =>
  props.rooms.map((r) => ({
    label: r.name,
    value: r.name,
    description: r.type || "",
  }))
);

const shiftTypeOptions = computed(() =>
  props.shiftTypes.map((s) => ({
    label: s.name,
    value: s.name,
    description:
      s.start_time && s.end_time
        ? `${formatTime(s.start_time)} - ${formatTime(s.end_time)}`
        : "",
  }))
);

// Resolve shift start/end times from the selected shift type
const resolvedShiftTimes = computed(() => {
  if (!selectedShiftType.value) return { start: "", end: "" };
  const val = selectedShiftType.value?.value || selectedShiftType.value;
  const found = props.shiftTypes.find((s) => s.name === val);
  if (!found) return { start: "", end: "" };
  return {
    start: formatTime(found.start_time),
    end: formatTime(found.end_time),
    raw_start: found.start_time,
    raw_end: found.end_time,
  };
});

// Date range count
const dateRangeCount = computed(() => {
  if (!editStartDate.value || !editEndDate.value) return 0;
  const start = dayjs(editStartDate.value);
  const end = dayjs(editEndDate.value);
  if (end.isBefore(start)) return 0;
  return end.diff(start, "day") + 1;
});

// Current location value
const currentLocationValue = computed(() => {
  if (editAssignBasedOn.value === "Ward") {
    return selectedWard.value?.value || "";
  }
  return selectedRoom.value?.value || "";
});

// Shift type value
const shiftTypeValue = computed(() => {
  return selectedShiftType.value?.value || selectedShiftType.value || "";
});

// Pill tooltip
function getTooltip(asgn) {
  const location = asgn.assign_based_on === "Room" ? asgn.room : asgn.ward;
  const shift = asgn.shift_type || "";
  const times =
    asgn.shift_start_time && asgn.shift_end_time
      ? `${formatTime(asgn.shift_start_time)}-${formatTime(
          asgn.shift_end_time
        )}`
      : "";
  return [location, shift, times].filter(Boolean).join(" · ");
}

function formatTime(timeStr) {
  if (!timeStr) return "";
  // Handle "HH:mm:ss" or "HH:mm" formats
  const parts = String(timeStr).split(":");
  if (parts.length >= 2) return `${parts[0]}:${parts[1]}`;
  return timeStr;
}

const cellClasses = computed(() => ({
  "bg-red-50/60": props.isOnLeave,
  "bg-orange-50/40": props.isWeekend && !props.isOnLeave,
}));

const dialogActions = computed(() => [
  {
    label: "Cancel",
    variant: "subtle",
    onClick: () => cancelEdit(),
  },
  {
    label: editingAssignment.value ? "Update" : "Assign",
    variant: "solid",
    disabled:
      !shiftTypeValue.value ||
      !currentLocationValue.value ||
      !editStartDate.value ||
      !editEndDate.value,
    onClick: () => confirmEdit(),
  },
]);

function openNewDialog() {
  if (props.isPastDate || props.isOnLeave) return;
  editingAssignment.value = null;
  editAssignBasedOn.value = "Ward";
  selectedWard.value = null;
  selectedRoom.value = null;
  selectedShiftType.value = null;
  editStartDate.value = props.date;
  editEndDate.value = props.date;
  showDialog.value = true;
}

function openEditDialog(asgn) {
  if (props.isPastDate || props.isOnLeave) return;
  editingAssignment.value = asgn;

  editAssignBasedOn.value = asgn.assign_based_on || "Ward";

  if (asgn.assign_based_on === "Room") {
    const val = asgn.room || "";
    selectedRoom.value = val ? { label: val, value: val } : null;
    selectedWard.value = null;
  } else {
    const val = asgn.ward || "";
    selectedWard.value = val ? { label: val, value: val } : null;
    selectedRoom.value = null;
  }

  const shiftVal = asgn.shift_type || "";
  selectedShiftType.value = shiftVal
    ? { label: shiftVal, value: shiftVal }
    : null;

  // For editing, only allow the single date
  editStartDate.value = asgn.assignment_date || props.date;
  editEndDate.value = asgn.assignment_date || props.date;

  showDialog.value = true;
}

function confirmEdit() {
  const locationVal = currentLocationValue.value;
  const shiftVal = shiftTypeValue.value;
  if (!locationVal || !shiftVal || !editStartDate.value || !editEndDate.value)
    return;

  if (editingAssignment.value?.name) {
    // Editing an existing saved assignment — include original shift for bulk matching
    emit("edit", {
      nurse: props.nurse,
      date: editingAssignment.value.assignment_date,
      assignBasedOn: editAssignBasedOn.value,
      value: locationVal,
      shiftType: shiftVal,
      shiftStartTime: resolvedShiftTimes.value.raw_start || "",
      shiftEndTime: resolvedShiftTimes.value.raw_end || "",
      existingName: editingAssignment.value.name,
      originalShiftType: editingAssignment.value.shift_type || "",
    });
  } else {
    // New assignment — emit with date range
    emit("assign", {
      nurse: props.nurse,
      startDate: editStartDate.value,
      endDate: editEndDate.value,
      assignBasedOn: editAssignBasedOn.value,
      value: locationVal,
      shiftType: shiftVal,
      shiftStartTime: resolvedShiftTimes.value.raw_start || "",
      shiftEndTime: resolvedShiftTimes.value.raw_end || "",
    });
  }

  showDialog.value = false;
}

function cancelEdit() {
  showDialog.value = false;
  editingAssignment.value = null;
}

function removeAssignment() {
  emit("remove", {
    nurse: props.nurse,
    date: editingAssignment.value?.assignment_date || props.date,
    existingName:
      editingAssignment.value?.name || editingAssignment.value?.existing_name,
  });
  showDialog.value = false;
  editingAssignment.value = null;
}
</script>
