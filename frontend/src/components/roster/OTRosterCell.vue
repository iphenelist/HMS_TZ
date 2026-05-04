<template>
  <td
    class="relative border border-dashed border-gray-400 rounded-lg px-1 py-1 text-center align-top"
    :class="cellClasses"
  >
    <!-- Schedule cards -->
    <div
      class="flex flex-col gap-1 max-h-[160px] overflow-y-auto"
      v-if="cellSchedules.length"
    >
      <div
        v-for="schedule in cellSchedules"
        :key="schedule.name"
        class="flex flex-col rounded border px-1.5 py-1 text-xs cursor-pointer transition-colors"
        :class="cardClasses(schedule)"
        @click.stop="openViewDialog(schedule)"
        :title="`${schedule.patient_name} · ${formatTime(
          schedule.start_time
        )} · ${schedule.procedure_template}`"
      >
        <div class="flex items-center gap-1">
          <span class="truncate font-medium flex-1 text-left">
            {{ schedule.patient_name }}
          </span>
          <span class="shrink-0 text-blue-700 font-medium">{{
            formatTime(schedule.start_time)
          }}</span>
          <span
            v-if="schedule.priority !== 'Elective'"
            class="shrink-0 rounded-full px-1 text-[10px] font-semibold"
            :class="{
              'bg-red-100 text-red-700': schedule.priority === 'Emergency',
              'bg-orange-100 text-orange-700': schedule.priority === 'Urgent',
            }"
          >
            {{ schedule.priority === "Emergency" ? "!" : "U" }}
          </span>
        </div>
        <span class="truncate text-[10px] text-gray-500 text-left">{{
          schedule.procedure_template
        }}</span>
      </div>
    </div>

    <!-- Add button (only for future/today dates) -->
    <div
      class="flex items-center justify-center rounded border border-dashed transition-colors"
      :class="[
        cellSchedules.length ? 'h-6 mt-1' : 'h-8',
        isPastDate
          ? 'border-gray-100 text-gray-200'
          : 'border-gray-200 text-gray-400 hover:border-blue-400 hover:bg-blue-50/50 hover:text-blue-500 cursor-pointer',
      ]"
      @click="handleAddClick"
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
    </div>

    <!-- View/Edit/Cancel Dialog -->
    <Dialog
      :options="{
        title: viewSchedule ? `${viewSchedule.patient_name}` : '',
        size: 'xl',
      }"
      v-model="showViewDialog"
      @close="closeViewDialog"
    >
      <template #body-content>
        <div v-if="viewSchedule" class="flex flex-col gap-3">
          <!-- Status badge -->
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
            >
              {{ viewSchedule.status }}
            </span>
            <span
              v-if="viewSchedule.priority !== 'Elective'"
              class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium"
              :class="{
                'bg-red-100 text-red-700':
                  viewSchedule.priority === 'Emergency',
                'bg-orange-100 text-orange-700':
                  viewSchedule.priority === 'Urgent',
              }"
            >
              {{ viewSchedule.priority }}
            </span>
          </div>

          <!-- Schedule details -->
          <div
            class="grid grid-cols-2 gap-3 rounded-lg bg-gray-50 p-3 text-sm"
          >
            <div>
              <span class="text-gray-500">Patient:</span>
              <span class="ml-1 font-medium text-gray-800">{{
                viewSchedule.patient_name
              }}</span>
            </div>
            <div>
              <span class="text-gray-500">Date:</span>
              <span class="ml-1 font-medium text-gray-800">{{
                viewSchedule.date
              }}</span>
            </div>
            <div>
              <span class="text-gray-500">Procedure:</span>
              <span class="ml-1 font-medium text-gray-800">{{
                viewSchedule.procedure_template
              }}</span>
            </div>
            <div>
              <span class="text-gray-500">Time:</span>
              <span class="ml-1 font-medium text-gray-800">{{
                formatTime(viewSchedule.start_time)
              }}</span>
            </div>
            <div>
              <span class="text-gray-500">Theater:</span>
              <span class="ml-1 font-medium text-gray-800">{{
                viewSchedule.theater_room
              }}</span>
            </div>
            <div v-if="viewSchedule.estimated_duration">
              <span class="text-gray-500">Duration:</span>
              <span class="ml-1 font-medium text-gray-800">{{
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
                :key="`${member.practitioner}-${idx}`"
                class="flex items-center rounded bg-gray-50 px-3 py-1.5 text-sm"
              >
                <span
                  class="shrink-0 text-gray-500"
                  style="width: 140px; min-width: 140px"
                  >{{ member.role }}</span
                >
                <span class="mx-3 h-4 border-l border-gray-300 w-24"></span>
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

          <!-- Action buttons -->
          <div
            v-if="!isPastDate && viewSchedule.status === 'Scheduled'"
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
                <template #prefix>
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
                      d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                  </svg>
                </template>
                Postpone
              </Button>
              <Button
                variant="subtle"
                theme="red"
                size="sm"
                class="w-full"
                @click="handleRemove"
              >
                <template #prefix>
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
                      d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                    />
                  </svg>
                </template>
                Remove
              </Button>
              <Button
                variant="subtle"
                size="sm"
                class="w-full"
                @click="createPreopAssessment"
              >
                <template #prefix>
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
                      d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"
                    />
                  </svg>
                </template>
                Create Preop Assessment
              </Button>
              <Button
                variant="subtle"
                size="sm"
                class="w-full"
                @click="createSurgicalHandover"
              >
                <template #prefix>
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
                      d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4"
                    />
                  </svg>
                </template>
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
        size: 'xl',
        actions: newDialogActions,
      }"
      v-model="showNewDialog"
      @close="closeNewDialog"
    >
      <template #body-content>
        <div class="flex flex-col gap-4">
          <!-- Context info -->
          <div class="flex items-center gap-3 rounded-lg bg-gray-50 px-3 py-2">
            <div class="text-sm">
              <span class="text-gray-500">Theater:</span>
              <span class="ml-1 font-medium text-gray-800">{{
                theaterRoom
              }}</span>
            </div>
            <div class="text-sm">
              <span class="text-gray-500">Date:</span>
              <span class="ml-1 font-medium text-gray-800">{{ date }}</span>
            </div>
          </div>

          <!-- Patient -->
          <FormControl
            type="autocomplete"
            label="Patient *"
            :options="patientOptions"
            v-model="newForm.patient"
            placeholder="Search patient..."
          />

          <!-- Procedure Template -->
          <FormControl
            type="autocomplete"
            label="Procedure Template *"
            :options="procedureOptions"
            v-model="newForm.procedure_template"
            placeholder="Search procedure..."
          />

          <div class="grid grid-cols-3 gap-4">
            <!-- Start Time -->
            <div>
              <label class="mb-1.5 block text-xs text-gray-600"
                >Start Time *</label
              >
              <input
                type="time"
                v-model="newForm.start_time"
                class="w-full rounded border border-gray-300 px-2.5 py-1.5 text-sm focus:border-blue-400 focus:ring-1 focus:ring-blue-400"
              />
            </div>

            <!-- Duration -->
            <div>
              <label class="mb-1.5 block text-xs text-gray-600"
                >Duration (mins)</label
              >
              <input
                type="number"
                v-model.number="newForm.duration_mins"
                min="0"
                placeholder="120"
                class="w-full rounded border border-gray-300 px-2.5 py-1.5 text-sm focus:border-blue-400 focus:ring-1 focus:ring-blue-400"
              />
            </div>

            <!-- Priority -->
            <FormControl
              type="select"
              label="Priority"
              :options="priorityOptions"
              v-model="newForm.priority"
            />
          </div>

          <!-- Surgical Team -->
          <div>
            <div class="mb-2 flex items-center justify-between">
              <label class="text-xs font-medium text-gray-700"
                >Surgical Team *</label
              >
              <button
                type="button"
                class="rounded bg-blue-50 px-2 py-0.5 text-xs text-blue-600 hover:bg-blue-100"
                @click="addTeamMember"
              >
                + Add Member
              </button>
            </div>
            <div class="space-y-2">
              <div
                v-for="(member, idx) in newForm.team"
                :key="idx"
                class="flex items-center gap-2 rounded border border-gray-200 bg-gray-50 px-2 py-1.5"
              >
                <select
                  v-model="member.role"
                  class="rounded border border-gray-300 px-2 py-1 text-sm flex-shrink-0 w-40"
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
                  class="shrink-0 rounded p-1 text-gray-400 hover:bg-red-50 hover:text-red-500"
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
              class="w-full rounded border border-gray-300 px-2.5 py-1.5 text-sm focus:border-blue-400 focus:ring-1 focus:ring-blue-400"
              placeholder="Additional notes..."
            ></textarea>
          </div>
        </div>
      </template>
    </Dialog>
  </td>
</template>

<script setup>
import { computed, reactive, ref } from "vue";
import { createResource } from "frappe-ui";

const props = defineProps({
  theaterRoom: { type: String, required: true },
  date: { type: String, required: true },
  isWeekend: { type: Boolean, default: false },
  isPastDate: { type: Boolean, default: false },
  cellSchedules: { type: Array, default: () => [] },
  company: { type: String, default: "" },
});

const emit = defineEmits(["save", "remove", "postpone"]);

const showViewDialog = ref(false);
const viewSchedule = ref(null);
const showNewDialog = ref(false);

// Role sort order for surgical team display
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

// Lists for autocomplete
const patientList = createResource({
  url: "frappe.client.get_list",
  params: {
    doctype: "Patient",
    fields: ["name", "patient_name"],
    filters: { status: "Active" },
    order_by: "patient_name asc",
    limit_page_length: 9999,
  },
});

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

// New form state
const newForm = reactive({
  patient: null,
  procedure_template: null,
  start_time: "",
  duration_mins: null,
  priority: "Elective",
  notes: "",
  team: [
    { role: "Surgeon", practitioner_obj: null },
    { role: "Anesthetist", practitioner_obj: null },
    { role: "Nurse", practitioner_obj: null },
  ],
});

const patientOptions = computed(() =>
  (patientList.data || []).map((p) => ({
    label: `${p.patient_name} (${p.name})`,
    value: p.name,
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
  const hasPatient = !!newForm.patient?.value;
  const hasProcedure = !!newForm.procedure_template?.value;
  const hasTime = !!newForm.start_time;
  const hasTeam = newForm.team.some(
    (m) => m.role && m.practitioner_obj?.value
  );
  return hasPatient && hasProcedure && hasTime && hasTeam;
});

const newDialogActions = computed(() => [
  {
    label: "Cancel",
    variant: "subtle",
    onClick: () => closeNewDialog(),
  },
  {
    label: "Book Theater",
    variant: "solid",
    disabled: !isNewFormValid.value,
    onClick: () => submitNewSchedule(),
  },
]);

function formatTime(timeStr) {
  if (!timeStr) return "";
  // "HH:mm:ss" -> "HH:mm"
  return String(timeStr).slice(0, 5);
}

function formatDuration(seconds) {
  if (!seconds) return "";
  const num = typeof seconds === "string" ? parseInt(seconds, 10) : seconds;
  if (isNaN(num)) return "";
  const h = Math.floor(num / 3600);
  const m = Math.floor((num % 3600) / 60);
  if (h > 0) return `${h}h ${m}m`;
  return `${m}m`;
}

function cardClasses(schedule) {
  const base = "border-gray-200 bg-white hover:bg-gray-50";
  if (schedule.status === "Cancelled")
    return "border-red-200 bg-red-50/50 line-through opacity-60";
  if (schedule.status === "Completed")
    return "border-green-200 bg-green-50/50";
  if (schedule.status === "In Progress")
    return "border-orange-200 bg-orange-50/50";
  return base;
}

const cellClasses = computed(() => ({
  "bg-orange-50/50": props.isWeekend,
}));

function handleAddClick() {
  if (props.isPastDate) return;
  // Load lists on first open
  if (!patientList.data) patientList.submit();
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
    .map((m) => ({
      role: m.role,
      practitioner: m.practitioner_obj.value,
    }));

  const durationSeconds = newForm.duration_mins
    ? newForm.duration_mins * 60
    : null;

  emit("save", {
    patient: newForm.patient.value,
    procedure_template: newForm.procedure_template.value,
    theater_room: props.theaterRoom,
    date: props.date,
    start_time: newForm.start_time,
    estimated_duration: durationSeconds,
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
    showViewDialog.value = false;
    viewSchedule.value = null;
  }
}

function handlePostpone() {
  if (viewSchedule.value) {
    emit("postpone", viewSchedule.value.name);
    showViewDialog.value = false;
    viewSchedule.value = null;
  }
}

function createPreopAssessment() {
  if (!viewSchedule.value) return;
  const s = viewSchedule.value;
  const params = new URLSearchParams({
    ot_schedule: s.name,
    patient: s.patient,
    company: props.company || "",
  });
  window.open(
    `/app/preoperative-assessment/new?${params.toString()}`,
    "_blank"
  );
}

function createSurgicalHandover() {
  if (!viewSchedule.value) return;
  const s = viewSchedule.value;
  const params = new URLSearchParams({
    patient: s.patient,
    company: props.company || "",
  });
  window.open(`/app/surgical-handover/new?${params.toString()}`, "_blank");
}
</script>
