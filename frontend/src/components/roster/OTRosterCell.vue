<template>
  <div
    class="flex flex-col overflow-hidden border-r border-b border-gray-200 last:border-r-0"
    :class="[cell.isCurrentMonth ? 'bg-white' : 'bg-gray-50/50']"
  >
    <!-- Day number header -->
    <div class="flex items-center justify-between px-2 py-1 shrink-0">
      <span
        class="inline-flex h-5 min-w-[20px] items-center justify-center text-xs font-medium"
        :class="[
          !cell.isCurrentMonth
            ? 'text-gray-300'
            : cell.isToday
            ? 'rounded-full bg-blue-600 px-1.5 text-white'
            : cell.isWeekend
            ? 'text-red-400'
            : 'text-gray-700',
        ]"
      >
        {{ cell.day }}
      </span>
      <span
        v-if="cellSchedules.length && cell.isCurrentMonth"
        class="text-[9px] font-medium text-gray-400"
      >
        {{ cellSchedules.length }}
        {{ cellSchedules.length === 1 ? "case" : "cases" }}
      </span>
    </div>

    <!-- Schedule cards + add button -->
    <div
      class="flex-1 overflow-y-auto px-1 pb-1 space-y-0.5"
      v-if="cell.isCurrentMonth"
    >
      <!-- Schedule cards -->
      <div
        v-for="schedule in cellSchedules"
        :key="schedule.name"
        class="group rounded-md px-1.5 py-1 text-[10px] leading-tight cursor-pointer transition-all hover:shadow-sm"
        :class="cardClasses(schedule)"
        @click.stop="openViewDialog(schedule)"
        :title="cardTooltip(schedule)"
      >
        <!-- Row 1: time + priority -->
        <div class="flex items-center gap-1">
          <span class="font-semibold" :class="timeColor(schedule)">{{
            formatTime(schedule.start_time)
          }}</span>
          <span
            v-if="schedule.priority !== 'Elective'"
            class="shrink-0 rounded px-1 text-[8px] font-bold uppercase leading-tight"
            :class="{
              'bg-red-500 text-white': schedule.priority === 'Emergency',
              'bg-orange-400 text-white': schedule.priority === 'Urgent',
            }"
            >{{ schedule.priority === "Emergency" ? "EMR" : "URG" }}</span
          >
        </div>
        <!-- Row 2: patient -->
        <div class="truncate font-medium text-gray-800">
          {{ schedule.patient_name }}
        </div>
        <!-- Row 3: procedure -->
        <div class="truncate text-gray-500">
          {{ schedule.procedure_template || "—" }}
        </div>
        <!-- Row 4: theater room -->
        <div class="truncate text-gray-400 text-[9px]">
          {{ getTheaterRoomLabel(schedule.theater_room) }}
        </div>
      </div>

      <!-- Add button -->
      <button
        v-if="!cell.isPast"
        class="flex w-full items-center justify-center rounded-md border border-dashed h-5 mt-0.5 transition-all text-[10px]"
        :class="'border-gray-200 text-gray-300 hover:border-blue-400 hover:bg-blue-50 hover:text-blue-500'"
        @click="handleAddClick"
      >
        <svg
          class="h-2.5 w-2.5"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          stroke-width="3"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M12 4v16m8-8H4"
          />
        </svg>
      </button>
    </div>

    <!-- View/Details Dialog -->
    <Dialog
      :options="{
        title: viewSchedule ? viewSchedule.patient_name : '',
        size: 'xl',
      }"
      v-model="showViewDialog"
      @close="closeViewDialog"
    >
      <template #body-content>
        <div v-if="viewSchedule" class="flex flex-col gap-3">
          <!-- Status + priority badges -->
          <div class="flex items-center gap-2">
            <span
              class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium"
              :class="{
                'bg-blue-100 text-blue-800':
                  viewSchedule.status === 'Scheduled',
                'bg-orange-100 text-orange-800':
                  viewSchedule.status === 'In Progress',
                'bg-green-100 text-green-800':
                  viewSchedule.status === 'Completed',
                'bg-red-100 text-red-800': viewSchedule.status === 'Cancelled',
                'bg-gray-100 text-gray-800':
                  viewSchedule.status === 'Postponed',
              }"
              >{{ viewSchedule.status }}</span
            >
            <span
              v-if="viewSchedule.priority !== 'Elective'"
              class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium"
              :class="{
                'bg-red-100 text-red-700':
                  viewSchedule.priority === 'Emergency',
                'bg-orange-100 text-orange-700':
                  viewSchedule.priority === 'Urgent',
              }"
              >{{ viewSchedule.priority }}</span
            >
          </div>

          <!-- Details grid -->
          <div
            class="grid grid-cols-2 gap-x-6 gap-y-2 rounded-lg bg-gray-50 p-4 text-sm"
          >
            <div>
              <span class="text-gray-500">Patient:</span
              ><span class="ml-1 font-medium text-gray-800">{{
                viewSchedule.patient_name
              }}</span>
            </div>
            <div>
              <span class="text-gray-500">Date:</span
              ><span class="ml-1 font-medium text-gray-800">{{
                viewSchedule.date
              }}</span>
            </div>
            <div>
              <span class="text-gray-500">Procedure:</span
              ><span class="ml-1 font-medium text-gray-800">{{
                viewSchedule.procedure_template
              }}</span>
            </div>
            <div>
              <span class="text-gray-500">Time:</span
              ><span class="ml-1 font-medium text-gray-800">{{
                formatTime(viewSchedule.start_time)
              }}</span>
            </div>
            <div>
              <span class="text-gray-500">Theater:</span
              ><span class="ml-1 font-medium text-gray-800">{{
                getTheaterRoomLabel(viewSchedule.theater_room)
              }}</span>
            </div>
            <div v-if="viewSchedule.estimated_duration">
              <span class="text-gray-500">Duration:</span
              ><span class="ml-1 font-medium text-gray-800">{{
                formatDuration(viewSchedule.estimated_duration)
              }}</span>
            </div>
          </div>

          <!-- Surgical team -->
          <div
            v-if="viewSchedule.team && viewSchedule.team.length"
            class="mt-1"
          >
            <div class="mb-2 text-sm font-medium text-gray-700">
              Surgical Team
            </div>
            <div class="space-y-1">
              <div
                v-for="(member, idx) in sortedTeam"
                :key="idx"
                class="flex items-center rounded bg-gray-50 px-3 py-1.5 text-sm"
              >
                <span class="shrink-0 text-gray-500" style="width: 140px">{{
                  member.role
                }}</span>
                <span class="mx-3 h-4 border-l border-gray-300"></span>
                <span class="font-medium text-gray-800">{{
                  member.practitioner_name
                }}</span>
              </div>
            </div>
          </div>

          <!-- Notes -->
          <div v-if="viewSchedule.notes" class="mt-1 text-sm">
            <span class="text-gray-500">Notes:</span>
            <p class="mt-1 text-gray-700">{{ viewSchedule.notes }}</p>
          </div>

          <!-- Actions -->
          <div
            v-if="!cell.isPast && viewSchedule.status === 'Scheduled'"
            class="border-t pt-3 mt-1"
          >
            <div class="grid grid-cols-2 gap-2">
              <Button
                variant="subtle"
                theme="orange"
                size="sm"
                class="w-full"
                @click="handlePostpone"
              >
                Postpone
              </Button>
              <Button
                variant="subtle"
                theme="red"
                size="sm"
                class="w-full"
                @click="handleRemove"
              >
                Remove
              </Button>
              <Button
                variant="subtle"
                size="sm"
                class="w-full"
                @click="createPreopAssessment"
              >
                Create Preop Assessment
              </Button>
              <Button
                variant="subtle"
                size="sm"
                class="w-full"
                @click="createSurgicalHandover"
              >
                Create Surgical Handover
              </Button>
            </div>
          </div>
        </div>
      </template>
    </Dialog>

    <!-- New Schedule Dialog -->
    <Dialog
      :options="{
        title: 'New Theater Booking',
        size: '2xl',
        actions: newDialogActions,
      }"
      v-model="showNewDialog"
      @close="closeNewDialog"
    >
      <template #body-content>
        <div class="flex flex-col gap-4">
          <!-- Date context -->
          <div
            class="rounded-lg bg-blue-50 px-3 py-2 text-sm font-medium text-blue-800"
          >
            📅 {{ formatDateDisplay(cell.date) }}
          </div>

          <!-- Row 1: Theater Room | Patient | Start Time (3 columns) -->
          <div class="grid grid-cols-3 gap-4">
            <FormControl
              type="autocomplete"
              label="Theater Room *"
              :options="theaterRoomOptions"
              v-model="newForm.theater_room_obj"
              placeholder="Select theater room..."
            />
            <FormControl
              type="autocomplete"
              label="Patient *"
              :options="patientOptions"
              :loading="patientSearchLoading"
              v-model="newForm.patient"
              placeholder="Search patient..."
              @update:query="onPatientSearch"
            />
            <div>
              <label class="mb-1.5 block text-xs text-gray-600"
                >Start Time *</label
              >
              <input
                type="time"
                v-model="newForm.start_time"
                class="w-full rounded-md border border-gray-300 px-2.5 py-1.5 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
              />
            </div>
          </div>

          <!-- Row 2: Procedure | Priority | Duration (3 columns) -->
          <div class="grid grid-cols-3 gap-4">
            <FormControl
              type="autocomplete"
              label="Procedure Template *"
              :options="procedureOptions"
              v-model="newForm.procedure_template"
              placeholder="Search procedure..."
            />
            <FormControl
              type="select"
              label="Priority"
              :options="priorityOptions"
              v-model="newForm.priority"
            />
            <div>
              <label class="mb-1.5 block text-xs text-gray-600"
                >Duration (mins)</label
              >
              <input
                type="number"
                v-model.number="newForm.duration_mins"
                min="0"
                placeholder="120"
                class="w-full rounded-md border border-gray-300 px-2.5 py-1.5 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
              />
            </div>
          </div>

          <!-- Surgical Team -->
          <div>
            <div class="mb-2 flex items-center justify-between">
              <label class="text-xs font-medium text-gray-700"
                >Surgical Team *</label
              >
              <button
                type="button"
                class="rounded-md bg-blue-50 px-2.5 py-0.5 text-xs font-medium text-blue-600 hover:bg-blue-100 transition-colors"
                @click="addTeamMember"
              >
                + Add Member
              </button>
            </div>
            <div class="space-y-2">
              <div
                v-for="(member, idx) in newForm.team"
                :key="idx"
                class="flex items-center gap-2 rounded-md border border-gray-200 bg-gray-50/50 px-2 py-1.5"
              >
                <select
                  v-model="member.role"
                  class="rounded-md border border-gray-300 px-2 py-1 text-sm flex-shrink-0 w-40 bg-white"
                >
                  <option value="">Select Role</option>
                  <option value="Surgeon">Surgeon</option>
                  <option value="Assistant Surgeon">Assistant Surgeon</option>
                  <option value="Anesthetist">Anesthetist</option>
                  <option value="Nurse">Nurse</option>
                </select>
                <FormControl
                  type="autocomplete"
                  class="flex-1"
                  :options="getPractitionerOptions(member.role)"
                  v-model="member.practitioner_obj"
                  placeholder="Search practitioner..."
                />
                <button
                  type="button"
                  class="shrink-0 rounded-md p-1 text-gray-400 hover:bg-red-50 hover:text-red-500 transition-colors"
                  @click="removeTeamMember(idx)"
                  title="Remove"
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
                      d="M6 18L18 6M6 6l12 12"
                    />
                  </svg>
                </button>
              </div>
            </div>
          </div>

          <!-- Notes -->
          <div>
            <label class="mb-1.5 block text-xs text-gray-600">Notes</label>
            <textarea
              v-model="newForm.notes"
              rows="2"
              class="w-full rounded-md border border-gray-300 px-2.5 py-1.5 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
              placeholder="Additional notes..."
            ></textarea>
          </div>
        </div>
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import dayjs from "dayjs";
import { computed, reactive, ref } from "vue";
import { createResource, call } from "frappe-ui";

