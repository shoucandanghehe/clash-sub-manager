<script setup lang="ts">
import { storeToRefs } from 'pinia'
import { computed, reactive, ref } from 'vue'

import {
  singBoxConfigPath,
  type MergeProfilePayload,
  type MergeProfileRecord,
  type MergeProfileTargetRecord,
  type TemplateSourceRecord,
} from '../api'
import { useManagerStore } from '../stores/manager'

type ProfileFormat = 'yaml' | 'json'

interface SingBoxTargetForm {
  compatibilityVersion: string | null
  templateId: number | null
}

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
const { busy, compositeTemplates, mergeProfiles, singBoxVersions, subscriptions, templates } = storeToRefs(store)

const dialog = ref(false)
const editingId = ref<number | null>(null)
const form = reactive<MergeProfileForm>({
  name: '',
  templateSource: null,
  subscriptionIds: [],
  enabled: true,
})

const singBoxDialog = ref(false)
const singBoxProfileId = ref<number | null>(null)
const singBoxForm = reactive<SingBoxTargetForm>({
  compatibilityVersion: null,
  templateId: null,
})
const singBoxProfile = computed(() => {
  return mergeProfiles.value.find((profile) => profile.id === singBoxProfileId.value) ?? null
})
const selectedSingBoxVersion = computed(() => {
  return singBoxVersions.value.find((version) => version.compatibility_version === singBoxForm.compatibilityVersion)
})
const singBoxTemplates = computed(() => {
  return templates.value.filter((template) => (
    template.target === 'sing-box' && template.schema_version === selectedSingBoxVersion.value?.schema_version
  ))
})
const canSaveSingBoxTarget = computed(() => {
  return singBoxProfile.value !== null && singBoxTemplates.value.some((template) => template.id === singBoxForm.templateId)
})

