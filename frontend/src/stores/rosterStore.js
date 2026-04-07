import dayjs from "dayjs";
import { createResource } from "frappe-ui";
import { defineStore } from "pinia";
import { computed, ref } from "vue";

export const useRosterStore = defineStore("roster", () => {
  // Filter state
  const company = ref("");
  const startDate = ref("");
  const frequency = ref("Weekly");
  const endDate = ref("");

  // Data state
  const nurses = ref([]);
  const assignments = ref([]);
  const serviceUnitTypes = ref([]);
  const serviceUnits = ref([]);

  // Pending changes (tracked before save)
  const pendingChanges = ref([]);

  // Loading state
  const isLoading = ref(false);
  const isSaving = ref(false);

  // Date columns
  const dateColumns = computed(() => {
    if (!startDate.value || !endDate.value) return [];
    const cols = [];
    let current = dayjs(startDate.value);
    const end = dayjs(endDate.value);
    while (current.isBefore(end) || current.isSame(end, "day")) {
      cols.push({
        date: current.format("YYYY-MM-DD"),
        label: current.format("ddd DD"),
        isWeekend:
          current.day() === 0 || current.day() === 6,
      });
      current = current.add(1, "day");
    }
    return cols;
  });

  // Build a lookup map: nurse -> date -> assignment
  const assignmentMap = computed(() => {
    const map = {};
    for (const a of assignments.value) {
      const key = `${a.nurse}|${a.assignment_date}`;
      map[key] = a;
    }
    // Overlay pending changes
    for (const change of pendingChanges.value) {
      const key = `${change.nurse}|${change.assignment_date}`;
      if (change.action === "remove") {
        delete map[key];
      } else {
        map[key] = { ...map[key], ...change, _pending: true };
      }
    }
    return map;
  });

  function getAssignment(nurse, date) {
    return assignmentMap.value[`${nurse}|${date}`] || null;
  }

  // Calculate end date
  function calculateEndDate() {
    if (!startDate.value || !frequency.value) {
      endDate.value = "";
      return;
    }
    const frequencyMap = {
      Daily: { days: 0 },
      Weekly: { days: 6 },
      Monthly: { months: 1 },
      Quarterly: { months: 3 },
      "Bi-Yearly": { months: 6 },
      Yearly: { months: 12 },
    };
    const offset = frequencyMap[frequency.value];
    if (!offset) return;

    if (offset.days !== undefined) {
      endDate.value = dayjs(startDate.value)
        .add(offset.days, "day")
        .format("YYYY-MM-DD");
    } else {
      endDate.value = dayjs(startDate.value)
        .add(offset.months, "month")
        .subtract(1, "day")
        .format("YYYY-MM-DD");
    }
  }

  // API resources
  const rosterDataResource = createResource({
    url: "hms_tz.hms_tz.doctype.nursing_schedule.roster.get_roster_data",
    onSuccess(data) {
      nurses.value = data.nurses || [];
      assignments.value = data.assignments || [];
      pendingChanges.value = [];
      isLoading.value = false;
    },
    onError() {
      isLoading.value = false;
    },
  });

  const serviceOptionsResource = createResource({
    url: "hms_tz.hms_tz.doctype.nursing_schedule.roster.get_service_options",
    onSuccess(data) {
      serviceUnitTypes.value = data.service_unit_types || [];
      serviceUnits.value = data.service_units || [];
    },
  });

  const saveResource = createResource({
    url: "hms_tz.hms_tz.doctype.nursing_schedule.roster.save_roster_assignments",
    onSuccess() {
      isSaving.value = false;
      // Reload after save
      loadRoster();
    },
    onError() {
      isSaving.value = false;
    },
  });

  function loadRoster() {
    if (!company.value || !startDate.value || !endDate.value) return;
    isLoading.value = true;
    rosterDataResource.submit({
      company: company.value,
      start_date: startDate.value,
      end_date: endDate.value,
    });
    serviceOptionsResource.submit({
      company: company.value,
    });
  }

  function addPendingChange(change) {
    // Remove any existing pending change for same nurse+date
    pendingChanges.value = pendingChanges.value.filter(
      (c) =>
        !(
          c.nurse === change.nurse &&
          c.assignment_date === change.assignment_date
        ),
    );
    pendingChanges.value.push(change);
  }

  function removePendingChange(nurse, date) {
    pendingChanges.value = pendingChanges.value.filter(
      (c) => !(c.nurse === nurse && c.assignment_date === date),
    );
  }

  function hasPendingChanges() {
    return pendingChanges.value.length > 0;
  }

  function saveRoster() {
    if (!pendingChanges.value.length) return;
    isSaving.value = true;
    saveResource.submit({
      company: company.value,
      start_date: startDate.value,
      end_date: endDate.value,
      frequency: frequency.value,
      assignments: JSON.stringify(pendingChanges.value),
    });
  }

  return {
    // State
    company,
    startDate,
    frequency,
    endDate,
    nurses,
    assignments,
    serviceUnitTypes,
    serviceUnits,
    pendingChanges,
    isLoading,
    isSaving,
    // Computed
    dateColumns,
    assignmentMap,
    // Methods
    getAssignment,
    calculateEndDate,
    loadRoster,
    addPendingChange,
    removePendingChange,
    hasPendingChanges,
    saveRoster,
  };
});
