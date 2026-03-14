<script setup lang="ts">
import { storeToRefs } from 'pinia'
import { computed, reactive, ref, watch } from 'vue'

import type {
  CompositeTemplatePayload,
  CompositeTemplateRecord,
  TemplatePatchOperation,
  TemplatePatchPayload,
  TemplatePatchRecord,
  TemplatePayload,
  TemplateRecord,
} from '../api'
import { useManagerStore } from '../stores/manager'

type TemplateTab = 'templates' | 'patches' | 'composites'

interface TemplateForm {
  name: string
  content: string
  isDefault: boolean
}

interface TemplatePatchForm {
  name: string
  description: string
  operationsText: string
}

interface CompositeTemplateForm {
  name: string
  baseTemplateId: number | null
  patchSequence: number[]
}

const DEFAULT_TEMPLATE = 'proxies: []\nproxy-groups: []\nrules: []\n'
const DEFAULT_PATCH_OPERATIONS = JSON.stringify(
  [
    {
      op: 'list_append',
      path: 'proxy-groups.0.proxies',
      value: 'DIRECT',
    },
  ],
  null,
  2,
)

const store = useManagerStore()
const {
  busy,
  compositeTemplatePreview,
  compositeTemplatePreviewName,
  compositeTemplates,
  templatePatchPreview,
  templatePatchPreviewName,
  templatePatches,
  templates,
} = storeToRefs(store)

const activeTab = ref<TemplateTab>('templates')

const templateDialog = ref(false)
const templateEditingId = ref<number | null>(null)
const selectedTemplateId = ref<number | null>(null)
const templateForm = reactive<TemplateForm>({
  name: '',
  content: DEFAULT_TEMPLATE,
  isDefault: false,
})

const patchDialog = ref(false)
const patchEditingId = ref<number | null>(null)
const selectedPatchId = ref<number | null>(null)
const patchPreviewTemplateId = ref<number | null>(null)
const patchForm = reactive<TemplatePatchForm>({
  name: '',
  description: '',
  operationsText: DEFAULT_PATCH_OPERATIONS,
})

const compositeDialog = ref(false)
const compositeEditingId = ref<number | null>(null)
const selectedCompositeId = ref<number | null>(null)
const compositeForm = reactive<CompositeTemplateForm>({
  name: '',
  baseTemplateId: null,
  patchSequence: [],
})

const templateHeaders = [
  { title: '名称', key: 'name' },
  { title: '默认', key: 'is_default' },
  { title: '预览', key: 'preview' },
  { title: '操作', key: 'actions', sortable: false, align: 'end' },
] as const

const patchHeaders = [
  { title: '名称', key: 'name' },
  { title: '描述', key: 'description' },
  { title: '操作数', key: 'operation_count' },
  { title: '操作', key: 'actions', sortable: false, align: 'end' },
] as const

const compositeHeaders = [
  { title: '名称', key: 'name' },
  { title: '基础模板', key: 'base_template' },
  { title: '补丁序列', key: 'patches' },
  { title: '操作', key: 'actions', sortable: false, align: 'end' },
] as const

const templateDialogTitle = computed(() => {
  return templateEditingId.value === null ? '新建基础模板' : '编辑基础模板'
})

const patchDialogTitle = computed(() => {
  return patchEditingId.value === null ? '新建模板补丁' : '编辑模板补丁'
})

const compositeDialogTitle = computed(() => {
  return compositeEditingId.value === null ? '新建组合模板' : '编辑组合模板'
})

const canSubmitTemplate = computed(() => {
  return templateForm.name.trim().length > 0 && templateForm.content.trim().length > 0
})

const canSubmitPatch = computed(() => {
  return patchForm.name.trim().length > 0 && patchForm.operationsText.trim().length > 0
})

const canSubmitComposite = computed(() => {
  return compositeForm.name.trim().length > 0 && compositeForm.baseTemplateId !== null
})

