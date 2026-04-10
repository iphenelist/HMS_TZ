import dayjs from "dayjs";
import { createResource } from "frappe-ui";
import { defineStore } from "pinia";
import { computed, ref } from "vue";

export const useOTRosterStore = defineStore("otRoster", () => {
  // Filter state
  const company = ref("");
  const startDate = ref("");
  const frequency = ref("Weekly");
  const endDate = ref("");

  // Data state
  const theaterRooms = ref([]);
  const schedules = ref([]);

  // Loading state
  const isLoading = ref(false);

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

  // Build lookup: theater_room -> date -> [schedules]
  const scheduleMap = computed(() => {
    const map = {};
    for (const s of schedules.value) {
      const key = `${s.theater_room}|${s.date}`;
      if (!map[key]) map[key] = [];
      map[key].push(s);
    }
    return map;
  });

  function getSchedules(theaterRoom, date) {
    return scheduleMap.value[`${theaterRoom}|${date}`] || [];
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
    url: "hms_tz.hms_tz.doctype.ot_schedule.roster.get_ot_roster_data",
    onSuccess(data) {
      theaterRooms.value = data.theater_rooms || [];
      schedules.value = data.schedules || [];
      isLoading.value = false;
    },
    onError() {
      isLoading.value = false;
    },
  });

  const saveResource = createResource({
    url: "hms_tz.hms_tz.doctype.ot_schedule.roster.save_ot_schedule",
    onSuccess() {
      loadRoster();
    },
  });

  const cancelResource = createResource({
    url: "hms_tz.hms_tz.doctype.ot_schedule.roster.cancel_ot_schedule",
    onSuccess() {
      loadRoster();
    },
  });

  const removeResource = createResource({
    url: "hms_tz.hms_tz.doctype.ot_schedule.roster.remove_ot_schedule",
    onSuccess() {
      loadRoster();
    },
  });

  const postponeResource = createResource({
    url: "hms_tz.hms_tz.doctype.ot_schedule.roster.postpone_ot_schedule",
    onSuccess() {
      loadRoster();
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
  }

  function saveSchedule(scheduleData) {
    return saveResource.submit({
      schedule_data: JSON.stringify(scheduleData),
    });
  }

  function cancelSchedule(name) {
    return cancelResource.submit({ name });
  }

  function removeSchedule(name) {
    return removeResource.submit({ name });
  }

  function postponeSchedule(name) {
    return postponeResource.submit({ name });
  }

  return {
    company,
    startDate,
    frequency,
    endDate,
    theaterRooms,
    schedules,
    isLoading,
    dateColumns,
    scheduleMap,
    getSchedules,
    calculateEndDate,
    loadRoster,
    saveSchedule,
    cancelSchedule,
    removeSchedule,
    postponeSchedule,
    saveResource,
    cancelResource,
    removeResource,
    postponeResource,
  };
});
