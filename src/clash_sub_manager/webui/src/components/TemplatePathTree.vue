<script setup lang="ts">
import { computed } from 'vue'

import type { TemplatePathTreeNode } from '../utils/templatePath'

defineOptions({
  name: 'TemplatePathTree',
})

const props = withDefaults(
  defineProps<{
    nodes: TemplatePathTreeNode[]
    activePath?: string | null
    searchTerm?: string
    collapsedPaths?: string[]
    level?: number
  }>(),
  {
    activePath: null,
    searchTerm: '',
    collapsedPaths: () => [],
    level: 0,
  }
)

const emit = defineEmits<{
  select: [path: string]
  toggle: [path: string]
}>()

const collapsedPathSet = computed(() => new Set(props.collapsedPaths))


function highlightParts(value: string): Array<{ text: string; matched: boolean }> {
  const keyword = props.searchTerm.trim()
  if (!keyword) {
    return [{ text: value, matched: false }]
  }

  const source = value.toLowerCase()
  const needle = keyword.toLowerCase()
  const parts: Array<{ text: string; matched: boolean }> = []
  let start = 0

  while (start < value.length) {
    const index = source.indexOf(needle, start)
    if (index === -1) {
      parts.push({ text: value.slice(start), matched: false })
      break
    }

    if (index > start) {
      parts.push({ text: value.slice(start, index), matched: false })
    }
    parts.push({ text: value.slice(index, index + keyword.length), matched: true })
    start = index + keyword.length
  }

  return parts.length > 0 ? parts : [{ text: value, matched: false }]
}


function selectPath(path: string): void {
  emit('select', path)
}

function toggleNode(path: string): void {
  emit('toggle', path)
}

function isExpanded(path: string): boolean {
  if (props.searchTerm.trim()) {
    return true
  }
  return !collapsedPathSet.value.has(path)
}
</script>

<template>
  <div class="path-tree" role="tree">
    <div v-for="node in nodes" :key="node.id" class="path-tree__node">
      <div class="path-tree__row" :style="{ paddingInlineStart: `${level * 22}px` }">
        <button
          v-if="node.children.length > 0"
          type="button"
          class="path-tree__toggle"
          :aria-label="isExpanded(node.path) ? '收起节点' : '展开节点'"
          @click="toggleNode(node.path)"
        >
          <v-icon :icon="isExpanded(node.path) ? 'mdi-minus-box-outline' : 'mdi-plus-box-outline'" size="16" />
        </button>
        <span v-else class="path-tree__toggle path-tree__toggle--placeholder" />

        <button
          type="button"
          class="path-tree__button"
          :class="{ 'path-tree__button--active': node.path === activePath }"
          @click="selectPath(node.path)"
        >
          <span class="path-tree__branch" />
          <span class="path-tree__content">
            <span class="path-tree__label">
              <template v-for="(part, partIndex) in highlightParts(node.label)" :key="`${node.id}-label-${partIndex}`">
                <mark v-if="part.matched" class="path-tree__highlight">{{ part.text }}</mark>
                <template v-else>{{ part.text }}</template>
              </template>
            </span>
            <span class="path-tree__preview">
              <template v-for="(part, partIndex) in highlightParts(node.valuePreview)" :key="`${node.id}-preview-${partIndex}`">
                <mark v-if="part.matched" class="path-tree__highlight">{{ part.text }}</mark>
                <template v-else>{{ part.text }}</template>
              </template>
            </span>
          </span>
        </button>
      </div>

      <div v-if="node.children.length > 0 && isExpanded(node.path)" class="path-tree__children">
        <TemplatePathTree
          :nodes="node.children"
          :active-path="activePath"
          :search-term="searchTerm"
          :collapsed-paths="collapsedPaths"
          :level="level + 1"
          @select="selectPath"
          @toggle="toggleNode"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.path-tree {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.path-tree__node {
  position: relative;
}

.path-tree__row {
  display: flex;
  align-items: flex-start;
  gap: 2px;
  min-height: 28px;
}

.path-tree__toggle {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  min-width: 20px;
  height: 20px;
  margin-top: 2px;
  border: none;
  background: transparent;
  color: rgba(var(--v-theme-on-surface), var(--v-medium-emphasis-opacity));
  cursor: pointer;
  padding: 0;
}

.path-tree__toggle--placeholder {
  cursor: default;
}

.path-tree__button {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  width: 100%;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: inherit;
  cursor: pointer;
  padding: 3px 8px 3px 0;
  text-align: left;
}

.path-tree__button:hover {
  background: rgba(var(--v-theme-primary), 0.05);
}

.path-tree__button--active {
  background: rgba(var(--v-theme-primary), 0.12);
  color: rgb(var(--v-theme-primary));
}

.path-tree__branch {
  position: relative;
  width: 14px;
  min-width: 14px;
  height: 14px;
}

.path-tree__branch::before {
  content: '';
  position: absolute;
  left: 0;
  top: 7px;
  width: 10px;
  border-top: 1px dotted rgba(var(--v-theme-on-surface), 0.35);
}

.path-tree__content {
  display: inline-flex;
  align-items: baseline;
  gap: 10px;
  min-width: 0;
}

.path-tree__label {
  font-family: ui-monospace, 'SFMono-Regular', 'SF Mono', Consolas, 'Liberation Mono', Menlo, monospace;
  font-size: 0.92rem;
}

.path-tree__preview {
  color: rgba(var(--v-theme-on-surface), var(--v-medium-emphasis-opacity));
  font-size: 0.8rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.path-tree__highlight {
  background: rgba(var(--v-theme-warning), 0.35);
  color: inherit;
  border-radius: 2px;
  padding: 0 1px;
}


.path-tree__children {
  position: relative;
}

.path-tree__children::before {
  content: '';
  position: absolute;
  left: 10px;
  top: -2px;
  bottom: 4px;
  border-left: 1px dotted rgba(var(--v-theme-on-surface), 0.25);
}
</style>