const selectedTemplate = computed(() => {
  return templates.value.find((template) => template.id === selectedTemplateId.value) ?? null
})

const selectedPatch = computed(() => {
  return templatePatches.value.find((patch) => patch.id === selectedPatchId.value) ?? null
})

const selectedComposite = computed(() => {
  return compositeTemplates.value.find((composite) => composite.id === selectedCompositeId.value) ?? null
})

watch(
  templates,
  (items) => {
    if (items.length === 0) {
      selectedTemplateId.value = null
      patchPreviewTemplateId.value = null
      if (!compositeDialog.value) {
        compositeForm.baseTemplateId = null
      }
      return
    }

    if (!items.some((template) => template.id === selectedTemplateId.value)) {
      selectedTemplateId.value = items.find((template) => template.is_default)?.id ?? items[0].id
    }

    if (!items.some((template) => template.id === patchPreviewTemplateId.value)) {
      patchPreviewTemplateId.value = items.find((template) => template.is_default)?.id ?? items[0].id
    }

    if (
      compositeForm.baseTemplateId !== null &&
      !items.some((template) => template.id === compositeForm.baseTemplateId)
    ) {
      compositeForm.baseTemplateId = items.find((template) => template.is_default)?.id ?? items[0].id
    }
  },
  { immediate: true },
)

watch(
  templatePatches,
  (items) => {
    if (items.length === 0) {
      selectedPatchId.value = null
      compositeForm.patchSequence = []
      return
    }

    if (!items.some((patch) => patch.id === selectedPatchId.value)) {
      selectedPatchId.value = items[0].id
    }

    compositeForm.patchSequence = compositeForm.patchSequence.filter((patchId) =>
      items.some((patch) => patch.id === patchId),
    )
  },
  { immediate: true },
)

watch(
  compositeTemplates,
  (items) => {
    if (items.length === 0) {
      selectedCompositeId.value = null
      return
    }

    if (!items.some((composite) => composite.id === selectedCompositeId.value)) {
      selectedCompositeId.value = items[0].id
    }
  },
  { immediate: true },
)

function formatOperations(operations: TemplatePatchOperation[]): string {
  return JSON.stringify(operations, null, 2)
}

function parsePatchOperations(raw: string): TemplatePatchOperation[] {
  let parsed: unknown
  try {
    parsed = JSON.parse(raw)
  } catch {
    throw new Error('补丁操作必须是合法 JSON。')
  }

  if (!Array.isArray(parsed)) {
    throw new Error('补丁操作必须是 JSON 数组。')
  }

  return parsed as TemplatePatchOperation[]
}

function resetTemplateForm(): void {
  templateEditingId.value = null
  templateForm.name = ''
  templateForm.content = DEFAULT_TEMPLATE
  templateForm.isDefault = false
}

function openCreateTemplateDialog(): void {
  resetTemplateForm()
  templateDialog.value = true
}

function openEditTemplateDialog(template: TemplateRecord): void {
  templateEditingId.value = template.id
  selectedTemplateId.value = template.id
  templateForm.name = template.name
  templateForm.content = template.content
  templateForm.isDefault = template.is_default
  templateDialog.value = true
}

async function saveTemplate(): Promise<void> {
  const payload: TemplatePayload = {
    name: templateForm.name.trim(),
    content: templateForm.content,
    is_default: templateForm.isDefault,
  }

  const succeeded = templateEditingId.value === null
    ? await store.createTemplate(payload)
    : await store.updateTemplate(templateEditingId.value, payload)

  if (succeeded) {
    templateDialog.value = false
    resetTemplateForm()
  }
}

function resetPatchForm(): void {
  patchEditingId.value = null
  patchForm.name = ''
  patchForm.description = ''
  patchForm.operationsText = DEFAULT_PATCH_OPERATIONS
}

function openCreatePatchDialog(): void {
  resetPatchForm()
  patchDialog.value = true
}

