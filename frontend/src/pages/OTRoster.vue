<template>
  <div class="flex h-screen w-screen overflow-hidden">
    <!-- Sidebar -->
    <div
      class="flex h-full flex-col border-r bg-gray-50"
      :class="isSidebarCollapsed ? 'w-12' : 'w-[220px]'"
    >
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
      <nav class="flex flex-1 flex-col gap-0.5 p-2">
        <button
          class="flex h-8 items-center gap-2 rounded-md px-2 text-sm font-medium text-gray-700 hover:bg-gray-200"
          @click="goTo('/frontend/nurse-roster')"
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
              d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
            />
          </svg>
          <span v-if="!isSidebarCollapsed">Nurse Roster</span>
        </button>
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
    <div class="flex flex-1 flex-col overflow-hidden bg-white">
      <!-- Top bar -->
      <div class="relative border-b bg-white px-6 py-4">
        <h1 class="text-center text-xl font-semibold text-gray-900">
          OT Roster
        </h1>
        <p class="mt-1 text-center text-sm" style="color: #60a5fa">
          Schedule surgeries across theater rooms
        </p>
        <div class="absolute right-6 top-1/2 -translate-y-1/2">
          <DeskSearchBar />
        </div>
      </div>

      <!-- Filter bar -->
      <div class="border-b bg-white px-6 py-3">
        <div class="flex flex-wrap items-end justify-center gap-4">
          <div class="w-52">
            <label class="mb-1 block text-xs font-medium text-gray-600"
              >Company</label
            >
            <FormControl
              type="autocomplete"
              :options="companyOptions"
              v-model="companyModel"
              placeholder="Select Company"
            />
          </div>
          <div class="w-40">
            <label class="mb-1 block text-xs font-medium text-gray-600"
              >Date</label
            >
            <div class="relative">
              <input
                type="date"
                :value="datePickerValue"
                @input="onDateInput"
                class="absolute inset-0 w-full opacity-0 cursor-pointer z-10"
              />
              <div
                class="flex items-center justify-between rounded-md border border-gray-300 bg-white px-2.5 py-1.5 text-sm text-gray-700 cursor-pointer hover:border-gray-400 transition-colors"
              >
                <span>{{ formattedDate }}</span>
                <svg
                  class="h-3.5 w-3.5 text-gray-400"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  stroke-width="2"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
                  />
                </svg>
              </div>
            </div>
          </div>
          <div v-if="store.isLoading" class="flex items-center pb-1">
            <LoadingIndicator class="h-5 w-5" />
          </div>
        </div>
      </div>

      <!-- Calendar -->
      <div
        v-if="store.company"
        class="flex flex-1 flex-col overflow-hidden p-4"
      >
        <!-- Month header bar -->
        <div class="mb-3 flex items-center justify-between">
          <span class="text-lg font-semibold text-gray-800">{{
            store.monthYearLabel
          }}</span>
          <div class="flex items-center gap-1">
            <button
              class="flex h-7 w-7 items-center justify-center rounded-md text-gray-500 hover:bg-gray-100 transition-colors"
              @click="
                store.goToPrevMonth();
                reloadIfReady();
              "
              title="Previous month"
            >
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
                  d="M15 19l-7-7 7-7"
                />
              </svg>
            </button>
            <button
              class="rounded-md px-2.5 py-1 text-xs font-medium text-gray-600 hover:bg-gray-100 transition-colors"
              @click="
                store.goToToday();
                reloadIfReady();
              "
            >
              Today
            </button>
            <button
              class="flex h-7 w-7 items-center justify-center rounded-md text-gray-500 hover:bg-gray-100 transition-colors"
              @click="
                store.goToNextMonth();
                reloadIfReady();
              "
              title="Next month"
            >
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
                  d="M9 5l7 7-7 7"
                />
              </svg>
            </button>
          </div>
        </div>

        <!-- Bordered calendar container -->
        <div
          class="flex flex-1 flex-col overflow-hidden rounded-lg border border-gray-200"
        >
          <!-- Day-of-week headers -->
          <div class="grid grid-cols-7 bg-gray-50/80">
            <div
              v-for="(dayName, idx) in dayNames"
              :key="dayName"
              class="py-2 text-center text-[11px] font-semibold uppercase tracking-wider text-gray-500"
              :class="idx < 6 ? 'border-r border-gray-200' : ''"
            >
              {{ dayName }}
            </div>
          </div>

          <!-- Calendar grid -->
          <div
            class="grid flex-1 grid-cols-7 overflow-hidden border-t border-gray-200"
            :style="{
              gridTemplateRows: `repeat(${store.calendarRows}, minmax(120px, 1fr))`,
            }"
          >
            <OTRosterCell
              v-for="cell in store.calendarDates"
              :key="cell.date"
              :cell="cell"
              :cell-schedules="store.getSchedules(cell.date)"
              :company="store.company"
              :theater-rooms="store.theaterRooms"
              :get-theater-room-label="store.getTheaterRoomLabel"
              @save="handleSave"
              @remove="handleRemove"
              @postpone="handlePostpone"
            />
          </div>
        </div>
      </div>

      <!-- Empty state -->
      <div v-else class="flex flex-1 flex-col items-center justify-center">
        <svg
          class="mx-auto h-12 w-12 text-gray-300"
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
        <h3 class="mt-3 text-sm font-medium text-gray-700">
          No roster loaded
        </h3>
        <p class="mt-1 text-xs text-gray-400">
          Select a company to view the OT calendar.
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import dayjs from "dayjs";
import { createResource } from "frappe-ui";
import { computed, onMounted, ref, watch } from "vue";
import OTRosterCell from "@/components/roster/OTRosterCell.vue";
import DeskSearchBar from "@/components/DeskSearchBar.vue";
import { useOTRosterStore } from "@/stores/otRosterStore";

