<script setup>
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import "leaflet.markercluster";
import "leaflet.markercluster/dist/MarkerCluster.css";
import "leaflet.markercluster/dist/MarkerCluster.Default.css";
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
let stationCluster = null;
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

// A pin-shaped marker (not a plain circle) — much more visible on a map at
// a glance, and the pointed tip gives an unambiguous location anchor.
function pinIcon(operatorId, highlighted, dimmed) {
  const size = highlighted ? 30 : 26;
  const opacity = dimmed ? 0.25 : 1;
  return L.divIcon({
    className: "station-pin-wrapper",
    html: `<div class="station-pin" style="
        width:${size}px;height:${size}px;
        background:${colorForOperator(operatorId)};
        opacity:${opacity};
      "></div>`,
    iconSize: [size, size],
    // Anchor at the bottom point of the pin (the pin shape's "tip" sits at
    // the bottom-center after the CSS rotation, see style below).
    iconAnchor: [size / 2, size],
    popupAnchor: [0, -size],
  });
}

// Cluster icon: shows the total charger count in the cluster. Bucketed
// into a few size classes so visually dense areas stand out more.
function clusterIcon(cluster) {
  const count = cluster.getChildCount();
  let sizeClass = "small";
  if (count >= 100) sizeClass = "large";
  else if (count >= 20) sizeClass = "medium";

  return L.divIcon({
    html: `<div class="station-cluster station-cluster--${sizeClass}"><span>${count}</span></div>`,
    className: "station-cluster-wrapper",
    iconSize: L.point(40, 40),
  });
}

function renderStations() {
  if (!map) return;
  if (stationCluster) {
    map.removeLayer(stationCluster);
  }

  // Clusters nearby chargers into a single "N chargers" pin, which breaks
  // apart into individual pins as you zoom in (disableClusteringAtZoom
  // fully stops clustering once you're zoomed in close enough that
  // individual stations are usefully distinguishable).
  stationCluster = L.markerClusterGroup({
    iconCreateFunction: clusterIcon,
    maxClusterRadius: 60,
    disableClusteringAtZoom: 16,
    spiderfyOnMaxZoom: true,
    showCoverageOnHover: false,
  });

  const dimAll = anyActiveHighlight();

  for (const s of props.stations) {
    const highlighted = isHighlighted(s.operator_id);
    const marker = L.marker([s.latitude, s.longitude], {
      icon: pinIcon(s.operator_id, highlighted, dimAll && !highlighted),
    });
    // Click to see full metadata (operator, power, connectors, spot count);
    // hover tooltip stays as a lightweight preview.
    marker.bindTooltip(`${s.operator_name}${s.station_name ? " — " + s.station_name : ""}`);
    marker.bindPopup(popupContent(s));
    stationCluster.addLayer(marker);
  }

  map.addLayer(stationCluster);
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

/* Classic map-pin shape: a circle with one corner squared off, rotated 45°
   so the squared corner becomes a downward-pointing tip. */
.station-pin-wrapper {
  background: transparent !important;
  border: none !important;
}
.station-pin {
  border-radius: 50% 50% 50% 0;
  border: 2px solid #ffffff;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.5);
  transform: rotate(-45deg);
  cursor: pointer;
}

/* Cluster "summary" pins — shown instead of individual pins when several
   chargers are close together at the current zoom level. */
.station-cluster-wrapper {
  background: transparent !important;
  border: none !important;
}
.station-cluster {
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  border: 3px solid #ffffff;
  box-shadow: 0 1px 6px rgba(0, 0, 0, 0.5);
  color: #ffffff;
  font-weight: 700;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  cursor: pointer;
}
.station-cluster--small {
  width: 34px;
  height: 34px;
  font-size: 0.8rem;
  background: #1a73e8;
}
.station-cluster--medium {
  width: 42px;
  height: 42px;
  font-size: 0.9rem;
  background: #1557b0;
}
.station-cluster--large {
  width: 50px;
  height: 50px;
  font-size: 1rem;
  background: #0d3d7a;
}
</style>