function openEditPatchDialog(patch: TemplatePatchRecord): void {
  patchEditingId.value = patch.id
  selectedPatchId.value = patch.id
  patchForm.name = patch.name
  patchForm.description = patch.description ?? ''
  patchForm.operationsText = formatOperations(patch.operations)
  patchDialog.value = true
}

async function savePatch(): Promise<void> {
  const payload: TemplatePatchPayload = {
    name: patchForm.name.trim(),
    description: patchForm.description.trim() || null,
    operations: parsePatchOperations(patchForm.operationsText),
  }

  const succeeded = patchEditingId.value === null
    ? await store.createTemplatePatch(payload)
    : await store.updateTemplatePatch(patchEditingId.value, payload)

  if (succeeded) {
    patchDialog.value = false
    resetPatchForm()
  }
}

async function previewPatch(): Promise<void> {
  if (selectedPatchId.value === null || patchPreviewTemplateId.value === null) {
    store.showError('请选择要预览的补丁和基础模板。')
    return
  }

  await store.previewTemplatePatch(selectedPatchId.value, patchPreviewTemplateId.value)
}

function resetCompositeForm(): void {
  compositeEditingId.value = null
  compositeForm.name = ''
  compositeForm.baseTemplateId = templates.value.find((template) => template.is_default)?.id ?? templates.value[0]?.id ?? null
  compositeForm.patchSequence = []
}

function openCreateCompositeDialog(): void {
  resetCompositeForm()
  compositeDialog.value = true
}

function openEditCompositeDialog(composite: CompositeTemplateRecord): void {
  compositeEditingId.value = composite.id
  selectedCompositeId.value = composite.id
  compositeForm.name = composite.name
  compositeForm.baseTemplateId = composite.base_template_id
  compositeForm.patchSequence = [...composite.patch_sequence]
  compositeDialog.value = true
}

async function saveComposite(): Promise<void> {
  if (compositeForm.baseTemplateId === null) {
    store.showError('请选择基础模板。')
    return
  }

  const payload: CompositeTemplatePayload = {
    name: compositeForm.name.trim(),
    base_template_id: compositeForm.baseTemplateId,
    patch_sequence: [...compositeForm.patchSequence],
  }

  const succeeded = compositeEditingId.value === null
    ? await store.createCompositeTemplate(payload)
    : await store.updateCompositeTemplate(compositeEditingId.value, payload)

  if (succeeded) {
    compositeDialog.value = false
    resetCompositeForm()
  }
}

async function previewCompositeDraft(): Promise<void> {
  if (compositeForm.baseTemplateId === null) {
    store.showError('请选择基础模板。')
    return
  }

  await store.previewCompositeTemplate({
    name: compositeForm.name.trim(),
    base_template_id: compositeForm.baseTemplateId,
    patch_sequence: [...compositeForm.patchSequence],
  })
}
</script>