const props = defineProps({
  cell: { type: Object, required: true },
  cellSchedules: { type: Array, default: () => [] },
  company: { type: String, default: "" },
  theaterRooms: { type: Array, default: () => [] },
  getTheaterRoomLabel: { type: Function, default: (n) => n },
});

const emit = defineEmits(["save", "remove", "postpone"]);

const showViewDialog = ref(false);
const viewSchedule = ref(null);
const showNewDialog = ref(false);

const ROLE_ORDER = {
  Surgeon: 1,
  "Assistant Surgeon": 2,
  Anesthetist: 3,
  Nurse: 4,
};
const sortedTeam = computed(() => {
  if (!viewSchedule.value?.team) return [];
  return [...viewSchedule.value.team].sort(
    (a, b) => (ROLE_ORDER[a.role] || 99) - (ROLE_ORDER[b.role] || 99)
  );
});

// Patient live-search state
const patientOptions = ref([]);
const patientSearchLoading = ref(false);
let _patientSearchTimer = null;

async function fetchPatients(searchText = "") {
  patientSearchLoading.value = true;
  try {
    const results = await call(
      "hms_tz.hms_tz.doctype.ot_schedule.roster.search_patients",
      { search_text: searchText || "", limit: 30 }
    );
    patientOptions.value = (results || []).map((p) => ({
      label: `${(p.patient_name || "").trim()} (${p.name})`,
      value: p.name,
    }));
  } catch (_) {
    patientOptions.value = [];
  } finally {
    patientSearchLoading.value = false;
  }
}

