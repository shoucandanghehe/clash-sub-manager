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
import MonacoJsonEditor from '../components/MonacoJsonEditor.vue'
import SegmentedPicker from '../components/SegmentedPicker.vue'
import StructuredValueEditor from '../components/StructuredValueEditor.vue'
import TemplatePathTree from '../components/TemplatePathTree.vue'
import {
  createStructuredValueNode,
  setStructuredValueKind,
  structuredValueNodeFromUnknown,
  structuredValueNodeToUnknown,
  type StructuredValueFactory,
  type StructuredValueNode,
} from '../components/structuredValue'
import { useManagerStore } from '../stores/manager'
import {
  buildTemplatePathContext,
  buildTemplatePathTree,
  filterTemplatePathTree,
  parseTemplateDocument,
  resolveTemplatePath,
  type TemplatePathContext,
  type TemplatePathResolution,
} from '../utils/templatePath'

type TemplateTab = 'templates' | 'patches' | 'composites'
type PatchOperationKind = TemplatePatchOperation['op']

interface TemplateForm {
  name: string
  content: string
  isDefault: boolean
}

interface TemplatePatchForm {
  name: string
  description: string
  operations: LowCodePatchOperationRow[]
}

interface CompositeTemplateForm {
  name: string
  baseTemplateId: number | null
  patchSequence: number[]
}

interface LowCodePatchOperationRow {
  id: number
  op: PatchOperationKind
  path: string
  valueEditor: StructuredValueNode
  indexText: string
  useOldValue: boolean
  oldValueEditor: StructuredValueNode
}

interface PatchOperationOption {
  title: string
  value: PatchOperationKind
  description: string
}

const DEFAULT_TEMPLATE = 'proxies: []\nproxy-groups: []\nrules: []\n'

const PATCH_OPERATION_OPTIONS: PatchOperationOption[] = [
  { value: 'set', title: 'set', description: '替换指定路径的值' },
  { value: 'delete', title: 'delete', description: '删除指定路径的值' },
  { value: 'merge', title: 'merge', description: '向对象做深度合并' },
  { value: 'list_append', title: 'list_append', description: '向列表末尾追加元素' },
  { value: 'list_insert', title: 'list_insert', description: '向列表指定位置插入元素' },
  { value: 'list_remove', title: 'list_remove', description: '按索引从列表移除元素' },
  { value: 'list_replace', title: 'list_replace', description: '替换列表指定下标元素' },
]

