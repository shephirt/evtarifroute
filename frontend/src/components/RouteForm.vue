<script setup>
import { ref } from "vue";
import AddressAutocomplete from "./AddressAutocomplete.vue";

const emit = defineEmits(["submit"]);
defineProps({ loading: { type: Boolean, default: false } });

const startAddress = ref("");
const destinationAddress = ref("");
const trailerFriendly = ref(false);
const showVehicleSettings = ref(false);
const consumptionKwh100km = ref(18);
const arrivalBufferPercent = ref(10);
const bufferKm = ref(2);
const targetSpacingKm = ref(100);
const connectorType = ref("");
const minPowerKw = ref(null);

function submit() {
  if (!startAddress.value || !destinationAddress.value) return;
  emit("submit", {
    start_address: startAddress.value,
    destination_address: destinationAddress.value,
    buffer_km: bufferKm.value,
    trailer_friendly: trailerFriendly.value,
    connector_type: connectorType.value || null,
    min_power_kw: minPowerKw.value || null,
    target_spacing_km: targetSpacingKm.value,
  });
}
</script>

<template>
  <form class="form" @submit.prevent="submit">
    <label class="field">
      <span>Start location</span>
      <AddressAutocomplete v-model="startAddress" placeholder="e.g. Berlin, Germany" />
    </label>

    <label class="field">
      <span>Destination</span>
      <AddressAutocomplete v-model="destinationAddress" placeholder="e.g. Munich, Germany" />
    </label>

    <label class="field">
      <span>Route buffer (km)</span>
      <input v-model.number="bufferKm" type="range" min="1" max="10" step="0.5" />
      <span class="field__value">{{ bufferKm }} km</span>
    </label>

    <label class="field">
      <span>Desired charger spacing (km)</span>
      <input v-model.number="targetSpacingKm" type="range" min="20" max="300" step="10" />
      <span class="field__value">
        every ~{{ targetSpacingKm }} km (stations closer than
        {{ targetSpacingKm / 2 }} km apart count as one)
      </span>
    </label>

    <label class="checkbox">
      <input v-model="trailerFriendly" type="checkbox" />
      <span>Trailer / Caravan friendly (Drive-Through)</span>
    </label>

    <label class="field">
      <span>Socket / connector type</span>
      <select v-model="connectorType">
        <option value="">Any</option>
        <option value="Type 2">Type 2</option>
        <option value="CCS">CCS</option>
        <option value="CHAdeMO">CHAdeMO</option>
        <option value="Schuko">Schuko</option>
        <option value="Tesla">Tesla</option>
      </select>
    </label>

    <label class="field">
      <span>Minimum power (kW)</span>
      <input v-model.number="minPowerKw" type="number" min="0" step="1" placeholder="e.g. 50" />
    </label>

    <button
      type="button"
      class="accordion-toggle"
      @click="showVehicleSettings = !showVehicleSettings"
    >
      {{ showVehicleSettings ? "▾" : "▸" }} Vehicle settings
    </button>
    <div v-if="showVehicleSettings" class="accordion-content">
      <label class="field">
        <span>Expected consumption (kWh/100km)</span>
        <input v-model.number="consumptionKwh100km" type="number" min="5" max="60" step="0.5" />
      </label>
      <label class="field">
        <span>Arrival buffer (%)</span>
        <input v-model.number="arrivalBufferPercent" type="number" min="0" max="50" step="5" />
      </label>
      <p class="hint">
        Vehicle settings are informational for now — the analysis is based purely on
        CPO density along the route, not battery simulation (see SRS).
      </p>
    </div>

    <button type="submit" class="primary-btn" :disabled="loading">
      {{ loading ? "Analyzing…" : "Analyze Route" }}
    </button>
  </form>
</template>

<style scoped>
.form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.field {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 0.8rem;
  color: #444;
  font-weight: 600;
}
.field input[type="text"],
.field input[type="number"],
.field select {
  font-weight: 400;
  padding: 8px 10px;
  border: 1px solid #d5d8dc;
  border-radius: 8px;
  font-size: 0.9rem;
}
.field__value {
  font-weight: 400;
  color: #666;
  font-size: 0.8rem;
}
.checkbox {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.85rem;
  color: #333;
}
.accordion-toggle {
  background: none;
  border: none;
  text-align: left;
  padding: 4px 0;
  font-size: 0.85rem;
  font-weight: 600;
  color: #1a73e8;
  cursor: pointer;
}
.accordion-content {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 8px 10px;
  background: #f7f8f9;
  border-radius: 8px;
}
.hint {
  font-size: 0.75rem;
  color: #888;
  margin: 0;
}
.primary-btn {
  margin-top: 4px;
  background: #1a73e8;
  color: white;
  border: none;
  border-radius: 8px;
  padding: 10px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
}
.primary-btn:disabled {
  opacity: 0.6;
  cursor: default;
}
</style>
