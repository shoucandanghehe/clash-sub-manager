export type StructuredValueKind = 'string' | 'number' | 'boolean' | 'null' | 'object' | 'array'

export interface StructuredObjectEntry {
  id: number
  key: string
  value: StructuredValueNode
}

export interface StructuredValueNode {
  id: number
  kind: StructuredValueKind
  stringValue: string
  numberValue: string
  booleanValue: boolean
  objectEntries: StructuredObjectEntry[]
  arrayItems: StructuredValueNode[]
}

export interface StructuredValueFactory {
  nextId: () => number
}

export function createStructuredValueNode(
  factory: StructuredValueFactory,
  kind: StructuredValueKind = 'string',
): StructuredValueNode {
  return {
    id: factory.nextId(),
    kind,
    stringValue: '',
    numberValue: '',
    booleanValue: false,
    objectEntries: [],
    arrayItems: [],
  }
}

export function setStructuredValueKind(
  node: StructuredValueNode,
  factory: StructuredValueFactory,
  kind: StructuredValueKind,
): void {
  node.kind = kind
  node.stringValue = ''
  node.numberValue = ''
  node.booleanValue = false
  node.objectEntries = []
  node.arrayItems = []

  if (kind === 'object') {
    node.objectEntries = [createStructuredObjectEntry(factory)]
  }
  if (kind === 'array') {
    node.arrayItems = [createStructuredValueNode(factory)]
  }
}

export function createStructuredObjectEntry(factory: StructuredValueFactory): StructuredObjectEntry {
  return {
    id: factory.nextId(),
    key: '',
    value: createStructuredValueNode(factory),
  }
}

export function structuredValueKindFromUnknown(value: unknown): StructuredValueKind {
  if (value === null) {
    return 'null'
  }
  if (Array.isArray(value)) {
    return 'array'
  }
  if (typeof value === 'string') {
    return 'string'
  }
  if (typeof value === 'number') {
    return 'number'
  }
  if (typeof value === 'boolean') {
    return 'boolean'
  }
  return 'object'
}

export function structuredValueNodeFromUnknown(
  factory: StructuredValueFactory,
  value: unknown,
): StructuredValueNode {
  const kind = structuredValueKindFromUnknown(value)
  const node = createStructuredValueNode(factory, kind)

  if (kind === 'string') {
    node.stringValue = String(value)
    return node
  }
  if (kind === 'number') {
    node.numberValue = String(value)
    return node
  }
  if (kind === 'boolean') {
    node.booleanValue = Boolean(value)
    return node
  }
  if (kind === 'null') {
    return node
  }
  if (kind === 'array') {
    node.arrayItems = (value as unknown[]).map((item) => structuredValueNodeFromUnknown(factory, item))
    if (node.arrayItems.length === 0) {
      node.arrayItems = [createStructuredValueNode(factory)]
    }
    return node
  }

  node.objectEntries = Object.entries(value as Record<string, unknown>).map(([key, entryValue]) => ({
    id: factory.nextId(),
    key,
    value: structuredValueNodeFromUnknown(factory, entryValue),
  }))
  if (node.objectEntries.length === 0) {
    node.objectEntries = [createStructuredObjectEntry(factory)]
  }
  return node
}

export function structuredValueNodeToUnknown(node: StructuredValueNode, label: string): unknown {
  if (node.kind === 'string') {
    return node.stringValue
  }
  if (node.kind === 'number') {
    const trimmed = node.numberValue.trim()
    if (!trimmed) {
      throw new Error(`${label} 不能为空。`)
    }
    const parsed = Number(trimmed)
    if (Number.isNaN(parsed)) {
      throw new Error(`${label} 必须是合法数字。`)
    }
    return parsed
  }
  if (node.kind === 'boolean') {
    return node.booleanValue
  }
  if (node.kind === 'null') {
    return null
  }
  if (node.kind === 'array') {
    return node.arrayItems.map((item, index) => structuredValueNodeToUnknown(item, `${label}[${index}]`))
  }

  const result: Record<string, unknown> = {}
  for (const [index, entry] of node.objectEntries.entries()) {
    const key = entry.key.trim()
    if (!key) {
      throw new Error(`${label} 的第 ${index + 1} 个字段缺少 key。`)
    }
    result[key] = structuredValueNodeToUnknown(entry.value, `${label}.${key}`)
  }
  return result
}
