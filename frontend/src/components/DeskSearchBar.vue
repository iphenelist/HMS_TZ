<template>
  <div class="desk-search-bar" ref="containerRef">
    <div class="search-input-wrapper">
      <svg
        class="search-icon"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
        />
      </svg>
      <input
        ref="searchInput"
        v-model="query"
        type="text"
        placeholder="Search records, pages..."
        class="search-input"
        @input="onInput"
        @focus="isFocused = true"
        @keydown.escape="clearSearch"
        @keydown.enter="onEnter"
        @keydown.down.prevent="moveSelection(1)"
        @keydown.up.prevent="moveSelection(-1)"
      />
      <kbd v-if="!query" class="search-shortcut">Ctrl K</kbd>
      <button v-else class="close-btn" @click="clearSearch">
        <svg
          class="h-3.5 w-3.5"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M6 18L18 6M6 6l12 12"
          />
        </svg>
      </button>
    </div>

    <!-- Results dropdown -->
    <div v-if="showResults" class="search-results">
      <div v-if="isSearching" class="search-status">
        <span class="search-spinner"></span>
        Searching...
      </div>

      <template v-else-if="results.length">
        <!-- Pages section -->
        <div v-if="pageResults.length" class="results-section">
          <div class="results-section-title">Pages</div>
          <button
            v-for="(item, idx) in pageResults"
            :key="'page-' + idx"
            class="result-item"
            :class="{
              'result-active': selectedIndex === getGlobalIndex('pages', idx),
            }"
            @click="navigateTo(item)"
            @mouseenter="selectedIndex = getGlobalIndex('pages', idx)"
          >
            <svg
              class="result-icon"
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
            <div class="result-text">
              <span class="result-title">{{ item.label }}</span>
              <span class="result-subtitle">{{ item.description }}</span>
            </div>
          </button>
        </div>

        <!-- Records section -->
        <div v-if="recordResults.length" class="results-section">
          <div class="results-section-title">Records</div>
          <button
            v-for="(item, idx) in recordResults"
            :key="'record-' + idx"
            class="result-item"
            :class="{
              'result-active':
                selectedIndex === getGlobalIndex('records', idx),
            }"
            @click="navigateTo(item)"
            @mouseenter="selectedIndex = getGlobalIndex('records', idx)"
          >
            <svg
              class="result-icon"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"
              />
            </svg>
            <div class="result-text">
              <span class="result-title">{{ item.label }}</span>
              <span class="result-subtitle">{{ item.description }}</span>
            </div>
          </button>
        </div>
      </template>

      <div v-else-if="query.length >= 2" class="search-status">
        No results found
      </div>
      <div v-else class="search-status">
        Type at least 2 characters to search
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted, onUnmounted } from "vue";
import { createResource } from "frappe-ui";

const containerRef = ref(null);
const searchInput = ref(null);
const query = ref("");
const isFocused = ref(false);
const isSearching = ref(false);
const selectedIndex = ref(-1);
const results = ref([]);
let debounceTimer = null;

