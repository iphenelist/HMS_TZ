<template>
  <div class="flex h-screen w-screen overflow-hidden">
    <!-- Sidebar -->
    <div
      class="flex h-full flex-col border-r bg-gray-50"
      :class="isSidebarCollapsed ? 'w-12' : 'w-[220px]'"
    >
      <!-- Logo/Brand area -->
      <div class="flex items-center gap-2 border-b px-3 py-3">
        <div
          class="flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-blue-600 text-white"
        >
          <svg
            class="h-4 w-4"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"
            />
          </svg>
        </div>
        <span
          v-if="!isSidebarCollapsed"
          class="truncate text-sm font-semibold text-gray-800"
        >
          HMS TZ
        </span>
      </div>

      <!-- Nav links -->
      <nav class="flex flex-1 flex-col gap-0.5 p-2">
        <button
          class="flex h-8 items-center gap-2 rounded-md bg-blue-100 px-2 text-sm font-medium text-blue-700"
        >
          <svg
            class="h-4 w-4 shrink-0 text-blue-600"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
            />
          </svg>
          <span v-if="!isSidebarCollapsed">Nurse Roster</span>
        </button>
        <button
          class="flex h-8 items-center gap-2 rounded-md px-2 text-sm font-medium text-gray-700 hover:bg-gray-200"
          @click="goTo('/frontend/ot-roster')"
        >
          <svg
            class="h-4 w-4 shrink-0 text-gray-500"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2z"
            />
          </svg>
          <span v-if="!isSidebarCollapsed">OT Roster</span>
        </button>
        <button
          class="flex h-8 items-center gap-2 rounded-md px-2 text-sm font-medium text-gray-700 hover:bg-gray-200"
          @click="goTo('/app/nursing-schedule')"
        >
          <svg
            class="h-4 w-4 shrink-0 text-gray-500"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
            />
          </svg>
          <span v-if="!isSidebarCollapsed">Nursing Schedule</span>
        </button>
        <button
          class="flex h-8 items-center gap-2 rounded-md px-2 text-sm font-medium text-gray-700 hover:bg-gray-200"
          @click="goTo('/app/ot-schedule')"
        >
          <svg
            class="h-4 w-4 shrink-0 text-gray-500"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
          <span v-if="!isSidebarCollapsed">OT Schedule</span>
        </button>
      </nav>

      <!-- Collapse toggle -->
      <div class="border-t p-2">
        <button
          class="flex h-8 w-full items-center gap-2 rounded-md px-2 text-sm text-gray-500 hover:bg-gray-200"
          @click="isSidebarCollapsed = !isSidebarCollapsed"
        >
          <svg
            class="h-4 w-4 shrink-0 transition-transform duration-300"
            :class="{ 'rotate-180': isSidebarCollapsed }"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M11 19l-7-7 7-7m8 14l-7-7 7-7"
            />
          </svg>
          <span v-if="!isSidebarCollapsed">Collapse</span>
        </button>
      </div>
    </div>

    <!-- Main content -->
    <div class="flex flex-1 flex-col overflow-hidden">
      <!-- Header (centered) -->
      <div class="border-b bg-white px-6 py-4">
        <h1 class="text-center text-xl font-semibold text-gray-900">
          Nurse Roster
        </h1>
        <p class="mt-1 text-center text-sm" style="color: #60a5fa">
          Assign nurses to wards and rooms across dates
        </p>
      </div>

      <!-- Filter Bar (centered, reordered: Company → Frequency → Start Date → End Date) -->
      <div class="border-b bg-white px-6 py-4">
        <div class="flex flex-wrap items-end justify-center gap-4">
          <div class="w-52">
            <label class="mb-1 block text-xs font-medium text-gray-600">
              Company
            </label>
            <FormControl
              type="autocomplete"
              :options="companyOptions"
              v-model="companyModel"
              placeholder="Select Company"
            />
          </div>
          <div class="w-40">
            <label class="mb-1 block text-xs font-medium text-gray-600">
              Frequency
            </label>
            <FormControl
              type="select"
              :options="frequencyOptions"
              v-model="store.frequency"
              @change="store.calculateEndDate()"
            />
          </div>
          <div class="w-40">
            <label class="mb-1 block text-xs font-medium text-gray-600">
              Start Date
            </label>
            <DatePicker
              v-model="store.startDate"
              :formatValue="(val) => formatDateDisplay(val)"
              @change="store.calculateEndDate()"
              placeholder="Select date"
            />
          </div>
          <div class="w-40">
            <label class="mb-1 block text-xs font-medium text-gray-600">
              End Date
            </label>
            <DatePicker
              :modelValue="store.endDate"
              :formatValue="(val) => formatDateDisplay(val)"
              disabled
              class="bg-gray-50"
              placeholder="End date"
            />
          </div>
          <!-- Loading indicator inline -->
          <div v-if="store.isLoading" class="flex items-center pb-1">
            <LoadingIndicator class="h-5 w-5" />
          </div>
        </div>
      </div>

      <!-- Scrollable grid section -->
      <div class="flex-1 overflow-auto">
        <!-- Grid -->
        <div class="p-6" v-if="store.nurses.length">
          <div class="overflow-x-auto rounded-lg border bg-white shadow-sm">
            <table class="w-full border-collapse">
              <thead>
                <tr>
                  <th
                    class="sticky left-0 z-10 min-w-[180px] border-b border-r bg-gray-50 px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-600"
                  >
                    Nurse
                  </th>
                  <th
                    v-for="col in store.dateColumns"
                    :key="col.date"
                    class="min-w-[150px] border-b px-2 py-3 text-center text-xs font-semibold uppercase tracking-wider"
                    :class="
                      col.isWeekend
                        ? 'bg-orange-50 text-orange-700'
                        : 'bg-gray-50 text-gray-600'
                    "
                  >
                    {{ col.label }}
                  </th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="nurse in store.nurses"
                  :key="nurse.name"
                  class="group hover:bg-gray-50/50"
                >
                  <!-- Nurse name (sticky left) -->
                  <td
                    class="sticky left-0 z-10 border-b border-r bg-white px-4 py-2 group-hover:bg-gray-50"
                  >
                    <div class="text-sm font-medium text-gray-900">
                      {{ nurse.practitioner_name }}
                    </div>
                  </td>

                  <!-- Date cells -->
                  <RosterCell
                    v-for="col in store.dateColumns"
                    :key="`${nurse.name}-${col.date}`"
                    :nurse="nurse.name"
                    :date="col.date"
                    :is-weekend="col.isWeekend"
                    :is-past-date="isDatePast(col.date)"
                    :is-on-leave="store.isNurseOnLeave(nurse.name, col.date)"
                    :assignments="store.getAssignments(nurse.name, col.date)"
                    :wards="store.wards"
                    :rooms="store.rooms"
                    :shift-types="store.shiftTypes"
                    @assign="handleAssign"
                    @edit="handleEdit"
                    @remove="handleRemove"
                  />
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Empty state -->
        <div
          v-else-if="!store.isLoading"
          class="flex flex-col items-center justify-center px-6 py-20"
        >
          <div class="text-center">
            <svg
              class="mx-auto h-12 w-12 text-gray-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="1.5"
                d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
              />
            </svg>
            <h3 class="mt-4 text-sm font-medium text-gray-900">
              No roster loaded
            </h3>
            <p class="mt-1 text-sm text-gray-500">
              Select company, start date and frequency to load the roster
              automatically.
            </p>
          </div>
        </div>
      </div>

      <!-- Save bar (fixed at bottom of main content) -->
      <div
        v-if="store.hasPendingChanges()"
        class="border-t bg-white px-6 py-3 shadow-lg"
      >
        <div class="flex items-center justify-between">
          <p class="text-sm text-gray-600">
            <span class="font-semibold text-blue-600">{{
              store.pendingChanges.length
            }}</span>
            unsaved change(s)
          </p>
          <div class="flex gap-3">
            <Button variant="subtle" @click="store.pendingChanges = []">
              Discard
            </Button>
            <Button
              variant="solid"
              :loading="store.isSaving"
              @click="store.saveRoster()"
            >
              Save Changes
            </Button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import dayjs from "dayjs";