const headers = [
  { title: '名称', key: 'name' },
  { title: '订阅', key: 'subscriptions', sortable: false },
  { title: 'Mihomo 模板', key: 'template' },
  { title: 'sing-box', key: 'sing_box_target', sortable: false },
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
      ? templates.value.find((template) => template.id === id && template.target === 'mihomo')
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
  ...templates.value.filter((template) => template.target === 'mihomo').map((template) => ({
    title: `[Mihomo 基础] ${template.name}`,
    value: `template:${template.id}`,
  })),
  ...compositeTemplates.value.map((template) => ({
    title: `[Mihomo 组合] ${template.name}`,
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

function openSingBoxDialog(profile: MergeProfileRecord): void {
  singBoxProfileId.value = profile.id
  singBoxForm.compatibilityVersion = profile.sing_box_target?.compatibility_version ?? null
  singBoxForm.templateId = profile.sing_box_target?.template_id ?? null
  singBoxDialog.value = true
}

function updateSingBoxVersion(version: string | null): void {
  if (version === singBoxForm.compatibilityVersion) {
    return
  }
  singBoxForm.compatibilityVersion = version
  singBoxForm.templateId = null
}

function singBoxTemplateName(target: MergeProfileTargetRecord): string {
  return templates.value.find((template) => template.id === target.template_id)?.name ?? `模板 #${target.template_id}`
}

async function saveSingBoxTarget(): Promise<void> {
  const profile = singBoxProfile.value
  const compatibilityVersion = singBoxForm.compatibilityVersion
  const templateId = singBoxForm.templateId
  if (profile === null || compatibilityVersion === null || templateId === null) {
    return
  }
  if (await store.saveSingBoxTarget(profile.id, {
    compatibility_version: compatibilityVersion,
    template_id: templateId,
  })) {
    singBoxDialog.value = false
  }
}

async function removeSingBoxTarget(): Promise<void> {
  const profile = singBoxProfile.value
  if (profile !== null && await store.deleteSingBoxTarget(profile.id)) {
    singBoxDialog.value = false
  }
}

async function generateProfile(profile: MergeProfileRecord, format: ProfileFormat = 'yaml'): Promise<void> {
  const succeeded = format === 'json'
    ? await store.runSingBoxProfilePreview(profile)
    : await store.runMergeProfilePreview(profile.id)
  if (succeeded) {
    emit('navigatePreview')
  }
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

async function copyProfileLink(profile: MergeProfileRecord, format: ProfileFormat = 'yaml'): Promise<void> {
  let path: string
  if (format === 'json') {
    const target = profile.sing_box_target
    if (target === null) {
      store.showError('请先绑定 sing-box 目标。')
      return
    }
    path = singBoxConfigPath(profile.public_id, target.compatibility_version)
  } else {
    path = `/merge-profiles/by-name/${encodeURIComponent(profile.name)}/config`
  }
  const link = new URL(path, window.location.origin).toString()
  const message = `已复制 ${profile.name} 的 ${format === 'json' ? 'sing-box JSON' : 'Mihomo YAML'} 链接。`

  if (navigator.clipboard) {
    try {
      await navigator.clipboard.writeText(link)
      store.showNotice(message)
      return
    } catch {
      // Clipboard API 失败，尝试 fallback
    }
  }

  if (copyToClipboardFallback(link)) {
    store.showNotice(message)
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
          <v-card-subtitle class="px-0">管理订阅、Mihomo 模板和独立的 sing-box 输出目标。</v-card-subtitle>
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

      <template #item.sing_box_target="{ item }">
        <div class="d-flex flex-column ga-2 py-2">
          <div v-if="item.sing_box_target" class="d-flex flex-wrap align-center ga-2">
            <v-chip size="small" variant="tonal">{{ item.sing_box_target.compatibility_version }}</v-chip>
            <span class="text-body-2">{{ singBoxTemplateName(item.sing_box_target) }}</span>
          </div>
          <span v-else class="text-caption text-medium-emphasis">未绑定</span>
          <div class="d-flex align-center ga-1">
            <v-btn
              size="small"
              variant="text"
              :disabled="busy"
              :aria-label="`配置 ${item.name} 的 sing-box 目标`"
              @click="openSingBoxDialog(item)"
            >{{ item.sing_box_target ? '配置' : '绑定' }}</v-btn>
            <v-btn
              size="small"
              variant="text"
              color="primary"
              :disabled="busy || !item.sing_box_target"
              :aria-label="`生成 ${item.name} 的 sing-box JSON`"
              @click="generateProfile(item, 'json')"
            >生成 JSON</v-btn>
            <v-btn
              icon="mdi-content-copy"
              size="small"
              variant="text"
              :disabled="!item.sing_box_target"
              :aria-label="`复制 ${item.name} 的 sing-box JSON 链接`"
              title="复制 sing-box JSON 链接"
              @click="copyProfileLink(item, 'json')"
            />
          </div>
        </div>
      </template>

      <template #item.enabled="{ item }">
        <v-chip :color="item.enabled ? 'primary' : 'default'" size="small" variant="tonal">
          {{ item.enabled ? '启用' : '停用' }}
        </v-chip>
      </template>

      <template #item.actions="{ item }">
        <div class="d-flex justify-end ga-2 py-2">
          <v-btn
            icon="mdi-content-copy"
            size="small"
            variant="text"
            :aria-label="`复制 ${item.name} 的 Mihomo YAML 链接`"
            title="复制 Mihomo YAML 链接"
            @click="copyProfileLink(item)"
          />
          <v-btn
            icon="mdi-play-circle-outline"
            size="small"
            variant="text"
            color="primary"
            :disabled="busy"
            :aria-label="`生成 ${item.name} 的 Mihomo YAML`"
            title="生成 Mihomo YAML"
            @click="generateProfile(item)"
          />
          <v-btn icon="mdi-pencil" size="small" variant="text" :disabled="busy" :aria-label="`编辑 ${item.name}`" @click="openEditDialog(item)" />
          <v-btn icon="mdi-delete-outline" size="small" variant="text" color="error" :disabled="busy" :aria-label="`删除 ${item.name}`" @click="store.deleteMergeProfile(item.id)" />
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
              label="Mihomo 模板"
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

  <v-dialog v-model="singBoxDialog" max-width="760">
    <v-card>
      <v-card-item>
        <v-card-title>sing-box 目标 · {{ singBoxProfile?.name }}</v-card-title>
        <v-card-subtitle class="text-wrap">独立保存，不会更改 Mihomo 模板或所选订阅。</v-card-subtitle>
      </v-card-item>
      <v-card-text>
        <v-row>
          <v-col cols="12" md="4">
            <v-select
              :model-value="singBoxForm.compatibilityVersion"
              :items="singBoxVersions"
              item-title="compatibility_version"
              item-value="compatibility_version"
              label="目标内核版本"
              :disabled="busy"
              @update:model-value="updateSingBoxVersion"
            />
          </v-col>
          <v-col cols="12" md="8">
            <v-select
              v-model="singBoxForm.templateId"
              :items="singBoxTemplates"
              item-title="name"
              item-value="id"
              label="sing-box 原生模板"
              no-data-text="没有匹配版本的模板，请先到“模板”页面创建。"
              :disabled="busy || selectedSingBoxVersion === undefined"
            />
          </v-col>
        </v-row>
        <p class="text-body-2 text-medium-emphasis mt-2">
          JSON 配置使用订阅缓存，并在生成时由目标版本内核校验。需要更新远程节点时，请先到“订阅”页面更新。
        </p>
      </v-card-text>
      <v-card-actions>
        <v-btn
          v-if="singBoxProfile?.sing_box_target"
          color="error"
          variant="text"
          :disabled="busy"
          @click="removeSingBoxTarget"
        >解除绑定</v-btn>
        <v-spacer />
        <v-btn variant="text" @click="singBoxDialog = false">取消</v-btn>
        <v-btn color="primary" :disabled="busy || !canSaveSingBoxTarget" @click="saveSingBoxTarget">保存目标</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>
