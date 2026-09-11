<script setup>
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { onMounted, onBeforeUnmount, ref, watch } from "vue";

const props = defineProps({
  stations: { type: Array, default: () => [] },
  routeGeojson: { type: Object, default: null },
  center: { type: Object, default: null }, // {latitude, longitude}
  radiusKm: { type: Number, default: null },
  highlightOperatorId: { type: [Number, String, null], default: null },
  highlightOperatorIds: { type: Array, default: null },
});

const mapEl = ref(null);
let map = null;
let stationLayer = null;
let routeLayer = null;
let radiusLayer = null;

const DEFAULT_CENTER = [51.1657, 10.4515]; // roughly center of Germany
const DEFAULT_ZOOM = 6;

// Muted, mid-tone categorical palette (HSL, fixed saturation/lightness) —
// avoids overly bright/neon hues while still giving enough distinct colors
// for a large, unbounded number of operators. Hue is hashed from the
// operator ID so the same operator always gets the same color.
const PALETTE_SATURATION = 65;
const PALETTE_LIGHTNESS = 42;
const HUE_STEP = 47; // co-prime-ish step so consecutive IDs don't land on similar hues

function colorForOperator(operatorId) {
  if (operatorId === null || operatorId === undefined) return "#6b7280"; // neutral gray
  const hue = (Math.abs(Number(operatorId)) * HUE_STEP) % 360;
  return `hsl(${hue}, ${PALETTE_SATURATION}%, ${PALETTE_LIGHTNESS}%)`;
}

function isHighlighted(operatorId) {
  if (props.highlightOperatorId !== null && props.highlightOperatorId !== undefined) {
    return operatorId === props.highlightOperatorId;
  }
  if (props.highlightOperatorIds) {
    return props.highlightOperatorIds.includes(operatorId);
  }
  return true; // no active highlight filter -> show all at full opacity
}

function anyActiveHighlight() {
  return (
    (props.highlightOperatorId !== null && props.highlightOperatorId !== undefined) ||
    (props.highlightOperatorIds !== null && props.highlightOperatorIds !== undefined)
  );
}

function popupContent(s) {
  const rows = [];
  rows.push(`<strong>${s.station_name || "Unnamed station"}</strong>`);
  rows.push(`Operator: ${s.operator_name}`);
  if (s.max_power_kw != null) rows.push(`Max power: ${s.max_power_kw} kW`);
  if (s.number_of_points != null) rows.push(`Charging spots: ${s.number_of_points}`);
  if (s.connector_types && s.connector_types.length) {
    rows.push(`Connectors: ${s.connector_types.join(", ")}`);
  }
  return `<div class="station-popup">${rows.join("<br>")}</div>`;
}

function renderStations() {
  if (!map) return;
  if (stationLayer) {
    map.removeLayer(stationLayer);
  }
  stationLayer = L.layerGroup();

  const dimAll = anyActiveHighlight();

  for (const s of props.stations) {
    const highlighted = isHighlighted(s.operator_id);
    const marker = L.circleMarker([s.latitude, s.longitude], {
      radius: highlighted ? 9 : 7,
      color: "#ffffff", // white outline for contrast against any map background
      weight: 2,
      fillColor: colorForOperator(s.operator_id),
      fillOpacity: dimAll && !highlighted ? 0.2 : 0.95,
      opacity: dimAll && !highlighted ? 0.2 : 1,
      // Larger invisible padding around the marker to make it easier to
      // click precisely, without visually enlarging the dot itself.
      bubblingMouseEvents: false,
    });
    // Click to see full metadata (operator, power, connectors, spot count);
    // hover tooltip stays as a lightweight preview.
    marker.bindTooltip(`${s.operator_name}${s.station_name ? " — " + s.station_name : ""}`);
    marker.bindPopup(popupContent(s));
    marker.addTo(stationLayer);
  }

  stationLayer.addTo(map);
}

function renderRoute() {
  if (!map) return;
  if (routeLayer) {
    map.removeLayer(routeLayer);
    routeLayer = null;
  }
  if (!props.routeGeojson) return;

  routeLayer = L.geoJSON(props.routeGeojson, {
    style: { color: "#1a73e8", weight: 4, opacity: 0.7 },
  }).addTo(map);

  const bounds = routeLayer.getBounds();
  if (bounds.isValid()) {
    map.fitBounds(bounds, { padding: [30, 30] });
  }
}

function renderRadius() {
  if (!map) return;
  if (radiusLayer) {
    map.removeLayer(radiusLayer);
    radiusLayer = null;
  }
  if (!props.center || !props.radiusKm) return;

  radiusLayer = L.circle([props.center.latitude, props.center.longitude], {
    radius: props.radiusKm * 1000,
    color: "#1a73e8",
    fillColor: "#1a73e8",
    fillOpacity: 0.08,
    weight: 2,
  }).addTo(map);

  map.fitBounds(radiusLayer.getBounds(), { padding: [30, 30] });
}

onMounted(() => {
  // Zoom control default position (topleft) overlaps with the floating
  // panel, which also lives in the top-left. Move it to topright instead.
  map = L.map(mapEl.value, { zoomControl: false }).setView(DEFAULT_CENTER, DEFAULT_ZOOM);
  L.control.zoom({ position: "topright" }).addTo(map);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "&copy; OpenStreetMap contributors",
    maxZoom: 19,
  }).addTo(map);

  renderStations();
  renderRoute();
  renderRadius();
});

onBeforeUnmount(() => {
  if (map) map.remove();
});

watch(() => props.stations, renderStations, { deep: false });
watch(() => props.routeGeojson, renderRoute);
watch(() => [props.center, props.radiusKm], renderRadius);
watch(() => [props.highlightOperatorId, props.highlightOperatorIds], renderStations);
</script>

<template>
  <div ref="mapEl" class="map-view"></div>
</template>

<style scoped>
.map-view {
  width: 100%;
  height: 100%;
}
</style>

<style>
.station-popup {
  font-size: 0.85rem;
  line-height: 1.5;
}
</style>