function onPatientSearch(searchText) {
  clearTimeout(_patientSearchTimer);
  _patientSearchTimer = setTimeout(() => {
    fetchPatients(searchText || "");
  }, 300);
}

const procedureList = createResource({
  url: "frappe.client.get_list",
  params: {
    doctype: "Clinical Procedure Template",
    fields: ["name", "template"],
    filters: { disabled: 0 },
    order_by: "template asc",
    limit_page_length: 9999,
  },
});
const doctorList = createResource({
  url: "frappe.client.get_list",
  params: {
    doctype: "Healthcare Practitioner",
    fields: ["name", "practitioner_name"],
    filters: { practitioner_role: "Doctor" },
    order_by: "practitioner_name asc",
    limit_page_length: 9999,
  },
});
const nurseList = createResource({
  url: "frappe.client.get_list",
  params: {
    doctype: "Healthcare Practitioner",
    fields: ["name", "practitioner_name"],
    filters: { practitioner_role: "Nurse" },
    order_by: "practitioner_name asc",
    limit_page_length: 9999,
  },
});

const newForm = reactive({
  theater_room_obj: null,
  patient: null,
  procedure_template: null,
  start_time: "",
  duration_mins: null,
  priority: "Elective",
  notes: "",
  team: [
    { role: "Surgeon", practitioner_obj: null },
    { role: "Assistant Surgeon", practitioner_obj: null },
    { role: "Anesthetist", practitioner_obj: null },
    { role: "Nurse", practitioner_obj: null },
  ],
});