import { createResource } from "frappe-ui";
import { computed, onMounted, ref, watch } from "vue";
import RosterCell from "@/components/roster/RosterCell.vue";
import { useRosterStore } from "@/stores/rosterStore";

const store = useRosterStore();
const isSidebarCollapsed = ref(false);

// Company options
const companyOptions = ref([]);
const companyResource = createResource({
  url: "frappe.client.get_list",
  params: {
    doctype: "Company",
    fields: ["name"],
    order_by: "name asc",
    limit_page_length: 0,
  },
  auto: true,
  onSuccess(data) {
    companyOptions.value = data.map((c) => ({
      label: c.name,
      value: c.name,
    }));
  },
});

const frequencyOptions = [
  { label: "Daily", value: "Daily" },
  { label: "Weekly", value: "Weekly" },
  { label: "Monthly", value: "Monthly" },
  { label: "Quarterly", value: "Quarterly" },
  { label: "Bi-Yearly", value: "Bi-Yearly" },
  { label: "Yearly", value: "Yearly" },
];

// v-model computed for autocomplete: converts between option object and string
const companyModel = computed({
  get() {
    if (!store.company) return null;
    return { label: store.company, value: store.company };
  },
  set(option) {
    if (option && typeof option === "object") {
      store.company = option.value || option.label || "";
    } else {
      store.company = option || "";
    }
  },
});

