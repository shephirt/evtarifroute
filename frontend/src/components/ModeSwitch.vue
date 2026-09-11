<script setup>
defineProps({
  modelValue: { type: String, required: true },
});
const emit = defineEmits(["update:modelValue"]);
</script>

<template>
  <div class="mode-switch">
    <button
      class="mode-switch__option"
      :class="{ 'mode-switch__option--active': modelValue === 'route' }"
      @click="emit('update:modelValue', 'route')"
    >
      Travel &amp; Route
    </button>
    <button
      class="mode-switch__option"
      :class="{ 'mode-switch__option--active': modelValue === 'radius' }"
      @click="emit('update:modelValue', 'radius')"
    >
      Home &amp; Daily Life
    </button>
  </div>
</template>

<style scoped>
.mode-switch {
  display: flex;
  background: #eef0f2;
  border-radius: 10px;
  padding: 4px;
  gap: 4px;
}
.mode-switch__option {
  flex: 1;
  border: none;
  background: transparent;
  padding: 8px 10px;
  font-size: 0.85rem;
  font-weight: 600;
  color: #555;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}
.mode-switch__option--active {
  background: #ffffff;
  color: #1a73e8;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.15);
}
</style>