// Common pages users might search for
const PAGES = [
  {
    label: "Patient",
    description: "Patient List",
    route: "/app/patient",
    type: "page",
  },
  {
    label: "Patient Encounter",
    description: "Patient Encounter List",
    route: "/app/patient-encounter",
    type: "page",
  },
  {
    label: "Patient Appointment",
    description: "Appointment List",
    route: "/app/patient-appointment",
    type: "page",
  },
  {
    label: "Employee",
    description: "Employee List",
    route: "/app/employee",
    type: "page",
  },
  {
    label: "Nursing Schedule",
    description: "Nursing Schedule List",
    route: "/app/nursing-schedule",
    type: "page",
  },
  {
    label: "Clinical Procedure",
    description: "Clinical Procedure List",
    route: "/app/clinical-procedure",
    type: "page",
  },
  {
    label: "Lab Test",
    description: "Lab Test List",
    route: "/app/lab-test",
    type: "page",
  },
  {
    label: "Vital Signs",
    description: "Vital Signs List",
    route: "/app/vital-signs",
    type: "page",
  },
  {
    label: "Drug Prescription",
    description: "Drug Prescription List",
    route: "/app/drug-prescription",
    type: "page",
  },
  {
    label: "Inpatient Record",
    description: "Inpatient Record List",
    route: "/app/inpatient-record",
    type: "page",
  },
  {
    label: "Shift Assignment",
    description: "Shift Assignment List",
    route: "/app/shift-assignment",
    type: "page",
  },
  {
    label: "Shift Type",
    description: "Shift Type List",
    route: "/app/shift-type",
    type: "page",
  },
  {
    label: "Healthcare Service Unit",
    description: "Service Unit List",
    route: "/app/healthcare-service-unit",
    type: "page",
  },
  {
    label: "Company",
    description: "Company List",
    route: "/app/company",
    type: "page",
  },
  {
    label: "Department",
    description: "Department List",
    route: "/app/department",
    type: "page",
  },
  {
    label: "Designation",
    description: "Designation List",
    route: "/app/designation",
    type: "page",
  },
  {
    label: "Branch",
    description: "Branch List",
    route: "/app/branch",
    type: "page",
  },
  {
    label: "HMS TZ Setting",
    description: "HMS TZ Settings",
    route: "/app/hms-tz-setting",
    type: "page",
  },
  {
    label: "Nurse Roster",
    description: "Open Nurse Roster",
    route: "/frontend/nurse-roster",
    type: "page",
  },
  {
    label: "OT Roster",
    description: "Open OT Roster",
    route: "/frontend/ot-roster",
    type: "page",
  },
];

const pageResults = computed(() =>
  results.value.filter((r) => r.type === "page")
);
const recordResults = computed(() =>
  results.value.filter((r) => r.type === "record")
);
const showResults = computed(() => isFocused.value && query.value.length > 0);

function getGlobalIndex(section, localIdx) {
  if (section === "pages") return localIdx;
  return pageResults.value.length + localIdx;
}

function clearSearch() {
  query.value = "";
  results.value = [];
  selectedIndex.value = -1;
  searchInput.value?.blur();
  isFocused.value = false;
}

function onInput() {
  clearTimeout(debounceTimer);
  selectedIndex.value = -1;

  if (query.value.length < 2) {
    results.value = [];
    return;
  }

  debounceTimer = setTimeout(() => search(), 300);
}

async function search() {
  const q = query.value.trim().toLowerCase();
  if (q.length < 2) return;

  isSearching.value = true;

  // 1. Filter matching pages
  const matchedPages = PAGES.filter(
    (p) =>
      p.label.toLowerCase().includes(q) ||
      p.description.toLowerCase().includes(q)
  );

  // 2. Search records via global search
  let records = [];
  try {
    const data = await searchResource.fetch({
      doctype: "DocType",
      filters: {},
      or_filters: {},
    });
    // Use the global search API instead
    records = await searchGlobalRecords(q);
  } catch (e) {
    // Fallback: search common doctypes individually
    records = await searchCommonDoctypes(q);
  }

  results.value = [...matchedPages, ...records];
  isSearching.value = false;
}

async function searchGlobalRecords(q) {
  try {
    const response = await fetch(
      `/api/method/frappe.utils.global_search.search?text=${encodeURIComponent(
        q
      )}&start=0&limit=8`,
      {
        headers: {
          "X-Frappe-CSRF-Token": getCSRFToken(),
          Accept: "application/json",
        },
      }
    );
    const json = await response.json();
    if (json.message) {
      return json.message.map((r) => ({
        label: r.name,
        description: r.doctype,
        route: `/app/${toKebabCase(r.doctype)}/${encodeURIComponent(r.name)}`,
        type: "record",
      }));
    }
  } catch (e) {
    // Fallback silently
  }
  return [];
}

async function searchCommonDoctypes(q) {
  const doctypes = ["Patient", "Employee", "Patient Encounter"];
  const allResults = [];

  for (const dt of doctypes) {
    try {
      const response = await fetch(
        `/api/method/frappe.client.get_list?doctype=${encodeURIComponent(
          dt
        )}&filters=${encodeURIComponent(
          JSON.stringify({ name: ["like", `%${q}%`] })
        )}&fields=${encodeURIComponent(
          JSON.stringify(["name"])
        )}&limit_page_length=3`,
        {
          headers: {
            "X-Frappe-CSRF-Token": getCSRFToken(),
            Accept: "application/json",
          },
        }
      );
      const json = await response.json();
      if (json.message) {
        allResults.push(
          ...json.message.map((r) => ({
            label: r.name,
            description: dt,
            route: `/app/${toKebabCase(dt)}/${encodeURIComponent(r.name)}`,
            type: "record",
          }))
        );
      }
    } catch (e) {
      // Skip silently
    }
  }
  return allResults;
}

