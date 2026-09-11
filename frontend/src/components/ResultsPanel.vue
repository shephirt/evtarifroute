<script setup>
defineProps({
  rankings: { type: Array, default: () => [] },
  totalStations: { type: Number, default: 0 },
  tariffs: { type: Array, default: () => [] },
  tariffsLoading: { type: Boolean, default: false },
  selectedOperatorId: { type: [Number, String, null], default: null },
});
const emit = defineEmits(["hover-operator", "hover-tariff", "select-operator"]);
</script>

<template>
  <div class="results">
    <section v-if="rankings.length" class="section">
      <h3>CPO Dominance <span class="muted">({{ totalStations }} stations)</span></h3>
      <p v-if="selectedOperatorId !== null" class="muted hint">
        Showing only the selected CPO's stations — click it again to show all.
      </p>
      <ul class="ranking-list">
        <li
          v-for="r in rankings"
          :key="r.operator_id ?? r.operator_name"
          class="ranking-row"
          :class="{ 'ranking-row--selected': r.operator_id === selectedOperatorId }"
          @mouseenter="emit('hover-operator', r.operator_id)"
          @mouseleave="emit('hover-operator', null)"
          @click="emit('select-operator', r.operator_id)"
        >
          <span class="ranking-row__name">{{ r.operator_name }}</span>
          <span class="ranking-row__meta">
            <span v-if="r.effective_station_count != null" class="ranking-row__segments">
              {{ r.effective_station_count }} well-spaced
            </span>
            <span class="ranking-row__count">{{ r.station_count }}</span>
          </span>
        </li>
      </ul>
    </section>

    <section class="section">
      <h3>Tariff Recommendations</h3>
      <p v-if="tariffsLoading" class="muted">Loading tariffs…</p>
      <p v-else-if="!tariffs.length" class="muted">
        No matching MSP tariffs configured yet.
      </p>
      <ul v-else class="tariff-cards">
        <li
          v-for="t in tariffs"
          :key="t.tariff_id"
          class="tariff-card"
          @mouseenter="emit('hover-tariff', t.covered_operator_ids)"
          @mouseleave="emit('hover-tariff', null)"
        >
          <div class="tariff-card__header">
            <span class="tariff-card__name">{{ t.name }}</span>
            <span class="tariff-card__provider">{{ t.provider }}</span>
          </div>
          <div class="tariff-card__cost">
            €{{ t.estimated_monthly_cost.toFixed(2) }}<span class="muted">/mo (est.)</span>
          </div>
          <div class="tariff-card__coverage">
            {{ (t.coverage_ratio * 100).toFixed(0) }}% network coverage
            ({{ t.covered_station_count }} stations)
          </div>
          <p v-if="t.notes" class="tariff-card__notes">{{ t.notes }}</p>
        </li>
      </ul>
    </section>
  </div>
</template>

<style scoped>
.results {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.section h3 {
  margin: 0 0 8px;
  font-size: 0.95rem;
}
.muted {
  color: #888;
  font-weight: 400;
  font-size: 0.8rem;
}
.ranking-list {
  list-style: none;
  margin: 0;
  padding: 0;
  max-height: 220px;
  overflow-y: auto;
  border: 1px solid #eee;
  border-radius: 8px;
}
.ranking-row {
  display: flex;
  justify-content: space-between;
  padding: 6px 10px;
  font-size: 0.85rem;
  cursor: pointer;
  border-bottom: 1px solid #f2f2f2;
}
.ranking-row:last-child {
  border-bottom: none;
}
.ranking-row:hover {
  background: #eef5ff;
}
.ranking-row--selected {
  background: #dbeafe;
  font-weight: 600;
}
.hint {
  margin: -4px 0 8px;
}
.ranking-row__meta {
  display: flex;
  align-items: center;
  gap: 8px;
}
.ranking-row__segments {
  font-size: 0.72rem;
  color: #888;
}
.ranking-row__count {
  font-weight: 600;
  color: #1a73e8;
}
.tariff-cards {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.tariff-card {
  border: 1px solid #e2e5e9;
  border-radius: 10px;
  padding: 10px 12px;
  cursor: default;
  transition: box-shadow 0.15s, border-color 0.15s;
}
.tariff-card:hover {
  border-color: #1a73e8;
  box-shadow: 0 2px 8px rgba(26, 115, 232, 0.15);
}
.tariff-card__header {
  display: flex;
  justify-content: space-between;
  font-size: 0.85rem;
  font-weight: 600;
}
.tariff-card__provider {
  color: #888;
  font-weight: 400;
}
.tariff-card__cost {
  font-size: 1.1rem;
  font-weight: 700;
  color: #1a73e8;
  margin-top: 4px;
}
.tariff-card__coverage {
  font-size: 0.78rem;
  color: #555;
  margin-top: 2px;
}
.tariff-card__notes {
  font-size: 0.75rem;
  color: #888;
  margin: 6px 0 0;
}
</style>
