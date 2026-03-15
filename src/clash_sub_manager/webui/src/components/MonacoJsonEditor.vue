<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as monaco from 'monaco-editor'

import editorWorker from 'monaco-editor/esm/vs/editor/editor.worker?worker'
import jsonWorker from 'monaco-editor/esm/vs/language/json/json.worker?worker'

const PATCH_OPERATIONS_SCHEMA_URI = 'inmemory://schema/patch-operations.json'
const MODEL_URI = monaco.Uri.parse('inmemory://model/patch-operations.json')
const PATCH_OPERATION_NAMES = ['set', 'delete', 'merge', 'list_append', 'list_insert', 'list_remove', 'list_replace'] as const
const OPERATION_FIELD_MAP: Record<(typeof PATCH_OPERATION_NAMES)[number], string[]> = {
  set: ['op', 'path', 'value'],
  delete: ['op', 'path'],
  merge: ['op', 'path', 'value'],
  list_append: ['op', 'path', 'value'],
  list_insert: ['op', 'path', 'index', 'value'],
  list_remove: ['op', 'path', 'value'],
  list_replace: ['op', 'path', 'index', 'old_value', 'value'],
}
const DEFAULT_FIELDS = ['op', 'path', 'value', 'index', 'old_value']

const props = withDefaults(
  defineProps<{
    modelValue: string
    height?: string
    pathSuggestions?: string[]
  }>(),
  {
    height: '28rem',
    pathSuggestions: () => [],
  },
)

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const container = ref<HTMLElement | null>(null)
let editor: monaco.editor.IStandaloneCodeEditor | null = null
let model: monaco.editor.ITextModel | null = null
let applyingExternalValue = false
let completionDisposable: monaco.IDisposable | null = null

setupMonacoEnvironment()
setupJsonDiagnostics()
setupPatchJsonCompletions()

function setupMonacoEnvironment(): void {
  if ((globalThis as { __clashMonacoConfigured?: boolean }).__clashMonacoConfigured) {
    return
  }

  self.MonacoEnvironment = {
    getWorker(_: string, label: string) {
      if (label === 'json') {
        return new jsonWorker()
      }
      return new editorWorker()
    },
  }

  ;(globalThis as { __clashMonacoConfigured?: boolean }).__clashMonacoConfigured = true
}

function setupJsonDiagnostics(): void {
  monaco.languages.json.jsonDefaults.setDiagnosticsOptions({
    validate: true,
    allowComments: false,
    enableSchemaRequest: false,
    schemas: [
      {
        uri: PATCH_OPERATIONS_SCHEMA_URI,
        fileMatch: [String(MODEL_URI)],
        schema: {
          type: 'array',
          items: {
            type: 'object',
            additionalProperties: false,
            required: ['op', 'path'],
            properties: {
              op: {
                type: 'string',
                enum: [...PATCH_OPERATION_NAMES],
              },
              path: {
                type: 'string',
                minLength: 1,
              },
              value: {},
              index: {
                type: 'integer',
                minimum: 0,
              },
              old_value: {},
            },
            allOf: [
              {
                if: { properties: { op: { const: 'delete' } } },
                then: {
                  not: {
                    anyOf: [{ required: ['value'] }, { required: ['index'] }, { required: ['old_value'] }],
                  },
                },
              },
              {
                if: { properties: { op: { enum: ['set', 'merge', 'list_append', 'list_remove'] } } },
                then: {
                  required: ['value'],
                },
              },
              {
                if: { properties: { op: { enum: ['list_insert', 'list_replace'] } } },
                then: {
                  required: ['value', 'index'],
                },
              },
            ],
          },
        },
      },
    ],
  })
}

function setupPatchJsonCompletions(): void {
  if (completionDisposable) {
    return
  }

  completionDisposable = monaco.languages.registerCompletionItemProvider('json', {
    triggerCharacters: ['"', ':', '{', '[', ','],
    provideCompletionItems(currentModel, position) {
      if (currentModel.uri.toString() !== MODEL_URI.toString()) {
        return { suggestions: [] }
      }

      const suggestions = [
        ...createOperationValueSuggestions(currentModel, position),
        ...createPathValueSuggestions(currentModel, position),
        ...createFieldNameSuggestions(currentModel, position),
        ...createOperationSnippetSuggestions(currentModel, position),
      ]
      return { suggestions }
    },
  })
}

function createOperationValueSuggestions(
  currentModel: monaco.editor.ITextModel,
  position: monaco.Position,
): monaco.languages.CompletionItem[] {
  if (!isInsidePropertyString(currentModel, position, 'op')) {
    return []
  }

  const range = stringValueRange(currentModel, position)
  return PATCH_OPERATION_NAMES.map((name) => ({
    label: name,
    kind: monaco.languages.CompletionItemKind.EnumMember,
    insertText: name,
    range,
    detail: '补丁操作类型',
    documentation: describeOperation(name),
  }))
}

