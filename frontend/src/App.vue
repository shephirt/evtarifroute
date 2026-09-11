<script setup>
import { computed, ref } from "vue";
import ModeSwitch from "./components/ModeSwitch.vue";
import RouteForm from "./components/RouteForm.vue";
import RadiusForm from "./components/RadiusForm.vue";
import ResultsPanel from "./components/ResultsPanel.vue";
import MapView from "./components/MapView.vue";
import { radiusAnalysis, routeAnalysis, tariffRecommendation } from "./api.js";

const mode = ref("route"); // 'route' | 'radius'
const loading = ref(false);
const error = ref(null);

const rankings = ref([]);
const stations = ref([]);
const totalStations = ref(0);
const routeGeojson = ref(null);
const radiusCenter = ref(null);
const radiusKm = ref(null);

const tariffs = ref([]);
const tariffsLoading = ref(false);

const hoveredOperatorId = ref(null);
const hoveredTariffOperatorIds = ref(null);
const selectedOperatorId = ref(null);

// When a CPO is clicked in the ranking list, isolate the map to only that
// operator's stations. Click again (or run a new search) to clear it.
const visibleStations = computed(() => {
  if (selectedOperatorId.value === null) return stations.value;
  return stations.value.filter((s) => s.operator_id === selectedOperatorId.value);
});

function toggleSelectedOperator(operatorId) {
  selectedOperatorId.value = selectedOperatorId.value === operatorId ? null : operatorId;
}

function resetResults() {
  rankings.value = [];
  stations.value = [];
  totalStations.value = 0;
  routeGeojson.value = null;
  radiusCenter.value = null;
  radiusKm.value = null;
  tariffs.value = [];
  selectedOperatorId.value = null;
}

async function loadTariffs() {
  if (!rankings.value.length) {
    tariffs.value = [];
    return;
  }
  tariffsLoading.value = true;
  try {
    const res = await tariffRecommendation({ rankings: rankings.value });
    tariffs.value = res.recommendations;
  } catch (e) {
    // Non-fatal: tariff recommendations are a bonus on top of the core
    // dominance analysis, don't block the whole results view on failure.
    console.error("Tariff recommendation failed:", e);
  } finally {
    tariffsLoading.value = false;
  }
}

async function handleRouteSubmit(payload) {
  loading.value = true;
  error.value = null;
  resetResults();
  try {
    const res = await routeAnalysis(payload);
    rankings.value = res.rankings;
    stations.value = res.stations;
    totalStations.value = res.total_stations;
    routeGeojson.value = res.route_geojson;
    await loadTariffs();
  } catch (e) {
    error.value = e.message;
  } finally {
    loading.value = false;
  }
}

async function handleRadiusSubmit(payload) {
  loading.value = true;
  error.value = null;
  resetResults();
  try {
    const res = await radiusAnalysis(payload);
    rankings.value = res.rankings;
    stations.value = res.stations;
    totalStations.value = res.total_stations;
    radiusCenter.value = res.location;
    radiusKm.value = res.radius_km;
    await loadTariffs();
  } catch (e) {
    error.value = e.message;
  } finally {
    loading.value = false;
  }
}

function onModeChange(newMode) {
  mode.value = newMode;
  error.value = null;
  resetResults();
}
</script>

<template>
  <div class="app">
    <div class="panel">
      <div class="panel__header">
        <h1>EVTarifRoute</h1>
        <ModeSwitch :model-value="mode" @update:model-value="onModeChange" />
      </div>

      <div class="panel__body">
        <!-- v-show (not v-if) so switching tabs doesn't unmount the form and
             lose whatever the user already typed in the other tab. -->
        <RouteForm v-show="mode === 'route'" :loading="loading" @submit="handleRouteSubmit" />
        <RadiusForm v-show="mode === 'radius'" :loading="loading" @submit="handleRadiusSubmit" />

        <p v-if="error" class="error">{{ error }}</p>

        <ResultsPanel
          v-if="rankings.length"
          :rankings="rankings"
          :total-stations="totalStations"
          :tariffs="tariffs"
          :tariffs-loading="tariffsLoading"
          :selected-operator-id="selectedOperatorId"
          @hover-operator="(id) => (hoveredOperatorId = id)"
          @hover-tariff="(ids) => (hoveredTariffOperatorIds = ids)"
          @select-operator="toggleSelectedOperator"
        />
      </div>
    </div>

    <div class="map-container">
      <MapView
        :stations="visibleStations"
        :route-geojson="routeGeojson"
        :center="radiusCenter"
        :radius-km="radiusKm"
        :highlight-operator-id="hoveredOperatorId"
        :highlight-operator-ids="hoveredTariffOperatorIds"
      />
    </div>
  </div>
</template>

<style>
* {
  box-sizing: border-box;
}
html,
body,
#app {
  margin: 0;
  height: 100%;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}
</style>

<style scoped>
.app {
  position: relative;
  width: 100vw;
  height: 100vh;
  overflow: hidden;
}
.map-container {
  position: absolute;
  inset: 0;
}
.panel {
  position: absolute;
  top: 16px;
  left: 16px;
  bottom: 16px;
  width: 340px;
  z-index: 1000;
  background: white;
  border-radius: 14px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.15);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.panel__header {
  padding: 16px 16px 8px;
  border-bottom: 1px solid #eee;
}
.panel__header h1 {
  font-size: 1.1rem;
  margin: 0 0 12px;
}
.panel__body {
  padding: 16px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.error {
  color: #d32f2f;
  font-size: 0.85rem;
  background: #fdecea;
  border-radius: 8px;
  padding: 8px 10px;
  margin: 0;
}
</style>