const VALUE_REQUIRED_OPERATIONS = new Set<PatchOperationKind>([
  'set',
  'merge',
  'list_append',
  'list_insert',
  'list_replace',
])
const INDEX_REQUIRED_OPERATIONS = new Set<PatchOperationKind>(['list_insert', 'list_remove', 'list_replace'])

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
const nextPatchOperationId = ref(1)
const valueFactory: StructuredValueFactory = {
  nextId: () => nextPatchOperationId.value++,
}

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
const patchAuthoringTemplateId = ref<number | null>(null)
const activePatchOperationId = ref<number | null>(null)
const pathPickerDialog = ref(false)
const pathPickerSearch = ref('')
const collapsedTreePaths = ref<string[]>([])
const expandedContextOperationIds = ref<number[]>([])
const patchEditorTab = ref<'lowCode' | 'json'>('lowCode')
const patchJsonText = ref('[]')
const patchJsonError = ref('')
const patchEditorSyncing = ref(false)
const suppressPatchJsonSync = ref(false)
const patchForm = reactive<TemplatePatchForm>({
  name: '',
  description: '',
  operations: [],
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

const patchValidationMessage = computed(() => {
  try {
    buildPatchOperationsFromForm()
    return ''
  } catch (caught) {
    return caught instanceof Error ? caught.message : '补丁配置无效。'
  }
})

const canSubmitPatch = computed(() => {
  return patchForm.name.trim().length > 0 && patchValidationMessage.value === '' && patchJsonError.value === ''
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

const patchAuthoringTemplate = computed(() => {
  return templates.value.find((template) => template.id === patchAuthoringTemplateId.value) ?? null
})

const patchAuthoringDocument = computed(() => {
  if (!patchAuthoringTemplate.value) {
    return null
  }

  try {
    return parseTemplateDocument(patchAuthoringTemplate.value.content)
  } catch (caught) {
    return caught instanceof Error ? caught.message : '模板解析失败。'
  }
})

const patchPathPreviews = computed<Record<number, TemplatePathResolution>>(() => {
  const documentOrError = patchAuthoringDocument.value
  if (!documentOrError) {
    return Object.fromEntries(
      patchForm.operations.map((operation) => [
        operation.id,
        {
          ok: false,
          message: '请选择一个目标模板以校验路径。',
        },
      ]),
    )
  }

  if (typeof documentOrError === 'string') {
    return Object.fromEntries(
      patchForm.operations.map((operation) => [
        operation.id,
        {
          ok: false,
          message: documentOrError,
        },
      ]),
    )
  }

  return Object.fromEntries(
    patchForm.operations.map((operation) => [operation.id, resolveTemplatePath(documentOrError, operation.path)]),
  )
})

const patchPathContexts = computed<Record<number, TemplatePathContext>>(() => {
  const template = patchAuthoringTemplate.value
  if (!template) {
    return Object.fromEntries(
      patchForm.operations.map((operation) => [operation.id, { matchedLineNumber: null, lines: [] }]),
    )
  }

  return Object.fromEntries(
    patchForm.operations.map((operation) => [
      operation.id,
      buildTemplatePathContext(
        template.content,
        operation.path,
        patchPathPreviews.value[operation.id]?.matchedValue,
      ),
    ]),
  )
})

const patchTreeNodes = computed(() => {
  const documentOrError = patchAuthoringDocument.value
  if (!documentOrError || typeof documentOrError === 'string') {
    return []
  }
  return buildTemplatePathTree(documentOrError)
})

const filteredPatchTreeNodes = computed(() => {
  return filterTemplatePathTree(patchTreeNodes.value, pathPickerSearch.value)
})
const patchPathSuggestions = computed(() => {
  return collectTemplatePaths(patchTreeNodes.value)
})



const patchPathEntries = computed<TemplatePathEntry[]>(() => {
  const documentOrError = patchAuthoringDocument.value
  if (!documentOrError || typeof documentOrError === 'string') {
    return []
  }
  return buildTemplatePathEntries(documentOrError)
})


const activePatchOperation = computed(() => {
  return patchForm.operations.find((operation) => operation.id === activePatchOperationId.value) ?? null
})
watch(
  templates,
  (items) => {
    if (items.length === 0) {
      selectedTemplateId.value = null
      patchPreviewTemplateId.value = null
      patchAuthoringTemplateId.value = null
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

    if (!items.some((template) => template.id === patchAuthoringTemplateId.value)) {
      patchAuthoringTemplateId.value = items.find((template) => template.is_default)?.id ?? items[0].id
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

function collectExpandableTreePaths(nodes: Array<{ path: string; children: Array<{ path: string; children: unknown[] }> }>): string[] {
  const paths: string[] = []

  function visit(entries: Array<{ path: string; children: Array<{ path: string; children: unknown[] }> }>): void {
    for (const entry of entries) {
      if (entry.children.length > 0) {
        paths.push(entry.path)
        visit(entry.children as Array<{ path: string; children: Array<{ path: string; children: unknown[] }> }>)
      }
    }
  }

  visit(nodes)
  return paths
}


function requiresValue(op: PatchOperationKind): boolean {
  return VALUE_REQUIRED_OPERATIONS.has(op)
}

function requiresIndex(op: PatchOperationKind): boolean {
  return INDEX_REQUIRED_OPERATIONS.has(op)
}

function collectTemplatePaths(nodes: Array<{ path: string; children: Array<{ path: string; children: unknown[] }> }>): string[] {
  const paths: string[] = []

  function visit(entries: Array<{ path: string; children: Array<{ path: string; children: unknown[] }> }>): void {
    for (const entry of entries) {
      paths.push(entry.path)
      visit(entry.children as Array<{ path: string; children: Array<{ path: string; children: unknown[] }> }>)
    }
  }

  visit(nodes)
  return paths
}


function normalizePatchOperation(value: unknown, index: number): TemplatePatchOperation {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    throw new Error(`第 ${index + 1} 条 JSON 操作必须是对象。`)
  }

  const candidate = value as Record<string, unknown>
  if (typeof candidate.op !== 'string') {
    throw new Error(`第 ${index + 1} 条 JSON 操作缺少字符串类型的 op。`)
  }
  if (typeof candidate.path !== 'string') {
    throw new Error(`第 ${index + 1} 条 JSON 操作缺少字符串类型的 path。`)
  }

  const operation: TemplatePatchOperation = {
    op: candidate.op as PatchOperationKind,
    path: candidate.path,
  }

  if ('value' in candidate) {
    operation.value = candidate.value
  }
  if (typeof candidate.index === 'number') {
    operation.index = candidate.index
  }
  if ('old_value' in candidate) {
    operation.old_value = candidate.old_value
  }
  return operation
}

function parsePatchOperationsJson(raw: string): TemplatePatchOperation[] {
  let parsed: unknown
  try {
    parsed = JSON.parse(raw)
  } catch {
    throw new Error('原生 JSON 不是合法 JSON。')
  }

  if (!Array.isArray(parsed)) {
    throw new Error('原生 JSON 必须是操作数组。')
  }

  return parsed.map((entry, index) => normalizePatchOperation(entry, index))
}

function syncPatchJsonFromLowCode(): void {
  try {
    patchEditorSyncing.value = true
    patchJsonText.value = JSON.stringify(buildPatchOperationsFromForm(), null, 2)
    patchJsonError.value = ''
  } catch (caught) {
    patchJsonError.value = caught instanceof Error ? caught.message : '补丁配置无效。'
  } finally {
    patchEditorSyncing.value = false
  }
}

function setLowCodeOperations(operations: TemplatePatchOperation[]): void {
  patchForm.operations = operations.map((operation) => patchRowFromOperation(operation))
  activePatchOperationId.value = patchForm.operations[0]?.id ?? null
}

function handlePatchJsonInput(value: string): void {
  patchJsonText.value = value
  if (patchEditorSyncing.value) {
    return
  }

  try {
    parsePatchOperationsJson(value)
    patchJsonError.value = ''
  } catch (caught) {
    patchJsonError.value = caught instanceof Error ? caught.message : '原生 JSON 无法解析。'
  }
}
function formatPatchJson(): void {
  try {
    const operations = parsePatchOperationsJson(patchJsonText.value)
    suppressPatchJsonSync.value = true
    setLowCodeOperations(operations)
    patchJsonError.value = ''
    syncPatchJsonFromLowCode()
  } catch (caught) {
    patchJsonError.value = caught instanceof Error ? caught.message : '原生 JSON 无法解析。'
    store.showError(patchJsonError.value)
  } finally {
    suppressPatchJsonSync.value = false
  }
}



watch(
  patchEditorTab,
  (tab, previousTab) => {
    if (tab === previousTab) {
      return
    }

    if (tab === 'json') {
      syncPatchJsonFromLowCode()
      return
    }

    if (previousTab === 'json') {
      try {
        const operations = parsePatchOperationsJson(patchJsonText.value)
        suppressPatchJsonSync.value = true
        setLowCodeOperations(operations)
        patchJsonError.value = ''
      } catch (caught) {
        patchJsonError.value = caught instanceof Error ? caught.message : '原生 JSON 无法解析。'
        patchEditorSyncing.value = true
        patchEditorTab.value = 'json'
        patchEditorSyncing.value = false
      } finally {
        suppressPatchJsonSync.value = false
      }
    }
  },
  { flush: 'sync' },
)


function operationDescription(op: PatchOperationKind): string {
  return PATCH_OPERATION_OPTIONS.find((option) => option.value === op)?.description ?? ''
}

function defaultValueNodeForOperation(op: PatchOperationKind): StructuredValueNode {
  return createStructuredValueNode(valueFactory, op === 'merge' ? 'object' : 'string')
}

function patchRowFromOperation(operation: TemplatePatchOperation): LowCodePatchOperationRow {
  return {
    id: nextPatchOperationId.value++,
    op: operation.op,
    path: operation.path,
    valueEditor: 'value' in operation ? structuredValueNodeFromUnknown(valueFactory, operation.value) : defaultValueNodeForOperation(operation.op),
    indexText: typeof operation.index === 'number' ? String(operation.index) : '',
    useOldValue: 'old_value' in operation,
    oldValueEditor: 'old_value' in operation ? structuredValueNodeFromUnknown(valueFactory, operation.old_value) : createStructuredValueNode(valueFactory),
  }
}

function formatOperations(operations: TemplatePatchOperation[]): string {
  return JSON.stringify(operations, null, 2)
}

function pathPreviewFor(operationId: number): TemplatePathResolution {
  return patchPathPreviews.value[operationId] ?? {
    ok: false,
    message: '路径预览不可用。',
  }
}

function pathContextFor(operationId: number): TemplatePathContext {
  return patchPathContexts.value[operationId] ?? {
    matchedLineNumber: null,
    matchedBlockStartLineNumber: null,
    matchedBlockEndLineNumber: null,
    isCollectionMatch: false,
    lines: [],
  }
}

function isContextExpanded(operationId: number): boolean {
  return expandedContextOperationIds.value.includes(operationId)
}

function expandContext(operationId: number): void {
  if (!expandedContextOperationIds.value.includes(operationId)) {
    expandedContextOperationIds.value = [...expandedContextOperationIds.value, operationId]
  }
}

function collapseContext(operationId: number): void {
  expandedContextOperationIds.value = expandedContextOperationIds.value.filter((id) => id !== operationId)
}

function visibleContextLines(operationId: number): TemplatePathContext['lines'] {
  const context = pathContextFor(operationId)
  if (!context.isCollectionMatch || !context.matchedBlockStartLineNumber || !context.matchedBlockEndLineNumber) {
    return context.lines
  }

  const matchedLines = context.matchedBlockEndLineNumber - context.matchedBlockStartLineNumber + 1
  if (matchedLines <= 8 || isContextExpanded(operationId)) {
    return context.lines
  }

  const headCutoff = context.matchedBlockStartLineNumber + 2
  const tailStart = context.matchedBlockEndLineNumber - 2

  return context.lines.filter((line) => line.lineNumber <= headCutoff || line.lineNumber >= tailStart)
}

function hiddenContextLineCount(operationId: number): number {
  const context = pathContextFor(operationId)
  if (!context.isCollectionMatch || !context.matchedBlockStartLineNumber || !context.matchedBlockEndLineNumber) {
    return 0
  }

  const matchedLines = context.matchedBlockEndLineNumber - context.matchedBlockStartLineNumber + 1
  if (matchedLines <= 8) {
    return 0
  }
  return matchedLines - 6
}

function foldedTailStartLine(operationId: number): number | null {
  const context = pathContextFor(operationId)
  if (!context.isCollectionMatch || !context.matchedBlockEndLineNumber) {
    return null
  }
  if (hiddenContextLineCount(operationId) === 0) {
    return null
  }
  return context.matchedBlockEndLineNumber - 2
}

function shouldShowContextFoldBefore(operationId: number, lineNumber: number): boolean {
  const tailStart = foldedTailStartLine(operationId)
  if (tailStart === null || isContextExpanded(operationId)) {
    return false
  }
  return lineNumber === tailStart
}

function shouldShowContextCollapseAfter(operationId: number, lineNumber: number): boolean {
  const context = pathContextFor(operationId)
  if (!context.isCollectionMatch || !context.matchedBlockEndLineNumber) {
    return false
  }
  if (!isContextExpanded(operationId) || hiddenContextLineCount(operationId) === 0) {
    return false
  }
  return lineNumber === context.matchedBlockEndLineNumber
}

function createPatchOperationRow(op: PatchOperationKind = 'list_append'): LowCodePatchOperationRow {
  const row: LowCodePatchOperationRow = {
    id: nextPatchOperationId.value++,
    op,
    path: '',
    valueEditor: defaultValueNodeForOperation(op),
    indexText: '',
    useOldValue: false,
    oldValueEditor: createStructuredValueNode(valueFactory),
  }
  applyPatchOperationDefaults(row, op)
  return row
}

function applyPatchOperationDefaults(row: LowCodePatchOperationRow, nextOp: PatchOperationKind): void {
  row.op = nextOp

  if (nextOp === 'merge' && row.valueEditor.kind !== 'object') {
    setStructuredValueKind(row.valueEditor, valueFactory, 'object')
  }

  if (!requiresIndex(nextOp)) {
    row.indexText = ''
  } else if (!row.indexText.trim()) {
    row.indexText = '0'
  }

  if (nextOp !== 'list_remove' && nextOp !== 'list_replace') {
    row.useOldValue = false
    row.oldValueEditor = createStructuredValueNode(valueFactory)
  }
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

function buildPatchOperationsFromForm(): TemplatePatchOperation[] {
  return patchForm.operations.map((row, index) => {
    const rowNumber = index + 1
    const path = row.path.trim()
    if (!path) {
      throw new Error(`第 ${rowNumber} 条操作缺少 path。`)
    }

    const operation: TemplatePatchOperation = {
      op: row.op,
      path,
    }

    if (requiresValue(row.op)) {
      operation.value = structuredValueNodeToUnknown(row.valueEditor, `第 ${rowNumber} 条操作的 value`)
    }

    if (requiresIndex(row.op)) {
      const indexText = row.indexText.trim()
      if (!indexText) {
        throw new Error(`第 ${rowNumber} 条操作缺少 index。`)
      }
      if (!/^\d+$/.test(indexText)) {
        throw new Error(`第 ${rowNumber} 条操作的 index 必须是非负整数。`)
      }
      operation.index = Number(indexText)
    }

    if ((row.op === 'list_remove' || row.op === 'list_replace') && row.useOldValue) {
      operation.old_value = structuredValueNodeToUnknown(row.oldValueEditor, `第 ${rowNumber} 条操作的 old_value`)
    }

    return operation
  })
}

function resetPatchForm(): void {
  patchEditingId.value = null
  patchEditorTab.value = 'lowCode'
  patchForm.name = ''
  patchForm.description = ''
  patchForm.operations = [createPatchOperationRow()]
  activePatchOperationId.value = patchForm.operations[0]?.id ?? null
  patchAuthoringTemplateId.value = templates.value.find((template) => template.is_default)?.id ?? templates.value[0]?.id ?? null
  expandedContextOperationIds.value = []
  patchJsonError.value = ''
  syncPatchJsonFromLowCode()
}

function addPatchOperation(op: PatchOperationKind = 'list_append'): void {
  const operation = createPatchOperationRow(op)
  patchForm.operations.push(operation)
  activePatchOperationId.value = operation.id
}

function removePatchOperation(index: number): void {
  const removedId = patchForm.operations[index]?.id ?? null
  patchForm.operations.splice(index, 1)
  if (removedId !== null && activePatchOperationId.value === removedId) {
    activePatchOperationId.value = patchForm.operations[index]?.id ?? patchForm.operations[index - 1]?.id ?? null
  }
}

function movePatchOperation(index: number, direction: -1 | 1): void {
  const targetIndex = index + direction
  if (targetIndex < 0 || targetIndex >= patchForm.operations.length) {
    return
  }

  const [row] = patchForm.operations.splice(index, 1)
  patchForm.operations.splice(targetIndex, 0, row)
}

function updatePatchOperationKind(row: LowCodePatchOperationRow, op: PatchOperationKind): void {
  applyPatchOperationDefaults(row, op)
}

function openCreatePatchDialog(): void {
  resetPatchForm()
  patchDialog.value = true
}

function openEditPatchDialog(patch: TemplatePatchRecord): void {
  patchEditingId.value = patch.id
  patchEditorTab.value = 'lowCode'
  selectedPatchId.value = patch.id
  patchForm.name = patch.name
  patchForm.description = patch.description ?? ''
  setLowCodeOperations(patch.operations)
  patchAuthoringTemplateId.value = templates.value.find((template) => template.is_default)?.id ?? templates.value[0]?.id ?? null
  expandedContextOperationIds.value = []
  patchJsonError.value = ''
  syncPatchJsonFromLowCode()
  patchDialog.value = true
}

function setActivePatchOperation(operationId: number): void {
  activePatchOperationId.value = operationId
}

function applyTreePathToActiveOperation(path: string): void {
  if (!activePatchOperation.value) {
    store.showError('请先选择一个补丁操作，再从树中填充路径。')
    return
  }
  activePatchOperation.value.path = path
  pathPickerDialog.value = false
}

function toggleCollapsedTreePath(path: string): void {
  const next = new Set(collapsedTreePaths.value)
  if (next.has(path)) {
    next.delete(path)
  } else {
    next.add(path)
  }
  collapsedTreePaths.value = [...next]
}

function openPathPicker(operationId: number): void {
  setActivePatchOperation(operationId)
  pathPickerSearch.value = ''
  collapsedTreePaths.value = collectExpandableTreePaths(patchTreeNodes.value)
  pathPickerDialog.value = true
}

function closePathPicker(): void {
  pathPickerDialog.value = false
  pathPickerSearch.value = ''
}

async function savePatch(): Promise<void> {
  if (patchJsonError.value) {
    store.showError(patchJsonError.value)
    return
  }

  let operations: TemplatePatchOperation[]
  try {
    operations = parsePatchOperationsJson(patchJsonText.value)
    suppressPatchJsonSync.value = true
    setLowCodeOperations(operations)
  } catch (caught) {
    store.showError(caught instanceof Error ? caught.message : '原生 JSON 无法解析。')
    return
  } finally {
    suppressPatchJsonSync.value = false
  }

  const payload: TemplatePatchPayload = {
    name: patchForm.name.trim(),
    description: patchForm.description.trim() || null,
    operations,
  }
  const succeeded = patchEditingId.value === null
    ? await store.createTemplatePatch(payload)
    : await store.updateTemplatePatch(patchEditingId.value, payload)

  if (succeeded) {
    syncPatchJsonFromLowCode()
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
              <pre>{{ selectedPatch ? formatOperations(selectedPatch.operations) : '从左侧选择模板补丁查看生成后的 JSON。' }}</pre>
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
            <v-card-title class="px-0">组合模板结果</v-card-title>
            <v-card-subtitle class="px-0">{{ selectedComposite?.name ?? '尚未选择组合模板' }}</v-card-subtitle>
          </v-card-item>
          <v-card-text>
            <v-sheet class="preview-panel" color="surface-variant" rounded="xl">
              <pre>{{ selectedComposite?.cached_content ?? '从左侧选择组合模板，即可在这里查看结果。' }}</pre>
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

  <v-dialog v-model="patchDialog" max-width="1200">
    <v-card>
      <v-card-item>
        <v-card-title>{{ patchDialogTitle }}</v-card-title>
      </v-card-item>

      <v-card-text>
        <v-row>
          <v-col cols="12" md="5">
            <v-text-field v-model="patchForm.name" label="补丁名称" maxlength="255" />
          </v-col>
          <v-col cols="12" md="3">
            <v-text-field v-model="patchForm.description" label="描述" maxlength="255" />
          </v-col>
          <v-col cols="12" md="4">
            <v-select
              v-model="patchAuthoringTemplateId"
              :items="templates"
              item-title="name"
              item-value="id"
              label="路径参考模板"
              :disabled="templates.length === 0"
            />
          </v-col>
          <v-col cols="12">
            <v-tabs v-model="patchEditorTab" color="primary" class="mb-4">
              <v-tab value="lowCode">低代码编辑</v-tab>
              <v-tab value="json">原生 JSON 编辑</v-tab>
            </v-tabs>

            <v-window v-model="patchEditorTab">
              <v-window-item value="lowCode">
                <div class="d-flex flex-column flex-sm-row ga-3 align-sm-center justify-space-between mb-3">
                  <div>
                    <div class="text-subtitle-1 font-weight-medium">补丁操作序列</div>
                  </div>
                  <v-btn color="primary" prepend-icon="mdi-plus" variant="tonal" @click="addPatchOperation()">添加操作</v-btn>
                </div>

                <v-alert v-if="patchValidationMessage" type="warning" variant="tonal" class="mb-4">
                  {{ patchValidationMessage }}
                </v-alert>

                <v-alert v-if="patchForm.operations.length === 0" type="info" variant="tonal" class="mb-4">
                  当前没有补丁操作。点击“添加操作”，或切换到“原生 JSON 编辑”直接粘贴操作数组。
                </v-alert>

                <div class="d-flex flex-column ga-4">
                  <v-card
                    v-for="(operation, index) in patchForm.operations"
                    :key="operation.id"
                    border="sm"
                    rounded="xl"
                    variant="outlined"
                    :class="{ 'patch-operation-card--active': operation.id === activePatchOperationId }"
                    @click="setActivePatchOperation(operation.id)"
                  >
                    <v-card-item>
                      <div class="d-flex flex-column flex-md-row ga-3 justify-space-between">
                        <div>
                          <v-card-title class="px-0">第 {{ index + 1 }} 步</v-card-title>
                          <v-card-subtitle class="px-0">{{ operationDescription(operation.op) }}</v-card-subtitle>
                        </div>
                        <div class="d-flex ga-2 align-start">
                          <v-chip v-if="operation.id === activePatchOperationId" size="small" color="primary" variant="tonal">当前编辑路径</v-chip>
                          <v-btn icon="mdi-arrow-up" size="small" variant="text" :disabled="index === 0" @click.stop="movePatchOperation(index, -1)" />
                          <v-btn
                            icon="mdi-arrow-down"
                            size="small"
                            variant="text"
                            :disabled="index === patchForm.operations.length - 1"
                            @click.stop="movePatchOperation(index, 1)"
                          />
                          <v-btn icon="mdi-delete-outline" size="small" variant="text" color="error" @click.stop="removePatchOperation(index)" />
                        </div>
                      </div>
                    </v-card-item>

                    <v-card-text>
                      <v-row>
                        <v-col cols="12" md="4">
                          <SegmentedPicker
                            :model-value="operation.op"
                            :items="PATCH_OPERATION_OPTIONS.map((item) => ({ ...item, shortTitle: item.title }))"
                            aria-label="操作类型"
                            @update:model-value="updatePatchOperationKind(operation, $event)"
                          />
                        </v-col>
                        <v-col cols="12" md="8">
                          <v-text-field
                            v-model="operation.path"
                            label="路径"
                            placeholder="proxy-groups.0.proxies"
                            hint="使用点号路径；数组下标写数字。"
                            persistent-hint
                            @focus="setActivePatchOperation(operation.id)"
                          >
                            <template #append-inner>
                              <v-btn
                                icon="mdi-file-tree-outline"
                                size="small"
                                variant="text"
                                @click.stop="openPathPicker(operation.id)"
                              />
                            </template>
                          </v-text-field>
                        </v-col>
                        <v-col cols="12">
                          <v-alert :type="pathPreviewFor(operation.id).ok ? 'success' : 'info'" variant="tonal" density="comfortable">
                            <div class="font-weight-medium">{{ pathPreviewFor(operation.id).message }}</div>
                            <template v-if="pathPreviewFor(operation.id).ok && pathContextFor(operation.id).lines.length > 0">
                              <div class="text-caption text-medium-emphasis mt-2">目标模板上下文</div>
                              <div class="yaml-context-panel mt-2">
                                <template v-for="line in visibleContextLines(operation.id)" :key="`${operation.id}-${line.lineNumber}`">
                                  <div v-if="shouldShowContextFoldBefore(operation.id, line.lineNumber)" class="yaml-context-fold">
                                    <v-btn
                                      size="small"
                                      variant="text"
                                      prepend-icon="mdi-unfold-more-horizontal"
                                      @click="expandContext(operation.id)"
                                    >
                                      展开隐藏的 {{ hiddenContextLineCount(operation.id) }} 行
                                    </v-btn>
                                  </div>
                                  <div
                                    class="yaml-context-line"
                                    :class="{ 'yaml-context-line--match': line.isMatch }"
                                  >
                                    <div class="yaml-context-line__number">{{ line.lineNumber }}</div>
                                    <pre class="yaml-context-line__code"><template v-for="(token, tokenIndex) in line.tokens" :key="`${line.lineNumber}-${tokenIndex}`"><span :class="`yaml-token yaml-token--${token.kind}`">{{ token.text }}</span></template></pre>
                                  </div>
                                  <div v-if="shouldShowContextCollapseAfter(operation.id, line.lineNumber)" class="yaml-context-fold">
                                    <v-btn
                                      size="small"
                                      variant="text"
                                      prepend-icon="mdi-unfold-less-horizontal"
                                      @click="collapseContext(operation.id)"
                                    >
                                      收起已展开的块
                                    </v-btn>
                                  </div>
                                </template>
                              </div>
                            </template>
                          </v-alert>
                        </v-col>

                        <v-col v-if="requiresIndex(operation.op)" cols="12" md="4">
                          <v-text-field
                            v-model="operation.indexText"
                            label="索引"
                            type="number"
                            min="0"
                            placeholder="0"
                          />
                        </v-col>

                        <v-col v-if="requiresValue(operation.op)" cols="12" :md="requiresIndex(operation.op) ? 8 : 12">
                          <StructuredValueEditor
                            :node="operation.valueEditor"
                            :factory="valueFactory"
                            label="value"
                            :allow-null="operation.op !== 'merge'"
                          />
                        </v-col>

                        <v-col v-if="operation.op === 'list_remove' || operation.op === 'list_replace'" cols="12">
                          <v-switch v-model="operation.useOldValue" label="启用 old_value 校验" hide-details />
                        </v-col>

                        <v-col v-if="(operation.op === 'list_remove' || operation.op === 'list_replace') && operation.useOldValue" cols="12">
                          <StructuredValueEditor
                            :node="operation.oldValueEditor"
                            :factory="valueFactory"
                            label="old_value"
                          />
                        </v-col>
                      </v-row>
                    </v-card-text>
                  </v-card>
                </div>
              </v-window-item>

              <v-window-item value="json">
                <div class="d-flex flex-column ga-4">
                  <div class="d-flex justify-end">
                    <v-btn
                      color="primary"
                      variant="tonal"
                      prepend-icon="mdi-code-json"
                      @click="formatPatchJson"
                    >
                      格式化 JSON
                    </v-btn>
                  </div>
                  <v-alert v-if="patchJsonError" type="warning" variant="tonal">
                    {{ patchJsonError }}
                  </v-alert>
                  <MonacoJsonEditor
                    :model-value="patchJsonText"
                    :path-suggestions="patchPathSuggestions"
                    :path-entries="patchPathEntries"
                    height="32rem"
                    @update:model-value="handlePatchJsonInput"
                  />
                </div>
              </v-window-item>
            </v-window>
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

  <v-dialog v-model="pathPickerDialog" max-width="960">
    <v-card>
      <v-card-item>
        <v-card-title>选择模板路径</v-card-title>
      </v-card-item>

      <v-card-text>
        <div class="d-flex flex-column ga-4">
          <v-alert v-if="!activePatchOperation" type="info" variant="tonal">
            请先在补丁操作里选中一个目标路径输入框。
          </v-alert>
          <v-alert v-else type="success" variant="tonal">
            当前正在编辑：第 {{ patchForm.operations.findIndex((operation) => operation.id === activePatchOperationId) + 1 }} 步
          </v-alert>

          <v-alert v-if="!patchAuthoringTemplate" type="info" variant="tonal">
            请选择一个目标模板以浏览路径。
          </v-alert>
          <v-alert v-else-if="typeof patchAuthoringDocument === 'string'" type="warning" variant="tonal">
            {{ patchAuthoringDocument }}
          </v-alert>
          <template v-else>
            <v-text-field
              v-model="pathPickerSearch"
              label="搜索路径节点"
              placeholder="输入 key、路径或预览值"
              prepend-inner-icon="mdi-magnify"
              clearable
              hide-details
            />
            <div v-if="filteredPatchTreeNodes.length > 0" class="template-tree-panel">
              <TemplatePathTree
                :nodes="filteredPatchTreeNodes"
                :active-path="activePatchOperation?.path ?? null"
                :search-term="pathPickerSearch"
                :collapsed-paths="collapsedTreePaths"
                @select="applyTreePathToActiveOperation"
                @toggle="toggleCollapsedTreePath"
              />
            </div>
            <v-alert v-else type="info" variant="tonal">
              没有匹配的路径节点。
            </v-alert>
          </template>
        </div>
      </v-card-text>

      <v-card-actions>
        <v-spacer />
        <v-btn variant="text" @click="closePathPicker">关闭</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>

  <v-dialog v-model="compositeDialog">
    <v-card>
      <v-card-item>
        <v-card-title>{{ compositeDialogTitle }}</v-card-title>
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

.yaml-context-panel {
  border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  border-radius: 12px;
  overflow: hidden;
  background: rgba(var(--v-theme-surface), 1);
}

.yaml-context-fold {
  display: flex;
  justify-content: center;
  padding: 0.35rem 0.75rem;
  border-top: 1px dashed rgba(var(--v-border-color), 0.45);
  background: rgba(var(--v-theme-surface-variant), 0.16);
}


.yaml-context-line {
  display: grid;
  grid-template-columns: 56px 1fr;
  align-items: stretch;
  font-family: ui-monospace, 'SFMono-Regular', 'SF Mono', Consolas, 'Liberation Mono', Menlo, monospace;
  font-size: 0.86rem;
  line-height: 1.5;
}

.yaml-context-line + .yaml-context-line {
  border-top: 1px solid rgba(var(--v-border-color), 0.35);
}

.yaml-context-line--match {
  background: rgba(var(--v-theme-warning), 0.18);
  box-shadow: inset 4px 0 0 rgb(var(--v-theme-warning));
}

.yaml-context-line--match .yaml-context-line__number {
  color: rgb(var(--v-theme-warning));
  font-weight: 700;
  background: rgba(var(--v-theme-warning), 0.16);
}

.yaml-context-line__number {
  padding: 0.35rem 0.5rem;
  text-align: right;
  color: rgba(var(--v-theme-on-surface), var(--v-medium-emphasis-opacity));
  background: rgba(var(--v-theme-surface-variant), 0.55);
  border-inline-end: 1px solid rgba(var(--v-border-color), 0.35);
  user-select: none;
}

.yaml-context-line__code {
  margin: 0;
  padding: 0.35rem 0.75rem;
  white-space: pre-wrap;
  word-break: break-word;
}

.yaml-token--key {
  color: rgb(var(--v-theme-primary));
  font-weight: 600;
}

.yaml-token--punctuation {
  color: rgba(var(--v-theme-on-surface), var(--v-medium-emphasis-opacity));
}

.yaml-token--string {
  color: rgb(var(--v-theme-success));
}

.yaml-token--number {
  color: rgb(var(--v-theme-info));
}

.yaml-token--boolean,
.yaml-token--null {
  color: rgb(var(--v-theme-warning));
}

.yaml-token--comment {
  color: rgba(var(--v-theme-on-surface), 0.55);
  font-style: italic;
}

.template-tree-panel {
  max-height: 32rem;
  overflow: auto;
  border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  border-radius: 16px;
  background: rgba(var(--v-theme-surface), 1);
  padding: 0.5rem;
}

.patch-operation-card--active {
  border-color: rgba(var(--v-theme-primary), 0.7) !important;
  box-shadow: 0 0 0 1px rgba(var(--v-theme-primary), 0.24);
}
</style>