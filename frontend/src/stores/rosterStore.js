import dayjs from "dayjs";
import { createResource } from "frappe-ui";
import { defineStore } from "pinia";
import { computed, ref } from "vue";

export const useRosterStore = defineStore("roster", () => {
  // Filter state
  const company = ref("");
  const startDate = ref(dayjs().format("YYYY-MM-DD"));
  const duration = ref("Weekly");
  const endDate = ref("");

  // Optional employee-based filters
  const department = ref("");
  const designation = ref("");
  const branch = ref("");

  // Data state
  const nurses = ref([]);
  const assignments = ref([]);
  const wards = ref([]);
  const rooms = ref([]);
  const shiftTypes = ref([]);
  const nurseLeaves = ref({});

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
        isWeekend: current.day() === 0 || current.day() === 6,
      });
      current = current.add(1, "day");
    }
    return cols;
  });

  // Build a lookup map: nurse|date → array of assignments
  const assignmentMap = computed(() => {
    const map = {};

    // Group existing assignments
    for (const a of assignments.value) {
      const key = `${a.nurse}|${a.assignment_date}`;
      if (!map[key]) map[key] = [];
      map[key].push(a);
    }

    // Apply pending changes
    for (const change of pendingChanges.value) {
      const key = `${change.nurse}|${change.assignment_date}`;
      if (!map[key]) map[key] = [];

      if (change.action === "remove") {
        map[key] = map[key].filter((a) => a.name !== change.existing_name);
      } else if (change.action === "edit") {
        const idx = map[key].findIndex((a) => a.name === change.existing_name);
        if (idx >= 0) {
          map[key][idx] = { ...map[key][idx], ...change, _pending: true };
        }
      } else {
        // action === "add"
        map[key].push({ ...change, _pending: true });
      }
    }

    return map;
  });

  function getAssignments(nurse, date) {
    return assignmentMap.value[`${nurse}|${date}`] || [];
  }

  // Calculate end date based on duration
  function calculateEndDate() {
    if (!startDate.value || !duration.value) {
      endDate.value = "";
      return;
    }
    const durationMap = {
      Daily: { days: 0 },
      Weekly: { days: 6 },
      Monthly: { months: 1 },
      Quarterly: { months: 3 },
      "Bi-Yearly": { months: 6 },
      Yearly: { months: 12 },
    };
    const offset = durationMap[duration.value];
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

  // Calculate end date on store init (startDate defaults to today, duration to Weekly)
  calculateEndDate();

  // API resources
  const rosterDataResource = createResource({
    url: "hms_tz.hms_tz.doctype.nursing_schedule.roster.get_roster_data",
    onSuccess(data) {
      nurses.value = data.nurses || [];
      assignments.value = data.assignments || [];
      nurseLeaves.value = data.nurse_leave_dates || {};
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
      wards.value = data.wards || [];
      rooms.value = data.rooms || [];
      shiftTypes.value = data.shift_types || [];
    },
  });

  const saveResource = createResource({
    url: "hms_tz.hms_tz.doctype.nursing_schedule.roster.save_roster_assignments",
    onSuccess() {
      isSaving.value = false;
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
      department: department.value || undefined,
      designation: designation.value || undefined,
      branch: branch.value || undefined,
    });
    serviceOptionsResource.submit({
      company: company.value,
    });
  }

  function addPendingChange(change) {
    if (change.action === "add") {
      // Allow multiple add-actions per nurse+date (different shifts)
      pendingChanges.value.push(change);
    } else if (change.action === "edit" && change.existing_name) {
      // Replace any existing pending change for the same record
      pendingChanges.value = pendingChanges.value.filter(
        (c) => c.existing_name !== change.existing_name
      );
      pendingChanges.value.push(change);
    } else if (change.action === "remove" && change.existing_name) {
      // Remove any pending edits for this record and add a remove
      pendingChanges.value = pendingChanges.value.filter(
        (c) => c.existing_name !== change.existing_name
      );
      pendingChanges.value.push(change);
    }
  }

  function hasPendingChanges() {
    return pendingChanges.value.length > 0;
  }

  function isNurseOnLeave(nurse, date) {
    const leaveDates = nurseLeaves.value[nurse];
    return leaveDates ? leaveDates.includes(date) : false;
  }

  function saveRoster() {
    if (!pendingChanges.value.length) return;
    isSaving.value = true;
    saveResource.submit({
      company: company.value,
      start_date: startDate.value,
      end_date: endDate.value,
      assignments: JSON.stringify(pendingChanges.value),
    });
  }

  return {
    // State
    company,
    startDate,
    duration,
    endDate,
    department,
    designation,
    branch,
    nurses,
    assignments,
    wards,
    rooms,
    shiftTypes,
    nurseLeaves,
    pendingChanges,
    isLoading,
    isSaving,
    // Computed
    dateColumns,
    assignmentMap,
    // Methods
    getAssignments,
    calculateEndDate,
    loadRoster,
    addPendingChange,
    hasPendingChanges,
    isNurseOnLeave,
    saveRoster,
  };
});
