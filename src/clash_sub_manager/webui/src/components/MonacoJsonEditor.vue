<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as monaco from 'monaco-editor'

import editorWorker from 'monaco-editor/esm/vs/editor/editor.worker?worker'
import jsonWorker from 'monaco-editor/esm/vs/language/json/json.worker?worker'

const PATCH_OPERATIONS_SCHEMA_URI = 'inmemory://schema/patch-operations.json'
const MODEL_URI = monaco.Uri.parse('inmemory://model/patch-operations.json')
const PATCH_OPERATION_NAMES = ['set', 'delete', 'merge', 'list_append', 'list_insert', 'list_remove', 'list_replace'] as const

const props = withDefaults(
  defineProps<{
    modelValue: string
    height?: string
  }>(),
  {
    height: '28rem',
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
    provideCompletionItems(model, position) {
      if (model.uri.toString() !== MODEL_URI.toString()) {
        return { suggestions: [] }
      }

      const suggestions = [
        ...createOperationValueSuggestions(model, position),
        ...createOperationSnippetSuggestions(model, position),
      ]
      return { suggestions }
    },
  })
}

function createOperationValueSuggestions(
  currentModel: monaco.editor.ITextModel,
  position: monaco.Position,
): monaco.languages.CompletionItem[] {
  const range = currentModel.getWordUntilPosition(position)
  const wordRange = new monaco.Range(
    position.lineNumber,
    range.startColumn,
    position.lineNumber,
    range.endColumn,
  )

  if (!isInsideOpValue(currentModel, position)) {
    return []
  }

  return PATCH_OPERATION_NAMES.map((name) => ({
    label: name,
    kind: monaco.languages.CompletionItemKind.EnumMember,
    insertText: name,
    range: wordRange,
    detail: '补丁操作类型',
    documentation: describeOperation(name),
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

function isInsideOpValue(currentModel: monaco.editor.ITextModel, position: monaco.Position): boolean {
  const linePrefix = currentModel.getLineContent(position.lineNumber).slice(0, position.column - 1)
  return /"op"\s*:\s*"[^"]*$/.test(linePrefix)
}

function shouldOfferObjectSnippets(currentModel: monaco.editor.ITextModel, position: monaco.Position): boolean {
  const linePrefix = currentModel.getLineContent(position.lineNumber).slice(0, position.column - 1)
  return /^\s*$/.test(linePrefix) || /\[\s*$/.test(linePrefix) || /,\s*$/.test(linePrefix)
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
