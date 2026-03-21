<script setup lang="ts">
import { storeToRefs } from 'pinia'
import { computed, reactive, ref } from 'vue'

import type { MergeProfilePayload, MergeProfileRecord, TemplateSourceRecord } from '../api'
import { useManagerStore } from '../stores/manager'

interface MergeProfileForm {
  name: string
  templateSource: string | null
  subscriptionIds: number[]
  enabled: boolean
}

interface TemplateSourceOption {
  title: string
  value: string
}

const emit = defineEmits<{
  navigatePreview: []
}>()

const store = useManagerStore()
const { busy, compositeTemplates, mergeProfiles, subscriptions, templates } = storeToRefs(store)

const dialog = ref(false)
const editingId = ref<number | null>(null)
const form = reactive<MergeProfileForm>({
  name: '',
  templateSource: null,
  subscriptionIds: [],
  enabled: true,
})

const headers = [
  { title: '名称', key: 'name' },
  { title: '订阅', key: 'subscriptions', sortable: false },
  { title: '模板', key: 'template' },
  { title: '状态', key: 'enabled' },
  { title: '操作', key: 'actions', sortable: false, align: 'end' },
] as const

const dialogTitle = computed(() => {
  return editingId.value === null ? '新建合并配置' : '编辑合并配置'
})

const canSubmit = computed(() => {
  return form.name.trim().length > 0 && form.subscriptionIds.length > 0
})

function resetForm(): void {
  editingId.value = null
  form.name = ''
  form.templateSource = null
  form.subscriptionIds = []
  form.enabled = true
}

function openCreateDialog(): void {
  resetForm()
  dialog.value = true
}

function formatTemplateSourceValue(source: TemplateSourceRecord | null): string | null {
  return source ? `${source.kind}:${source.id}` : null
}

function parseTemplateSourceValue(value: string | null): TemplateSourceRecord | null {
  if (!value) {
    return null
  }

  const [kind, idText] = value.split(':', 2)
  if ((kind !== 'template' && kind !== 'composite') || !idText || !/^\d+$/.test(idText)) {
    throw new Error('模板来源无效。')
  }

  const id = Number(idText)
  const source =
    kind === 'template'
      ? templates.value.find((template) => template.id === id)
      : compositeTemplates.value.find((template) => template.id === id)

  if (!source) {
    throw new Error('所选模板不存在。')
  }

  return {
    id,
    kind,
    name: source.name,
  }
}

const templateSourceOptions = computed<TemplateSourceOption[]>(() => [
  ...templates.value.map((template) => ({
    title: `[基础] ${template.name}`,
    value: `template:${template.id}`,
  })),
  ...compositeTemplates.value.map((template) => ({
    title: `[组合] ${template.name}`,
    value: `composite:${template.id}`,
  })),
])

function openEditDialog(profile: MergeProfileRecord): void {
  editingId.value = profile.id
  form.name = profile.name
  form.templateSource = formatTemplateSourceValue(profile.template_source)
  form.subscriptionIds = profile.subscriptions.map((subscription) => subscription.id)
  form.enabled = profile.enabled
  dialog.value = true
}

async function saveProfile(): Promise<void> {
  let templateSource: TemplateSourceRecord | null
  try {
    templateSource = parseTemplateSourceValue(form.templateSource)
  } catch (caught) {
    store.showError(caught instanceof Error ? caught.message : '模板来源无效。')
    return
  }

  const payload: MergeProfilePayload = {
    name: form.name.trim(),
    template_source: templateSource,
    enabled: form.enabled,
    subscription_ids: [...form.subscriptionIds],
  }

  const succeeded = editingId.value === null
    ? await store.createMergeProfile(payload)
    : await store.updateMergeProfile(editingId.value, payload)

  if (succeeded) {
    dialog.value = false
    resetForm()
  }
}

async function generateProfile(profile: MergeProfileRecord): Promise<void> {
  if (await store.runMergeProfilePreview(profile.id)) {
    emit('navigatePreview')
  }
}

function buildProfileConfigUrl(profileName: string): string {
  const encodedName = encodeURIComponent(profileName)
  return new URL(`/merge-profiles/by-name/${encodedName}/config`, window.location.origin).toString()
}