const theaterRoomOptions = computed(() =>
  props.theaterRooms.map((r) => ({
    label: r.healthcare_service_unit_name || r.name,
    value: r.name,
  }))
);
const procedureOptions = computed(() =>
  (procedureList.data || []).map((p) => ({
    label: p.template || p.name,
    value: p.name,
  }))
);
function getPractitionerOptions(role) {
  const list = role === "Nurse" ? nurseList : doctorList;
  return (list.data || []).map((p) => ({
    label: p.practitioner_name,
    value: p.name,
  }));
}

const priorityOptions = [
  { label: "Elective", value: "Elective" },
  { label: "Urgent", value: "Urgent" },
  { label: "Emergency", value: "Emergency" },
];

const isNewFormValid = computed(() => {
  return (
    !!newForm.theater_room_obj?.value &&
    !!newForm.patient?.value &&
    !!newForm.procedure_template?.value &&
    !!newForm.start_time &&
    newForm.team.some((m) => m.role && m.practitioner_obj?.value)
  );
});

const newDialogActions = computed(() => [
  { label: "Cancel", variant: "subtle", onClick: () => closeNewDialog() },
  {
    label: "Book Theater",
    variant: "solid",
    disabled: !isNewFormValid.value,
    onClick: () => submitNewSchedule(),
  },
]);

function formatTime(t) {
  return t ? String(t).slice(0, 5) : "";
}

