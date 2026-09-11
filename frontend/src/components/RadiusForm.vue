<script setup>
import { ref } from "vue";
import AddressAutocomplete from "./AddressAutocomplete.vue";

const emit = defineEmits(["submit"]);
defineProps({ loading: { type: Boolean, default: false } });

const address = ref("");
const radiusKm = ref(3);
const requireAc = ref(false);
const requireDc = ref(false);
const trailerFriendly = ref(false);
const connectorType = ref("");
const minPowerKw = ref(null);

function submit() {
  if (!address.value) return;
  emit("submit", {
    address: address.value,
    radius_km: radiusKm.value,
    require_ac: requireAc.value,
    require_dc: requireDc.value,
    trailer_friendly: trailerFriendly.value,
    connector_type: connectorType.value || null,
    min_power_kw: minPowerKw.value || null,
  });
}
</script>

<template>
  <form class="form" @submit.prevent="submit">
    <label class="field">
      <span>Address or zip code</span>
      <AddressAutocomplete v-model="address" placeholder="e.g. 10115 Berlin" />
    </label>

    <label class="field">
      <span>Search radius</span>
      <input v-model.number="radiusKm" type="range" min="1" max="5" step="0.5" />
      <span class="field__value">{{ radiusKm }} km</span>
    </label>

    <div class="toggle-group">
      <label class="checkbox">
        <input v-model="requireAc" type="checkbox" />
        <span>AC (11–22 kW, overnight street parking)</span>
      </label>
      <label class="checkbox">
        <input v-model="requireDc" type="checkbox" />
        <span>DC fast charging</span>
      </label>
      <label class="checkbox">
        <input v-model="trailerFriendly" type="checkbox" />
        <span>Trailer / Caravan friendly (Drive-Through)</span>
      </label>
    </div>

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

    <button type="submit" class="primary-btn" :disabled="loading">
      {{ loading ? "Scanning…" : "Scan Neighborhood" }}
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
.toggle-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.checkbox {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.85rem;
  color: #333;
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
