<script setup lang="ts">
import {
  createStructuredObjectEntry,
  createStructuredValueNode,
  setStructuredValueKind,
  type StructuredObjectEntry,
  type StructuredValueFactory,
  type StructuredValueKind,
  type StructuredValueNode,
} from './structuredValue'
import SegmentedPicker from './SegmentedPicker.vue'

defineOptions({
  name: 'StructuredValueEditor',
})

interface ValueKindOption {
  title: string
  shortTitle: string
  value: StructuredValueKind
  icon: string
}

const props = withDefaults(
  defineProps<{
    node: StructuredValueNode
    factory: StructuredValueFactory
    label: string
    allowNull?: boolean
    depth?: number
  }>(),
  {
    allowNull: true,
    depth: 0,
  },
)

const VALUE_KIND_OPTIONS: ValueKindOption[] = [
  { value: 'string', title: '字符串', shortTitle: '文本', icon: 'mdi-format-text' },
  { value: 'number', title: '数字', shortTitle: '数字', icon: 'mdi-numeric' },
  { value: 'boolean', title: '布尔', shortTitle: '布尔', icon: 'mdi-toggle-switch-outline' },
  { value: 'null', title: 'null', shortTitle: 'null', icon: 'mdi-null' },
  { value: 'object', title: '对象', shortTitle: '对象', icon: 'mdi-code-braces' },
  { value: 'array', title: '数组', shortTitle: '数组', icon: 'mdi-format-list-bulleted-square' },
]

function availableKindOptions(): ValueKindOption[] {
  return props.allowNull ? VALUE_KIND_OPTIONS : VALUE_KIND_OPTIONS.filter((option) => option.value !== 'null')
}

function changeKind(kind: StructuredValueKind): void {
  setStructuredValueKind(props.node, props.factory, kind)
}

function addObjectEntry(): void {
  props.node.objectEntries.push(createStructuredObjectEntry(props.factory))
}

function removeObjectEntry(index: number): void {
  if (props.node.objectEntries.length === 1) {
    props.node.objectEntries[0] = createStructuredObjectEntry(props.factory)
    return
  }
  props.node.objectEntries.splice(index, 1)
}

function addArrayItem(): void {
  props.node.arrayItems.push(createStructuredValueNode(props.factory))
}

function removeArrayItem(index: number): void {
  if (props.node.arrayItems.length === 1) {
    props.node.arrayItems[0] = createStructuredValueNode(props.factory)
    return
  }
  props.node.arrayItems.splice(index, 1)
}

function moveArrayItem(index: number, direction: -1 | 1): void {
  const targetIndex = index + direction
  if (targetIndex < 0 || targetIndex >= props.node.arrayItems.length) {
    return
  }
  const [item] = props.node.arrayItems.splice(index, 1)
  props.node.arrayItems.splice(targetIndex, 0, item)
}

function objectEntryLabel(entry: StructuredObjectEntry, index: number): string {
  return entry.key.trim() || `${props.label}.${index + 1}`
}
</script>

<template>
  <div class="d-flex flex-column ga-4">
    <div class="d-flex flex-column ga-2">
      <div class="text-body-2 text-medium-emphasis">{{ label }} 类型</div>
      <SegmentedPicker
        :model-value="node.kind"
        :items="availableKindOptions()"
        :ariaLabel="`${label} 类型`"
        @update:model-value="(value) => changeKind(value as StructuredValueKind)"
      />
    </div>

    <v-text-field
      v-if="node.kind === 'string'"
      v-model="node.stringValue"
      :label="label"
      placeholder="DIRECT"
    />

    <v-text-field
      v-else-if="node.kind === 'number'"
      v-model="node.numberValue"
      :label="label"
      type="number"
      placeholder="0"
    />

    <v-switch
      v-else-if="node.kind === 'boolean'"
      v-model="node.booleanValue"
      :label="label"
      color="primary"
      hide-details
    />

    <v-alert v-else-if="node.kind === 'null'" type="info" variant="tonal">
      当前 {{ label }} 将提交为 null。
    </v-alert>

    <div v-else-if="node.kind === 'object'" class="d-flex flex-column ga-3">
      <div class="d-flex justify-space-between align-center">
        <div class="text-body-2 text-medium-emphasis">对象字段</div>
        <v-btn size="small" variant="tonal" prepend-icon="mdi-plus" @click="addObjectEntry">添加字段</v-btn>
      </div>

      <v-card
        v-for="(entry, index) in node.objectEntries"
        :key="entry.id"
        border="sm"
        rounded="xl"
        variant="outlined"
      >
        <v-card-text>
          <div class="d-flex justify-space-between align-center mb-3">
            <div class="text-body-2 font-weight-medium">字段 {{ index + 1 }}</div>
            <v-btn icon="mdi-delete-outline" size="small" variant="text" color="error" @click="removeObjectEntry(index)" />
          </div>

          <v-row>
            <v-col cols="12">
              <v-text-field v-model="entry.key" label="key" placeholder="name" />
            </v-col>
            <v-col cols="12">
              <StructuredValueEditor
                :node="entry.value"
                :factory="factory"
                :label="objectEntryLabel(entry, index)"
                :depth="depth + 1"
              />
            </v-col>
          </v-row>
        </v-card-text>
      </v-card>
    </div>

    <div v-else class="d-flex flex-column ga-3">
      <div class="d-flex justify-space-between align-center">
        <div class="text-body-2 text-medium-emphasis">数组元素</div>
        <v-btn size="small" variant="tonal" prepend-icon="mdi-plus" @click="addArrayItem">添加元素</v-btn>
      </div>

      <v-card
        v-for="(item, index) in node.arrayItems"
        :key="item.id"
        border="sm"
        rounded="xl"
        variant="outlined"
      >
        <v-card-text>
          <div class="d-flex justify-space-between align-center mb-3">
            <div class="text-body-2 font-weight-medium">元素 {{ index + 1 }}</div>
            <div class="d-flex ga-2">
              <v-btn icon="mdi-arrow-up" size="small" variant="text" :disabled="index === 0" @click="moveArrayItem(index, -1)" />
              <v-btn
                icon="mdi-arrow-down"
                size="small"
                variant="text"
                :disabled="index === node.arrayItems.length - 1"
                @click="moveArrayItem(index, 1)"
              />
              <v-btn icon="mdi-delete-outline" size="small" variant="text" color="error" @click="removeArrayItem(index)" />
            </div>
          </div>

          <StructuredValueEditor
            :node="item"
            :factory="factory"
            :label="`${label}[${index}]`"
            :depth="depth + 1"
          />
        </v-card-text>
      </v-card>
    </div>
  </div>
</template>