function copyToClipboardFallback(text: string): boolean {
  const textArea = document.createElement('textarea')
  textArea.value = text
  textArea.style.position = 'fixed'
  textArea.style.left = '-999999px'
  textArea.style.top = '-999999px'
  document.body.appendChild(textArea)
  textArea.focus()
  textArea.select()
  try {
    const successful = document.execCommand('copy')
    document.body.removeChild(textArea)
    return successful
  } catch {
    document.body.removeChild(textArea)
    return false
  }
}

async function copyProfileLink(profile: MergeProfileRecord): Promise<void> {
  const link = buildProfileConfigUrl(profile.name)

  if (navigator.clipboard) {
    try {
      await navigator.clipboard.writeText(link)
      store.showNotice(`已复制 ${profile.name} 链接。`)
      return
    } catch {
      // Clipboard API 失败，尝试 fallback
    }
  }

  if (copyToClipboardFallback(link)) {
    store.showNotice(`已复制 ${profile.name} 链接。`)
  } else {
    store.showError('复制链接失败，请检查浏览器权限。')
  }
}
</script>

<template>
  <v-card>
    <v-card-item>
      <div class="d-flex flex-column flex-sm-row ga-4 align-sm-center justify-space-between">
        <div>
          <v-card-title class="px-0">合并配置</v-card-title>
          <v-card-subtitle class="px-0">把订阅选择和模板选择固化成可复用的生成配置。</v-card-subtitle>
        </div>
        <v-btn color="primary" prepend-icon="mdi-plus" @click="openCreateDialog">新建合并配置</v-btn>
      </div>
    </v-card-item>

    <v-data-table :headers="headers" :items="mergeProfiles" item-value="id">
      <template #item.subscriptions="{ item }">
        <div class="d-flex flex-wrap ga-2 py-2">
          <v-chip v-for="subscription in item.subscriptions" :key="subscription.id" size="small" variant="tonal">
            {{ subscription.name }}
          </v-chip>
          <span v-if="item.subscriptions.length === 0" class="text-caption text-medium-emphasis">未选择订阅</span>
        </div>
      </template>

      <template #item.template="{ item }">
        <v-chip size="small" variant="tonal">{{ item.template_source ? `${item.template_source.kind === 'template' ? '基础' : '组合'} · ${item.template_source.name}` : '无模板' }}</v-chip>
      </template>

      <template #item.enabled="{ item }">
        <v-chip :color="item.enabled ? 'primary' : 'default'" size="small" variant="tonal">
          {{ item.enabled ? '启用' : '停用' }}
        </v-chip>
      </template>

      <template #item.actions="{ item }">
        <div class="d-flex justify-end ga-2 py-2">
          <v-btn icon="mdi-content-copy" size="small" variant="text" @click="copyProfileLink(item)" />
          <v-btn icon="mdi-play-circle-outline" size="small" variant="text" color="primary" @click="generateProfile(item)" />
          <v-btn icon="mdi-pencil" size="small" variant="text" @click="openEditDialog(item)" />
          <v-btn icon="mdi-delete-outline" size="small" variant="text" color="error" @click="store.deleteMergeProfile(item.id)" />
        </div>
      </template>
    </v-data-table>
  </v-card>

  <v-dialog v-model="dialog">
    <v-card>
      <v-card-item>
        <v-card-title>{{ dialogTitle }}</v-card-title>
        <v-card-subtitle>选择要合并的订阅，以及要套用的模板。</v-card-subtitle>
      </v-card-item>

      <v-card-text>
        <v-row>
          <v-col cols="12" md="6">
            <v-text-field v-model="form.name" label="名称" maxlength="255" />
          </v-col>
          <v-col cols="12" md="6">
            <v-select
              v-model="form.templateSource"
              :items="templateSourceOptions"
              item-title="title"
              item-value="value"
              label="模板"
              clearable
            />
          </v-col>
          <v-col cols="12">
            <v-autocomplete
              v-model="form.subscriptionIds"
              :items="subscriptions"
              item-title="name"
              item-value="id"
              label="订阅多选"
              multiple
            />
          </v-col>
          <v-col cols="12" md="4">
            <v-switch v-model="form.enabled" label="启用此配置" hide-details />
          </v-col>
        </v-row>
      </v-card-text>

      <v-card-actions>
        <v-spacer />
        <v-btn variant="text" @click="dialog = false">取消</v-btn>
        <v-btn color="primary" :disabled="busy || !canSubmit" @click="saveProfile">保存</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>