function formatDuration(seconds) {
  const num = typeof seconds === "string" ? parseInt(seconds, 10) : seconds;
  if (!num || isNaN(num)) return "";
  const h = Math.floor(num / 3600),
    m = Math.floor((num % 3600) / 60);
  return h > 0 ? `${h}h ${m}m` : `${m}m`;
}

function formatDateDisplay(dateStr) {
  return dayjs(dateStr).format("dddd, DD MMMM YYYY");
}

function cardClasses(s) {
  if (s.status === "Cancelled")
    return "border-l-2 border-l-red-400 bg-red-50/60 line-through opacity-60";
  if (s.status === "Completed")
    return "border-l-2 border-l-green-500 bg-green-50/60";
  if (s.status === "In Progress")
    return "border-l-2 border-l-orange-400 bg-orange-50/60";
  if (s.status === "Postponed")
    return "border-l-2 border-l-gray-400 bg-gray-100/60 opacity-60";
  return "border-l-2 border-l-blue-500 bg-blue-50/50 hover:bg-blue-100/60";
}

function timeColor(s) {
  if (s.status === "Cancelled") return "text-red-500";
  if (s.status === "Completed") return "text-green-600";
  if (s.status === "In Progress") return "text-orange-600";
  return "text-blue-600";
}

function cardTooltip(s) {
  return `${s.patient_name}\n${formatTime(s.start_time)} · ${
    s.procedure_template || ""
  }\n${props.getTheaterRoomLabel(s.theater_room)}`;
}

function handleAddClick() {
  if (props.cell.isPast) return;
  // Fetch an initial patient list for the dialog
  fetchPatients("");
  if (!procedureList.data) procedureList.submit();
  if (!doctorList.data) doctorList.submit();
  if (!nurseList.data) nurseList.submit();
  resetNewForm();
  showNewDialog.value = true;
}

function openViewDialog(schedule) {
  viewSchedule.value = schedule;
  showViewDialog.value = true;
}
function closeViewDialog() {
  showViewDialog.value = false;
  viewSchedule.value = null;
}
function closeNewDialog() {
  showNewDialog.value = false;
}

function resetNewForm() {
  newForm.theater_room_obj = null;
  newForm.patient = null;
  newForm.procedure_template = null;
  newForm.start_time = "";
  newForm.duration_mins = null;
  newForm.priority = "Elective";
  newForm.notes = "";
  newForm.team = [
    { role: "Surgeon", practitioner_obj: null },
    { role: "Assistant Surgeon", practitioner_obj: null },
    { role: "Anesthetist", practitioner_obj: null },
    { role: "Nurse", practitioner_obj: null },
  ];
}

function addTeamMember() {
  newForm.team.push({ role: "", practitioner_obj: null });
}
function removeTeamMember(idx) {
  newForm.team.splice(idx, 1);
}

function submitNewSchedule() {
  if (!isNewFormValid.value) return;
  const teamData = newForm.team
    .filter((m) => m.role && m.practitioner_obj?.value)
    .map((m) => ({ role: m.role, practitioner: m.practitioner_obj.value }));
  emit("save", {
    patient: newForm.patient.value,
    procedure_template: newForm.procedure_template.value,
    theater_room: newForm.theater_room_obj.value,
    date: props.cell.date,
    start_time: newForm.start_time,
    estimated_duration: newForm.duration_mins
      ? newForm.duration_mins * 60
      : null,
    priority: newForm.priority,
    notes: newForm.notes,
    company: props.company,
    team: teamData,
  });
  showNewDialog.value = false;
}

function handleRemove() {
  if (viewSchedule.value) {
    emit("remove", viewSchedule.value.name);
    closeViewDialog();
  }
}
function handlePostpone() {
  if (viewSchedule.value) {
    emit("postpone", viewSchedule.value.name);
    closeViewDialog();
  }
}
function createPreopAssessment() {
  if (!viewSchedule.value) return;
  const s = viewSchedule.value;
  window.open(
    `/app/preoperative-assessment/new?ot_schedule=${s.name}&patient=${
      s.patient
    }&company=${props.company || ""}`,
    "_blank"
  );
}
function createSurgicalHandover() {
  if (!viewSchedule.value) return;
  const s = viewSchedule.value;
  window.open(
    `/app/surgical-handover/new?patient=${s.patient}&company=${
      props.company || ""
    }`,
    "_blank"
  );
}
</script>