function createPathValueSuggestions(
  currentModel: monaco.editor.ITextModel,
  position: monaco.Position,
): monaco.languages.CompletionItem[] {
  if (!isInsidePropertyString(currentModel, position, 'path')) {
    return []
  }

  const range = stringValueRange(currentModel, position)
  return props.pathSuggestions.map((path) => ({
    label: path,
    kind: monaco.languages.CompletionItemKind.Reference,
    insertText: path,
    range,
    detail: '目标模板路径',
    documentation: '来自当前路径校验目标模板的可用路径。',
  }))
}

function createFieldNameSuggestions(
  currentModel: monaco.editor.ITextModel,
  position: monaco.Position,
): monaco.languages.CompletionItem[] {
  if (!shouldOfferFieldSuggestions(currentModel, position)) {
    return []
  }

  const line = currentModel.getLineContent(position.lineNumber)
  const indent = line.match(/^\s*/)?.[0] ?? ''
  const baseRange = new monaco.Range(position.lineNumber, position.column, position.lineNumber, position.column)
  const operationName = guessCurrentOperation(currentModel, position)
  const fields = operationName ? OPERATION_FIELD_MAP[operationName] : DEFAULT_FIELDS

  return fields.map((field) => ({
    label: field,
    kind: monaco.languages.CompletionItemKind.Property,
    insertText: fieldSnippet(field, indent),
    insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
    range: baseRange,
    detail: operationName ? `${operationName} 字段` : '补丁字段',
  }))
}

function createOperationSnippetSuggestions(
  currentModel: monaco.editor.ITextModel,
  position: monaco.Position,
): monaco.languages.CompletionItem[] {
  if (!shouldOfferObjectSnippets(currentModel, position)) {
    return []
  }

  const line = currentModel.getLineContent(position.lineNumber)
  const indent = line.match(/^\s*/)?.[0] ?? ''
  const baseRange = new monaco.Range(position.lineNumber, position.column, position.lineNumber, position.column)

  return [
    createSnippetSuggestion('set 操作', 'set', baseRange, [
      `${indent}{`,
      `${indent}  "op": "set",`,
      `${indent}  "path": "$1",`,
      `${indent}  "value": $2`,
      `${indent}}$0`,
    ]),
    createSnippetSuggestion('delete 操作', 'delete', baseRange, [
      `${indent}{`,
      `${indent}  "op": "delete",`,
      `${indent}  "path": "$1"`,
      `${indent}}$0`,
    ]),
    createSnippetSuggestion('merge 操作', 'merge', baseRange, [
      `${indent}{`,
      `${indent}  "op": "merge",`,
      `${indent}  "path": "$1",`,
      `${indent}  "value": {`,
      `${indent}    "$2": $3`,
      `${indent}  }`,
      `${indent}}$0`,
    ]),
    createSnippetSuggestion('list_append 操作', 'list_append', baseRange, [
      `${indent}{`,
      `${indent}  "op": "list_append",`,
      `${indent}  "path": "$1",`,
      `${indent}  "value": $2`,
      `${indent}}$0`,
    ]),
    createSnippetSuggestion('list_insert 操作', 'list_insert', baseRange, [
      `${indent}{`,
      `${indent}  "op": "list_insert",`,
      `${indent}  "path": "$1",`,
      `${indent}  "index": $2,`,
      `${indent}  "value": $3`,
      `${indent}}$0`,
    ]),
    createSnippetSuggestion('list_remove 操作', 'list_remove', baseRange, [
      `${indent}{`,
      `${indent}  "op": "list_remove",`,
      `${indent}  "path": "$1",`,
      `${indent}  "value": $2`,
      `${indent}}$0`,
    ]),
    createSnippetSuggestion('list_replace 操作', 'list_replace', baseRange, [
      `${indent}{`,
      `${indent}  "op": "list_replace",`,
      `${indent}  "path": "$1",`,
      `${indent}  "index": $2,`,
      `${indent}  "old_value": $3,`,
      `${indent}  "value": $4`,
      `${indent}}$0`,
    ]),
  ]
}

function createSnippetSuggestion(
  label: string,
  operationName: string,
  range: monaco.Range,
  lines: string[],
): monaco.languages.CompletionItem {
  return {
    label,
    kind: monaco.languages.CompletionItemKind.Snippet,
    insertText: lines.join('\n'),
    insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
    range,
    detail: `${operationName} JSON 模板`,
    documentation: describeOperation(operationName as (typeof PATCH_OPERATION_NAMES)[number]),
  }
}

