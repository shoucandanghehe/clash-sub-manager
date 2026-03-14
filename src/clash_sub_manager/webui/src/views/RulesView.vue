<script setup lang="ts">
import { storeToRefs } from 'pinia'
import { computed, reactive, ref, watch } from 'vue'

import type { RuleSourcePayload, RuleSourceRecord } from '../api'
import { useManagerStore } from '../stores/manager'

interface RuleSourceForm {
  name: string
  url: string
  autoUpdate: boolean
}

const store = useManagerStore()
const { busy, ruleSources } = storeToRefs(store)

const dialog = ref(false)
const editingId = ref<number | null>(null)
const selectedRuleSourceId = ref<number | null>(null)
const form = reactive<RuleSourceForm>({
  name: '',
  url: '',
  autoUpdate: true,
})

const headers = [
  { title: '名称', key: 'name' },
  { title: '链接', key: 'url' },
  { title: '更新策略', key: 'auto_update' },
  { title: '缓存状态', key: 'cache' },
  { title: '操作', key: 'actions', sortable: false, align: 'end' },
] as const

const dialogTitle = computed(() => {
  return editingId.value === null ? '新建规则源' : '编辑规则源'
})

const canSubmit = computed(() => {
  return form.name.trim().length > 0 && form.url.trim().length > 0
})

const selectedRuleSource = computed(() => {
  return ruleSources.value.find((ruleSource) => ruleSource.id === selectedRuleSourceId.value) ?? null
})

const selectedRuleSourceContent = computed(() => {
  return selectedRuleSource.value?.content?.trim() || '尚未缓存规则内容，请先刷新该规则源。'
})

watch(
  ruleSources,
  (items) => {
    if (items.length === 0) {
      selectedRuleSourceId.value = null
      return
    }

    const stillExists = items.some((item) => item.id === selectedRuleSourceId.value)
    if (!stillExists) {
      selectedRuleSourceId.value = items[0].id
    }
  },
  { immediate: true },
)

function resetForm(): void {
  editingId.value = null
  form.name = ''
  form.url = ''
  form.autoUpdate = true
}

function openCreateDialog(): void {
  resetForm()
  dialog.value = true
}

function selectRuleSource(ruleSource: RuleSourceRecord): void {
  selectedRuleSourceId.value = ruleSource.id
}

function openEditDialog(ruleSource: RuleSourceRecord): void {
  editingId.value = ruleSource.id
  form.name = ruleSource.name
  form.url = ruleSource.url
  form.autoUpdate = ruleSource.auto_update
  dialog.value = true
}

async function refreshRuleSource(ruleSource: RuleSourceRecord): Promise<void> {
  selectedRuleSourceId.value = ruleSource.id
  await store.refreshRuleSource(ruleSource.id)
}

async function saveRuleSource(): Promise<void> {
  const payload: RuleSourcePayload = {
    name: form.name.trim(),
    url: form.url.trim(),
    auto_update: form.autoUpdate,
  }

  const succeeded = editingId.value === null
    ? await store.createRuleSource(payload)
    : await store.updateRuleSource(editingId.value, payload)

  if (succeeded) {
    dialog.value = false
    resetForm()
  }
}
</script>

<template>
  <v-row>
    <v-col cols="12" lg="8">
      <v-card>
        <v-card-item>
          <div class="d-flex flex-column flex-sm-row ga-4 align-sm-center justify-space-between">
            <div>
              <v-card-title class="px-0">规则源</v-card-title>
              <v-card-subtitle class="px-0">管理远程规则源并手动刷新缓存。</v-card-subtitle>
            </div>
            <v-btn color="primary" prepend-icon="mdi-plus" @click="openCreateDialog">新建规则源</v-btn>
          </div>
        </v-card-item>

        <v-data-table :headers="headers" :items="ruleSources" item-value="id">
          <template #item.name="{ item }">
            <v-btn class="px-0" variant="text" @click="selectRuleSource(item)">
              {{ item.name }}
            </v-btn>
          </template>

          <template #item.url="{ item }">
            <div class="py-2 text-break">{{ item.url }}</div>
          </template>

          <template #item.auto_update="{ item }">
            <v-chip :color="item.auto_update ? 'primary' : 'default'" size="small" variant="tonal">
              {{ item.auto_update ? '自动更新' : '仅手动' }}
            </v-chip>
          </template>

          <template #item.cache="{ item }">
            <v-chip :color="item.content ? 'secondary' : 'default'" size="small" variant="tonal">
              {{ item.content ? '已缓存' : '未缓存' }}
            </v-chip>
          </template>

          <template #item.actions="{ item }">
            <div class="d-flex justify-end ga-2 py-2">
              <v-btn icon="mdi-eye-outline" size="small" variant="text" @click="selectRuleSource(item)" />
              <v-btn icon="mdi-refresh" size="small" variant="text" @click="refreshRuleSource(item)" />
              <v-btn icon="mdi-pencil" size="small" variant="text" @click="openEditDialog(item)" />
              <v-btn icon="mdi-delete-outline" size="small" variant="text" color="error" @click="store.deleteRuleSource(item.id)" />
            </div>
          </template>
        </v-data-table>
      </v-card>
    </v-col>

    <v-col cols="12" lg="4">
      <v-card class="fill-height">
        <v-card-item>
          <v-card-title class="px-0">规则预览</v-card-title>
          <v-card-subtitle class="px-0">
            {{ selectedRuleSource?.name ?? '尚未选择规则源' }}
          </v-card-subtitle>
        </v-card-item>
        <v-card-text>
          <div class="text-body-2 text-medium-emphasis mb-4 text-break">
            {{ selectedRuleSource?.url ?? '从左侧选择一个规则源即可查看其缓存内容。' }}
          </div>
          <v-sheet class="preview-panel" color="surface-variant" rounded="xl">
            <pre>{{ selectedRuleSourceContent }}</pre>
          </v-sheet>
        </v-card-text>
      </v-card>
    </v-col>
  </v-row>

  <v-dialog v-model="dialog">
    <v-card>
      <v-card-item>
        <v-card-title>{{ dialogTitle }}</v-card-title>
        <v-card-subtitle>规则源名称同样必须唯一，便于在错误和列表中定位。</v-card-subtitle>
      </v-card-item>

      <v-card-text>
        <v-row>
          <v-col cols="12" md="6">
            <v-text-field v-model="form.name" label="名称" maxlength="255" />
          </v-col>
          <v-col cols="12" md="6">
            <v-switch v-model="form.autoUpdate" label="自动更新" hide-details />
          </v-col>
          <v-col cols="12">
            <v-text-field v-model="form.url" label="规则链接" placeholder="https://example.com/rules.txt" />
          </v-col>
        </v-row>
      </v-card-text>

      <v-card-actions>
        <v-spacer />
        <v-btn variant="text" @click="dialog = false">取消</v-btn>
        <v-btn color="primary" :disabled="busy || !canSubmit" @click="saveRuleSource">保存</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>