<template>
  <v-row>
    <v-col cols="12">
      <v-card>
        <v-tabs v-model="activeTab" color="primary">
          <v-tab value="templates">基础模板</v-tab>
          <v-tab value="patches">模板补丁</v-tab>
          <v-tab value="composites">组合模板</v-tab>
        </v-tabs>
      </v-card>
    </v-col>

    <template v-if="activeTab === 'templates'">
      <v-col cols="12" lg="7">
        <v-card>
          <v-card-item>
            <div class="d-flex flex-column flex-sm-row ga-4 align-sm-center justify-space-between">
              <div>
                <v-card-title class="px-0">基础模板管理</v-card-title>
                <v-card-subtitle class="px-0">基础模板保存原始 Clash YAML，供预览、合并和组合模板复用。</v-card-subtitle>
              </div>
              <v-btn color="primary" prepend-icon="mdi-plus" @click="openCreateTemplateDialog">新建基础模板</v-btn>
            </div>
          </v-card-item>

          <v-data-table :headers="templateHeaders" :items="templates" item-value="id">
            <template #item.is_default="{ item }">
              <v-chip :color="item.is_default ? 'primary' : 'default'" size="small" variant="tonal">
                {{ item.is_default ? '默认模板' : '普通模板' }}
              </v-chip>
            </template>

            <template #item.preview="{ item }">
              <div class="text-caption text-medium-emphasis preview-ellipsis py-2">
                {{ item.content }}
              </div>
            </template>

            <template #item.actions="{ item }">
              <div class="d-flex justify-end ga-2 py-2">
                <v-btn icon="mdi-eye-outline" size="small" variant="text" @click="selectedTemplateId = item.id" />
                <v-btn icon="mdi-pencil" size="small" variant="text" @click="openEditTemplateDialog(item)" />
                <v-btn icon="mdi-delete-outline" size="small" variant="text" color="error" @click="store.deleteTemplate(item.id)" />
              </div>
            </template>
          </v-data-table>
        </v-card>
      </v-col>

      <v-col cols="12" lg="5">
        <v-card class="fill-height">
          <v-card-item>
            <v-card-title class="px-0">基础模板预览</v-card-title>
            <v-card-subtitle class="px-0">{{ selectedTemplate?.name ?? '尚未选择基础模板' }}</v-card-subtitle>
          </v-card-item>
          <v-card-text>
            <v-sheet class="preview-panel" color="surface-variant" rounded="xl">
              <pre>{{ selectedTemplate?.content ?? '从左侧列表选择一个基础模板，即可在这里查看完整 YAML。' }}</pre>
            </v-sheet>
          </v-card-text>
        </v-card>
      </v-col>
    </template>

    <template v-else-if="activeTab === 'patches'">
      <v-col cols="12" lg="7">
        <v-card>
          <v-card-item>
            <div class="d-flex flex-column flex-sm-row ga-4 align-sm-center justify-space-between">
              <div>
                <v-card-title class="px-0">模板补丁管理</v-card-title>
                <v-card-subtitle class="px-0">补丁以最小操作序列修改模板内容，顺序会被严格保留。</v-card-subtitle>
              </div>
              <v-btn color="primary" prepend-icon="mdi-plus" @click="openCreatePatchDialog">新建模板补丁</v-btn>
            </div>
          </v-card-item>

          <v-data-table :headers="patchHeaders" :items="templatePatches" item-value="id">
            <template #item.description="{ item }">
              <span class="text-medium-emphasis">{{ item.description || '无描述' }}</span>
            </template>

            <template #item.operation_count="{ item }">
              <v-chip size="small" variant="tonal">{{ item.operations.length }} 个操作</v-chip>
            </template>

            <template #item.actions="{ item }">
              <div class="d-flex justify-end ga-2 py-2">
                <v-btn icon="mdi-eye-outline" size="small" variant="text" @click="selectedPatchId = item.id" />
                <v-btn icon="mdi-pencil" size="small" variant="text" @click="openEditPatchDialog(item)" />
                <v-btn icon="mdi-delete-outline" size="small" variant="text" color="error" @click="store.deleteTemplatePatch(item.id)" />
              </div>
            </template>
          </v-data-table>
        </v-card>
      </v-col>

      <v-col cols="12" lg="5">
        <v-card class="mb-4">
          <v-card-item>
            <v-card-title class="px-0">补丁详情</v-card-title>
            <v-card-subtitle class="px-0">{{ selectedPatch?.name ?? '尚未选择模板补丁' }}</v-card-subtitle>
          </v-card-item>
          <v-card-text class="d-flex flex-column ga-4">
            <v-select
              v-model="patchPreviewTemplateId"
              :items="templates"
              item-title="name"
              item-value="id"
              label="预览使用的基础模板"
              :disabled="templates.length === 0"
            />
            <v-btn
              color="primary"
              :disabled="busy || selectedPatchId === null || patchPreviewTemplateId === null"
              @click="previewPatch"
            >
              预览补丁效果
            </v-btn>
            <v-sheet class="preview-panel" color="surface-variant" rounded="xl">
              <pre>{{ selectedPatch ? formatOperations(selectedPatch.operations) : '从左侧选择模板补丁查看操作 JSON。' }}</pre>
            </v-sheet>
          </v-card-text>
        </v-card>

        <v-card class="fill-height">
          <v-card-item>
            <v-card-title class="px-0">补丁预览结果</v-card-title>
            <v-card-subtitle class="px-0">{{ templatePatchPreviewName || '点击“预览补丁效果”后会显示在这里。' }}</v-card-subtitle>
          </v-card-item>
          <v-card-text>
            <v-sheet class="preview-panel" color="surface-variant" rounded="xl">
              <pre>{{ templatePatchPreview || '尚未生成模板补丁预览。' }}</pre>
            </v-sheet>
          </v-card-text>
        </v-card>
      </v-col>
    </template>

    <template v-else>
      <v-col cols="12" lg="7">
        <v-card>
          <v-card-item>
            <div class="d-flex flex-column flex-sm-row ga-4 align-sm-center justify-space-between">
              <div>
                <v-card-title class="px-0">组合模板管理</v-card-title>
                <v-card-subtitle class="px-0">组合模板把基础模板和补丁序列固化成可复用结果，并缓存最终 YAML。</v-card-subtitle>
              </div>
              <v-btn color="primary" prepend-icon="mdi-plus" @click="openCreateCompositeDialog">新建组合模板</v-btn>
            </div>
          </v-card-item>

          <v-data-table :headers="compositeHeaders" :items="compositeTemplates" item-value="id">
            <template #item.base_template="{ item }">
              <v-chip size="small" variant="tonal">{{ item.base_template.name }}</v-chip>
            </template>

            <template #item.patches="{ item }">
              <div class="d-flex flex-wrap ga-2 py-2">
                <v-chip v-for="patch in item.patches" :key="patch.id" size="small" variant="tonal">
                  {{ patch.name }}
                </v-chip>
                <span v-if="item.patches.length === 0" class="text-caption text-medium-emphasis">无补丁</span>
              </div>
            </template>

            <template #item.actions="{ item }">
              <div class="d-flex justify-end ga-2 py-2">
                <v-btn icon="mdi-eye-outline" size="small" variant="text" @click="selectedCompositeId = item.id" />
                <v-btn icon="mdi-pencil" size="small" variant="text" @click="openEditCompositeDialog(item)" />
                <v-btn icon="mdi-delete-outline" size="small" variant="text" color="error" @click="store.deleteCompositeTemplate(item.id)" />
              </div>
            </template>
          </v-data-table>
        </v-card>
      </v-col>

      <v-col cols="12" lg="5">
        <v-card class="mb-4">
          <v-card-item>
            <v-card-title class="px-0">组合模板缓存结果</v-card-title>
            <v-card-subtitle class="px-0">{{ selectedComposite?.name ?? '尚未选择组合模板' }}</v-card-subtitle>
          </v-card-item>
          <v-card-text>
            <v-sheet class="preview-panel" color="surface-variant" rounded="xl">
              <pre>{{ selectedComposite?.cached_content ?? '从左侧选择组合模板，即可在这里查看缓存结果。' }}</pre>
            </v-sheet>
          </v-card-text>
        </v-card>

        <v-card class="fill-height">
          <v-card-item>
            <v-card-title class="px-0">组合模板草稿预览</v-card-title>
            <v-card-subtitle class="px-0">{{ compositeTemplatePreviewName || '在编辑对话框中点击“预览”后会显示在这里。' }}</v-card-subtitle>
          </v-card-item>
          <v-card-text>
            <v-sheet class="preview-panel" color="surface-variant" rounded="xl">
              <pre>{{ compositeTemplatePreview || '尚未生成组合模板预览。' }}</pre>
            </v-sheet>
          </v-card-text>
        </v-card>
      </v-col>
    </template>
  </v-row>

  <v-dialog v-model="templateDialog">
    <v-card>
      <v-card-item>
        <v-card-title>{{ templateDialogTitle }}</v-card-title>
        <v-card-subtitle>基础模板内容必须是合法 YAML 映射，组合模板会以它为起点。</v-card-subtitle>
      </v-card-item>

      <v-card-text>
        <v-row>
          <v-col cols="12" md="8">
            <v-text-field v-model="templateForm.name" label="模板名称" maxlength="255" />
          </v-col>
          <v-col cols="12" md="4">
            <v-switch v-model="templateForm.isDefault" label="设为默认" hide-details />
          </v-col>
          <v-col cols="12">
            <v-textarea v-model="templateForm.content" label="YAML 内容" rows="18" />
          </v-col>
        </v-row>
      </v-card-text>

      <v-card-actions>
        <v-spacer />
        <v-btn variant="text" @click="templateDialog = false">取消</v-btn>
        <v-btn color="primary" :disabled="busy || !canSubmitTemplate" @click="saveTemplate">保存</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>

  <v-dialog v-model="patchDialog">
    <v-card>
      <v-card-item>
        <v-card-title>{{ patchDialogTitle }}</v-card-title>
        <v-card-subtitle>补丁操作使用 JSON 数组表示，内容会按顺序逐条执行。</v-card-subtitle>
      </v-card-item>

      <v-card-text>
        <v-row>
          <v-col cols="12" md="8">
            <v-text-field v-model="patchForm.name" label="补丁名称" maxlength="255" />
          </v-col>
          <v-col cols="12" md="4">
            <v-text-field v-model="patchForm.description" label="描述" maxlength="255" />
          </v-col>
          <v-col cols="12">
            <v-textarea v-model="patchForm.operationsText" label="操作 JSON" rows="16" auto-grow />
          </v-col>
        </v-row>
      </v-card-text>

      <v-card-actions>
        <v-spacer />
        <v-btn variant="text" @click="patchDialog = false">取消</v-btn>
        <v-btn color="primary" :disabled="busy || !canSubmitPatch" @click="savePatch">保存</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>

  <v-dialog v-model="compositeDialog">
    <v-card>
      <v-card-item>
        <v-card-title>{{ compositeDialogTitle }}</v-card-title>
        <v-card-subtitle>选择基础模板和补丁顺序，系统会按当前顺序生成并缓存最终结果。</v-card-subtitle>
      </v-card-item>

      <v-card-text>
        <v-row>
          <v-col cols="12">
            <v-text-field v-model="compositeForm.name" label="组合模板名称" maxlength="255" />
          </v-col>
          <v-col cols="12">
            <v-select
              v-model="compositeForm.baseTemplateId"
              :items="templates"
              item-title="name"
              item-value="id"
              label="基础模板"
            />
          </v-col>
          <v-col cols="12">
            <v-autocomplete
              v-model="compositeForm.patchSequence"
              :items="templatePatches"
              item-title="name"
              item-value="id"
              label="补丁序列（按选择顺序）"
              chips
              multiple
            />
          </v-col>
        </v-row>
      </v-card-text>

      <v-card-actions>
        <v-spacer />
        <v-btn variant="text" :disabled="busy || compositeForm.baseTemplateId === null" @click="previewCompositeDraft">预览</v-btn>
        <v-btn variant="text" @click="compositeDialog = false">取消</v-btn>
        <v-btn color="primary" :disabled="busy || !canSubmitComposite" @click="saveComposite">保存</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<style scoped>
.preview-ellipsis {
  display: -webkit-box;
  overflow: hidden;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 3;
}

.preview-panel {
  max-height: 28rem;
  overflow: auto;
  padding: 1rem;
}

.preview-panel pre {
  white-space: pre-wrap;
  word-break: break-word;
}
</style>