function isInsidePropertyString(
  currentModel: monaco.editor.ITextModel,
  position: monaco.Position,
  propertyName: string,
): boolean {
  const linePrefix = currentModel.getLineContent(position.lineNumber).slice(0, position.column - 1)
  return new RegExp(`"${propertyName}"\\s*:\\s*"[^"]*$`).test(linePrefix)
}

function stringValueRange(currentModel: monaco.editor.ITextModel, position: monaco.Position): monaco.Range {
  const range = currentModel.getWordUntilPosition(position)
  return new monaco.Range(
    position.lineNumber,
    range.startColumn,
    position.lineNumber,
    range.endColumn,
  )
}

function shouldOfferFieldSuggestions(currentModel: monaco.editor.ITextModel, position: monaco.Position): boolean {
  const linePrefix = currentModel.getLineContent(position.lineNumber).slice(0, position.column - 1)
  return /{\s*$/.test(linePrefix) || /,\s*$/.test(linePrefix)
}

function shouldOfferObjectSnippets(currentModel: monaco.editor.ITextModel, position: monaco.Position): boolean {
  const linePrefix = currentModel.getLineContent(position.lineNumber).slice(0, position.column - 1)
  return /^\s*$/.test(linePrefix) || /\[\s*$/.test(linePrefix) || /,\s*$/.test(linePrefix)
}

function fieldSnippet(field: string, indent: string): string {
  switch (field) {
    case 'op':
      return `${indent}"op": "$1"$0`
    case 'path':
      return `${indent}"path": "$1"$0`
    case 'index':
      return `${indent}"index": $1$0`
    case 'old_value':
      return `${indent}"old_value": $1$0`
    default:
      return `${indent}"${field}": $1$0`
  }
}

function guessCurrentOperation(
  currentModel: monaco.editor.ITextModel,
  position: monaco.Position,
): (typeof PATCH_OPERATION_NAMES)[number] | null {
  const fullText = currentModel.getValueInRange(
    new monaco.Range(1, 1, position.lineNumber, currentModel.getLineMaxColumn(position.lineNumber)),
  )
  const matches = [...fullText.matchAll(/"op"\s*:\s*"([a-z_]+)"/g)]
  const last = matches.at(-1)?.[1]
  return PATCH_OPERATION_NAMES.find((name) => name === last) ?? null
}

function describeOperation(name: (typeof PATCH_OPERATION_NAMES)[number]): string {
  switch (name) {
    case 'set':
      return '设置指定路径的值。'
    case 'delete':
      return '删除指定路径的值。'
    case 'merge':
      return '向目标对象执行深度合并。'
    case 'list_append':
      return '向列表末尾追加元素。'
    case 'list_insert':
      return '向列表指定索引插入元素。'
    case 'list_remove':
      return '从列表中删除匹配元素。'
    case 'list_replace':
      return '替换列表指定索引处的元素。'
  }
}

onMounted(() => {
  if (!container.value) {
    return
  }

  model = monaco.editor.getModel(MODEL_URI) ?? monaco.editor.createModel(props.modelValue, 'json', MODEL_URI)
  editor = monaco.editor.create(container.value, {
    model,
    language: 'json',
    theme: 'vs-dark',
    automaticLayout: true,
    minimap: { enabled: false },
    scrollBeyondLastLine: false,
    wordWrap: 'on',
    lineNumbers: 'on',
    tabSize: 2,
    insertSpaces: true,
    formatOnPaste: true,
    formatOnType: true,
    glyphMargin: false,
    folding: true,
    quickSuggestions: true,
    suggestOnTriggerCharacters: true,
    snippetSuggestions: 'inline',
  })

  editor.onDidChangeModelContent(() => {
    if (applyingExternalValue || !model) {
      return
    }
    emit('update:modelValue', model.getValue())
  })
})

watch(
  () => props.modelValue,
  (value) => {
    if (!model || value === model.getValue()) {
      return
    }

    applyingExternalValue = true
    model.pushEditOperations([], [{ range: model.getFullModelRange(), text: value }], () => null)
    applyingExternalValue = false
  },
)

onBeforeUnmount(() => {
  editor?.dispose()
  model?.dispose()
  completionDisposable?.dispose()
})
</script>

<template>
  <div ref="container" class="monaco-json-editor" :style="{ height }" />
</template>

<style scoped>
/* Monaco hover and suggestion widgets render outside the editor surface; do not clip them. */
.monaco-json-editor {
  width: 100%;
  border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  border-radius: 12px;
  overflow: visible;
}

/* Keep the editor canvas rounded without clipping Monaco overlays. */
:deep(.monaco-editor),
:deep(.overflow-guard) {
  border-radius: 12px;
}
</style>