function getCSRFToken() {
  return (
    document.cookie
      .split("; ")
      .find((row) => row.startsWith("csrf_token="))
      ?.split("=")[1] || ""
  );
}

function toKebabCase(str) {
  return str.replace(/\s+/g, "-").toLowerCase();
}

function moveSelection(delta) {
  const total = results.value.length;
  if (total === 0) return;
  selectedIndex.value = (selectedIndex.value + delta + total) % total;
}

function onEnter() {
  if (selectedIndex.value >= 0 && selectedIndex.value < results.value.length) {
    navigateTo(results.value[selectedIndex.value]);
  }
}

function navigateTo(item) {
  window.location.href = item.route;
}

// Keyboard shortcut: Ctrl+K to focus search
function handleKeydown(e) {
  if ((e.ctrlKey || e.metaKey) && e.key === "k") {
    e.preventDefault();
    searchInput.value?.focus();
    isFocused.value = true;
  }
}

// Click outside to close results
function handleClickOutside(e) {
  if (containerRef.value && !containerRef.value.contains(e.target)) {
    isFocused.value = false;
  }
}

onMounted(() => {
  document.addEventListener("keydown", handleKeydown);
  document.addEventListener("click", handleClickOutside);
});

onUnmounted(() => {
  document.removeEventListener("keydown", handleKeydown);
  document.removeEventListener("click", handleClickOutside);
  clearTimeout(debounceTimer);
});
</script>

<style scoped>
.desk-search-bar {
  position: relative;
}

.search-input-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
  background: white;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  padding: 0 10px;
  height: 36px;
  width: 320px;
  transition: all 0.2s ease;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
}

.search-input-wrapper:focus-within {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.search-icon {
  width: 16px;
  height: 16px;
  color: #9ca3af;
  flex-shrink: 0;
}

.search-input {
  flex: 1;
  border: none;
  outline: none;
  font-size: 13px;
  color: #1f2937;
  background: transparent;
  min-width: 0;
}

.search-input::placeholder {
  color: #9ca3af;
}

.close-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border-radius: 4px;
  border: none;
  background: transparent;
  color: #9ca3af;
  cursor: pointer;
  flex-shrink: 0;
}

.close-btn:hover {
  background: #f3f4f6;
  color: #6b7280;
}

.search-shortcut {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  padding: 1px 5px;
  font-size: 10px;
  font-family: inherit;
  color: #9ca3af;
  background: #f3f4f6;
  border: 1px solid #e5e7eb;
  border-radius: 4px;
  white-space: nowrap;
  flex-shrink: 0;
}

.search-results {
  position: absolute;
  top: calc(100% + 4px);
  right: 0;
  width: 360px;
  max-height: 380px;
  overflow-y: auto;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.08), 0 4px 10px rgba(0, 0, 0, 0.04);
  z-index: 50;
}

.search-status {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 14px 16px;
  font-size: 13px;
  color: #6b7280;
}

.search-spinner {
  width: 14px;
  height: 14px;
  border: 2px solid #e5e7eb;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.results-section {
  padding: 4px 0;
}

.results-section + .results-section {
  border-top: 1px solid #f3f4f6;
}

.results-section-title {
  padding: 6px 16px 4px;
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #9ca3af;
}

.result-item {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 8px 16px;
  border: none;
  background: transparent;
  cursor: pointer;
  text-align: left;
  transition: background 0.1s ease;
}

.result-item:hover,
.result-active {
  background: #f3f4f6;
}

.result-icon {
  width: 16px;
  height: 16px;
  color: #9ca3af;
  flex-shrink: 0;
}

.result-text {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.result-title {
  font-size: 13px;
  font-weight: 500;
  color: #1f2937;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.result-subtitle {
  font-size: 11px;
  color: #9ca3af;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
