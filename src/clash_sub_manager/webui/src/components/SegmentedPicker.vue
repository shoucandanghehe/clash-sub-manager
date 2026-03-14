<script setup lang="ts" generic="T extends string | number">
interface SegmentedPickerOption<TValue extends string | number> {
  title: string
  shortTitle: string
  value: TValue
  icon?: string
}

const props = defineProps<{
  modelValue: T
  items: SegmentedPickerOption<T>[]
  ariaLabel: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: T]
}>()

function select(value: T): void {
  if (value === props.modelValue) {
    return
  }
  emit('update:modelValue', value)
}
</script>

<template>
  <div class="segmented-picker" role="tablist" :aria-label="ariaLabel">
    <v-btn
      v-for="option in items"
      :key="option.value"
      :color="modelValue === option.value ? 'primary' : undefined"
      :title="option.title"
      :variant="modelValue === option.value ? 'flat' : 'text'"
      class="segmented-picker__button"
      :class="{ 'segmented-picker__button--active': modelValue === option.value }"
      size="small"
      @click="select(option.value)"
    >
      <v-icon v-if="option.icon" :icon="option.icon" start />
      {{ option.shortTitle }}
    </v-btn>
  </div>
</template>

<style scoped>
.segmented-picker {
  display: inline-flex;
  flex-wrap: wrap;
  gap: 0;
  border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  border-radius: 10px;
  overflow: hidden;
  width: fit-content;
  max-width: 100%;
}

.segmented-picker__button {
  border-radius: 0 !important;
  border-inline-end: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  min-width: 0;
}

.segmented-picker__button:last-child {
  border-inline-end: none;
}

.segmented-picker__button--active {
  box-shadow: none;
}
</style>
