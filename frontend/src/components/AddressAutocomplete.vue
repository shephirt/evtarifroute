<script setup>
import { ref, watch } from "vue";
import { geocodeSuggest } from "../api.js";

const props = defineProps({
  modelValue: { type: String, default: "" },
  placeholder: { type: String, default: "" },
});
const emit = defineEmits(["update:modelValue"]);

const suggestions = ref([]);
const showSuggestions = ref(false);
let debounceTimer = null;
let latestQuery = "";

function onInput(e) {
  const value = e.target.value;
  emit("update:modelValue", value);

  clearTimeout(debounceTimer);
  if (value.trim().length < 3) {
    suggestions.value = [];
    return;
  }

  debounceTimer = setTimeout(async () => {
    latestQuery = value;
    const results = await geocodeSuggest(value);
    // Ignore stale responses if the user kept typing.
    if (latestQuery === value) {
      suggestions.value = results;
      showSuggestions.value = true;
    }
  }, 300);
}

function selectSuggestion(s) {
  emit("update:modelValue", s.label);
  suggestions.value = [];
  showSuggestions.value = false;
}

function onBlur() {
  // Delay so a click on a suggestion registers before the list closes.
  setTimeout(() => (showSuggestions.value = false), 150);
}
</script>

<template>
  <div class="address-input">
    <input
      type="text"
      :value="modelValue"
      :placeholder="placeholder"
      required
      autocomplete="off"
      @input="onInput"
      @focus="showSuggestions = suggestions.length > 0"
      @blur="onBlur"
    />
    <ul v-if="showSuggestions && suggestions.length" class="suggestions">
      <li
        v-for="(s, i) in suggestions"
        :key="i"
        class="suggestions__item"
        @mousedown.prevent="selectSuggestion(s)"
      >
        {{ s.label }}
      </li>
    </ul>
  </div>
</template>

<style scoped>
.address-input {
  position: relative;
}
.address-input input {
  width: 100%;
  padding: 8px 10px;
  border: 1px solid #d5d8dc;
  border-radius: 8px;
  font-size: 0.9rem;
  font-weight: 400;
}
.suggestions {
  position: absolute;
  top: calc(100% + 2px);
  left: 0;
  right: 0;
  z-index: 2000;
  background: white;
  border: 1px solid #d5d8dc;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
  list-style: none;
  margin: 0;
  padding: 4px;
  max-height: 220px;
  overflow-y: auto;
}
.suggestions__item {
  padding: 8px 10px;
  font-size: 0.85rem;
  font-weight: 400;
  border-radius: 6px;
  cursor: pointer;
}
.suggestions__item:hover {
  background: #eef5ff;
}
</style>