// Check if a date is in the past (before today)
function isDatePast(dateStr) {
  return dayjs(dateStr).isBefore(dayjs(), "day");
}

function formatDateDisplay(val) {
  if (!val) return "";
  return dayjs(val).format("DD-MM-YYYY");
}

// Auto-load roster when all fields are filled
watch(
  () => [store.company, store.startDate, store.frequency, store.endDate],
  () => {
    if (store.company && store.startDate && store.frequency && store.endDate) {
      store.loadRoster();
    }
  }
);

function goTo(url) {
  window.location.href = url;
}

// Try to get params from URL
onMounted(() => {
  const params = new URLSearchParams(window.location.search);
  if (params.get("company")) store.company = params.get("company");
  if (params.get("start_date")) store.startDate = params.get("start_date");
  if (params.get("frequency")) store.frequency = params.get("frequency");
  if (store.startDate && store.frequency) {
    store.calculateEndDate();
  }
});

function handleAssign({
  nurse,
  startDate,
  endDate,
  assignBasedOn,
  value,
  shiftType,
  shiftStartTime,
  shiftEndTime,
}) {
  // Expand date range into individual pending changes
  let current = dayjs(startDate);
  const end = dayjs(endDate);
  while (current.isBefore(end) || current.isSame(end, "day")) {
    store.addPendingChange({
      nurse,
      assignment_date: current.format("YYYY-MM-DD"),
      assign_based_on: assignBasedOn,
      ward: assignBasedOn === "Ward" ? value : "",
      room: assignBasedOn === "Room" ? value : "",
      shift_type: shiftType,
      shift_start_time: shiftStartTime,
      shift_end_time: shiftEndTime,
      action: "add",
      _temp_id: `${nurse}-${current.format(
        "YYYY-MM-DD"
      )}-${shiftType}-${Date.now()}`,
    });
    current = current.add(1, "day");
  }
}

function handleEdit({
  nurse,
  date,
  assignBasedOn,
  value,
  shiftType,
  shiftStartTime,
  shiftEndTime,
  existingName,
}) {
  store.addPendingChange({
    nurse,
    assignment_date: date,
    assign_based_on: assignBasedOn,
    ward: assignBasedOn === "Ward" ? value : "",
    room: assignBasedOn === "Room" ? value : "",
    shift_type: shiftType,
    shift_start_time: shiftStartTime,
    shift_end_time: shiftEndTime,
    existing_name: existingName,
    action: "edit",
  });
}

function handleRemove({ nurse, date, existingName }) {
  store.addPendingChange({
    nurse,
    assignment_date: date,
    existing_name: existingName,
    action: "remove",
  });
}
</script>
