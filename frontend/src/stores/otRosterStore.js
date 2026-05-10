import dayjs from "dayjs";
import { createResource } from "frappe-ui";
import { defineStore } from "pinia";
import { computed, ref } from "vue";

export const useOTRosterStore = defineStore("otRoster", () => {
  // Filter state
  const company = ref("");
  const currentYear = ref(new Date().getFullYear());
  const currentMonth = ref(new Date().getMonth()); // 0-indexed

  // Data state
  const theaterRooms = ref([]);
  const schedules = ref([]);
  const isLoading = ref(false);

  // Calendar grid dates (includes padding days from prev/next month)
  const calendarDates = computed(() => {
    const firstOfMonth = new Date(currentYear.value, currentMonth.value, 1);
    const lastOfMonth = new Date(currentYear.value, currentMonth.value + 1, 0);

    // Grid starts on Sunday of the week containing the 1st
    const gridStart = new Date(firstOfMonth);
    gridStart.setDate(gridStart.getDate() - gridStart.getDay());

    // Grid ends on Saturday of the week containing the last day
    const gridEnd = new Date(lastOfMonth);
    gridEnd.setDate(gridEnd.getDate() + (6 - gridEnd.getDay()));

    const dates = [];
    const current = new Date(gridStart);
    while (current <= gridEnd) {
      dates.push({
        date: dayjs(current).format("YYYY-MM-DD"),
        day: current.getDate(),
        isCurrentMonth: current.getMonth() === currentMonth.value,
        isToday: dayjs(current).isSame(dayjs(), "day"),
        isWeekend: current.getDay() === 0 || current.getDay() === 6,
        isPast: dayjs(current).isBefore(dayjs(), "day"),
      });
      current.setDate(current.getDate() + 1);
    }
    return dates;
  });

  const calendarRows = computed(() => calendarDates.value.length / 7);

  // Data range for API calls (first and last date in calendar grid)
  const dataStartDate = computed(() =>
    calendarDates.value.length ? calendarDates.value[0].date : ""
  );
  const dataEndDate = computed(() =>
    calendarDates.value.length
      ? calendarDates.value[calendarDates.value.length - 1].date
      : ""
  );

  // Schedule lookup: date → [schedules]
  const scheduleMap = computed(() => {
    const map = {};
    for (const s of schedules.value) {
      if (!map[s.date]) map[s.date] = [];
      map[s.date].push(s);
    }
    return map;
  });

  function getSchedules(date) {
    return scheduleMap.value[date] || [];
  }

  // Theater room display-name lookup
  const theaterRoomMap = computed(() => {
    const map = {};
    for (const room of theaterRooms.value) {
      map[room.name] = room.healthcare_service_unit_name || room.name;
    }
    return map;
  });

  function getTheaterRoomLabel(roomName) {
    return theaterRoomMap.value[roomName] || roomName;
  }

  // Month/year label
  const monthYearLabel = computed(() =>
    dayjs(new Date(currentYear.value, currentMonth.value)).format("MMMM YYYY")
  );

  // Navigation
  function goToNextMonth() {
    if (currentMonth.value === 11) {
      currentMonth.value = 0;
      currentYear.value++;
    } else {
      currentMonth.value++;
    }
  }

  function goToPrevMonth() {
    if (currentMonth.value === 0) {
      currentMonth.value = 11;
      currentYear.value--;
    } else {
      currentMonth.value--;
    }
  }

  function goToDate(dateStr) {
    if (!dateStr) return;
    const d = dayjs(dateStr);
    currentYear.value = d.year();
    currentMonth.value = d.month();
  }

  function goToToday() {
    currentYear.value = new Date().getFullYear();
    currentMonth.value = new Date().getMonth();
  }

  // ── API resources ──────────────────────────────────────────────
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
    if (!company.value || !dataStartDate.value || !dataEndDate.value) return;
    isLoading.value = true;
    rosterDataResource.submit({
      company: company.value,
      start_date: dataStartDate.value,
      end_date: dataEndDate.value,
    });
  }

  function saveSchedule(scheduleData) {
    return saveResource.submit({
      schedule_data: JSON.stringify(scheduleData),
    });
  }

  function removeSchedule(name) {
    return removeResource.submit({ name });
  }

  function postponeSchedule(name) {
    return postponeResource.submit({ name });
  }

  return {
    company,
    currentYear,
    currentMonth,
    theaterRooms,
    schedules,
    isLoading,
    calendarDates,
    calendarRows,
    dataStartDate,
    dataEndDate,
    scheduleMap,
    monthYearLabel,
    getSchedules,
    getTheaterRoomLabel,
    goToNextMonth,
    goToPrevMonth,
    goToDate,
    goToToday,
    loadRoster,
    saveSchedule,
    removeSchedule,
    postponeSchedule,
    saveResource,
    removeResource,
    postponeResource,
  };
});