const store = useOTRosterStore();
const isSidebarCollapsed = ref(false);
const dayNames = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

// Company options
const companyOptions = ref([]);
createResource({
  url: "frappe.client.get_list",
  params: {
    doctype: "Company",
    fields: ["name"],
    order_by: "name asc",
    limit_page_length: 0,
  },
  auto: true,
  onSuccess(data) {
    companyOptions.value = data.map((c) => ({ label: c.name, value: c.name }));
    // Auto-select when only one company is available
    if (companyOptions.value.length === 1 && !store.company) {
      store.company = companyOptions.value[0].value;
    }
  },
});

const companyModel = computed({
  get() {
    if (!store.company) return null;
    return { label: store.company, value: store.company };
  },
  set(option) {
    store.company =
      option && typeof option === "object"
        ? option.value || option.label || ""
        : option || "";
  },
});

// Date picker (DD-MM-YYYY display via overlay)
const datePickerValue = ref(dayjs().format("YYYY-MM-DD"));

const formattedDate = computed(() => {
  if (!datePickerValue.value) return "";
  return dayjs(datePickerValue.value).format("DD-MM-YYYY");
});

function onDateInput(e) {
  const val = e.target.value;
  if (val) {
    datePickerValue.value = val;
    store.goToDate(val);
    reloadIfReady();
  }
}

watch(
  () => store.company,
  () => reloadIfReady()
);

function reloadIfReady() {
  if (store.company) store.loadRoster();
}

function goTo(url) {
  window.location.href = url;
}

onMounted(() => {
  const params = new URLSearchParams(window.location.search);
  if (params.get("company")) store.company = params.get("company");
  if (params.get("date")) {
    datePickerValue.value = params.get("date");
    store.goToDate(params.get("date"));
  }
  reloadIfReady();
});

function handleSave(scheduleData) {
  store.saveSchedule(scheduleData);
}
function handleRemove(name) {
  store.removeSchedule(name);
}
function handlePostpone(name) {
  store.postponeSchedule(name);
}
</script>
