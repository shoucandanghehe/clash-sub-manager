import { dump as dumpYaml, load as loadYaml } from 'js-yaml'

export interface TemplatePathResolution {
  ok: boolean
  message: string
  matchedValue?: unknown
}

export interface TemplatePathTreeNode {
  id: string
  path: string
  label: string
  valuePreview: string
  children: TemplatePathTreeNode[]
}

export interface TemplatePathEntry {
  path: string
  value: unknown
  valuePreview: string
  kind: 'scalar' | 'object' | 'array'
}

export interface YamlContextToken {
  text: string
  kind: 'plain' | 'key' | 'punctuation' | 'string' | 'number' | 'boolean' | 'null' | 'comment'
}

export interface TemplatePathContextLine {
  lineNumber: number
  raw: string
  tokens: YamlContextToken[]
  isMatch: boolean
}

export interface TemplatePathContext {
  matchedLineNumber: number | null
  matchedBlockStartLineNumber: number | null
  matchedBlockEndLineNumber: number | null
  isCollectionMatch: boolean
  lines: TemplatePathContextLine[]
}

export function parseTemplateDocument(content: string): Record<string, unknown> {
  const parsed = loadYaml(content)
  if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) {
    throw new Error('模板内容必须是 YAML 映射对象。')
  }
  return parsed as Record<string, unknown>
}

export function resolveTemplatePath(document: Record<string, unknown>, rawPath: string): TemplatePathResolution {
  const path = rawPath.trim()
  if (!path) {
    return {
      ok: false,
      message: '请输入路径。',
    }
  }

  const segments = path.split('.')
  if (segments.some((segment) => segment.trim() === '')) {
    return {
      ok: false,
      message: '路径不能包含空段。',
    }
  }

  let current: unknown = document
  for (const [index, rawSegment] of segments.entries()) {
    const segment = rawSegment.trim()
    const printablePath = segments.slice(0, index + 1).join('.')

    if (Array.isArray(current)) {
      if (!/^\d+$/.test(segment)) {
        return {
          ok: false,
          message: `路径 ${printablePath} 必须使用数字下标访问数组。`,
        }
      }

      const arrayIndex = Number(segment)
      if (arrayIndex >= current.length) {
        return {
          ok: false,
          message: `路径 ${printablePath} 超出数组范围，当前长度为 ${current.length}。`,
        }
      }
      current = current[arrayIndex]
      continue
    }

    if (!current || typeof current !== 'object') {
      return {
        ok: false,
        message: `路径 ${printablePath} 的上一级不是对象或数组。`,
      }
    }

    const objectValue = current as Record<string, unknown>
    if (!(segment in objectValue)) {
      return {
        ok: false,
        message: `路径 ${printablePath} 不存在。`,
      }
    }
    current = objectValue[segment]
  }

  return {
    ok: true,
    message: '已匹配到模板中的目标位置。',
    matchedValue: current,
  }
}

export function buildTemplatePathContext(
  content: string,
  rawPath: string,
  matchedValue?: unknown,
  scalarRadius = 3,
  collectionRadius = 1,
): TemplatePathContext {
  const lineMap = buildYamlPathLineMap(content)
  const matchedLineNumber = resolveBestLineNumber(lineMap, rawPath)
  if (matchedLineNumber === null) {
    return {
      matchedLineNumber: null,
      matchedBlockStartLineNumber: null,
      matchedBlockEndLineNumber: null,
      isCollectionMatch: false,
      lines: [],
    }
  }

  const rawLines = content.split(/\r?\n/)
  const isCollectionMatch = Array.isArray(matchedValue) || isPlainObject(matchedValue)
  const blockEnd = isCollectionMatch
    ? findCollectionBlockEnd(rawLines, matchedLineNumber)
    : matchedLineNumber
  const radius = isCollectionMatch ? collectionRadius : scalarRadius
  const start = Math.max(1, matchedLineNumber - radius)
  const end = Math.min(rawLines.length, blockEnd + radius)
  const lines: TemplatePathContextLine[] = []

  for (let lineNumber = start; lineNumber <= end; lineNumber += 1) {
    const raw = rawLines[lineNumber - 1] ?? ''
    lines.push({
      lineNumber,
      raw,
      tokens: tokenizeYamlLine(raw),
      isMatch: isCollectionMatch
        ? lineNumber >= matchedLineNumber && lineNumber <= blockEnd
        : lineNumber === matchedLineNumber,
    })
  }

  return {
    matchedLineNumber,
    matchedBlockStartLineNumber: matchedLineNumber,
    matchedBlockEndLineNumber: blockEnd,
    isCollectionMatch,
    lines,
  }
}

export function buildTemplatePathTree(document: Record<string, unknown>): TemplatePathTreeNode[] {
  return buildTreeChildren(document, '')
}

export function buildTemplatePathEntries(document: Record<string, unknown>): TemplatePathEntry[] {
  const entries: TemplatePathEntry[] = []

  function visit(value: unknown, parentPath: string): void {
    if (Array.isArray(value)) {
      for (const [index, entry] of value.entries()) {
        const path = joinPath(parentPath, String(index))
        entries.push({
          path,
          value: entry,
          valuePreview: previewValue(entry),
          kind: Array.isArray(entry) ? 'array' : isPlainObject(entry) ? 'object' : 'scalar',
        })
        visit(entry, path)
      }
      return
    }

    if (value && typeof value === 'object') {
      for (const [key, entry] of Object.entries(value as Record<string, unknown>)) {
        const path = joinPath(parentPath, key)
        entries.push({
          path,
          value: entry,
          valuePreview: previewValue(entry),
          kind: Array.isArray(entry) ? 'array' : isPlainObject(entry) ? 'object' : 'scalar',
        })
        visit(entry, path)
      }
    }
  }

  visit(document, '')
  return entries
}

export function filterTemplatePathTree(
  nodes: TemplatePathTreeNode[],
  rawKeyword: string,
): TemplatePathTreeNode[] {
  const keyword = rawKeyword.trim().toLowerCase()
  if (!keyword) {
    return nodes
  }

  return nodes.flatMap((node) => filterNode(node, keyword))
}

function filterNode(node: TemplatePathTreeNode, keyword: string): TemplatePathTreeNode[] {
  const matchedChildren = node.children.flatMap((child) => filterNode(child, keyword))
  const matchesSelf = [node.label, node.path, node.valuePreview].some((value) => value.toLowerCase().includes(keyword))

  if (!matchesSelf && matchedChildren.length === 0) {
    return []
  }

  return [{
    ...node,
    children: matchedChildren,
  }]
}

function buildTreeChildren(value: unknown, parentPath: string): TemplatePathTreeNode[] {
  if (Array.isArray(value)) {
    return value.map((entry, index) => buildTreeNode(String(index), entry, parentPath))
  }

  if (value && typeof value === 'object') {
    return Object.entries(value as Record<string, unknown>).map(([key, entry]) => buildTreeNode(key, entry, parentPath))
  }

  return []
}

function buildTreeNode(segment: string, value: unknown, parentPath: string): TemplatePathTreeNode {
  const path = parentPath ? `${parentPath}.${segment}` : segment
  return {
    id: path,
    path,
    label: segment,
    valuePreview: previewValue(value),
    children: buildTreeChildren(value, path),
  }
}

function previewValue(value: unknown): string {
  if (Array.isArray(value)) {
    return `数组(${value.length})`
  }
  if (value && typeof value === 'object') {
    return `对象(${Object.keys(value as Record<string, unknown>).length})`
  }
  if (typeof value === 'string') {
    return value.length > 36 ? `${value.slice(0, 36)}…` : value
  }
  if (value === null) {
    return 'null'
  }
  return String(value)
}

function buildYamlPathLineMap(content: string): Map<string, number> {
  const lines = content.split(/\r?\n/)
  const map = new Map<string, number>()
  const stack: Array<{ indent: number; path: string; kind: 'object' | 'array' | 'unknown'; nextIndex: number }> = [
    { indent: -1, path: '', kind: 'object', nextIndex: 0 },
  ]

  for (const [index, line] of lines.entries()) {
    if (!line.trim() || line.trimStart().startsWith('#')) {
      continue
    }

    const indent = countIndent(line)
    while (stack.length > 1 && indent <= stack[stack.length - 1].indent) {
      stack.pop()
    }

    const parent = stack[stack.length - 1]
    const trimmed = line.trim()

    if (trimmed.startsWith('- ')) {
      if (parent.kind === 'unknown') {
        parent.kind = 'array'
      }
      const itemIndex = parent.nextIndex
      parent.nextIndex += 1
      const itemPath = joinPath(parent.path, String(itemIndex))
      setIfAbsent(map, itemPath, index + 1)

      const rest = trimmed.slice(2).trim()
      if (!rest) {
        stack.push({ indent, path: itemPath, kind: 'unknown', nextIndex: 0 })
        continue
      }

      const inlineMapping = parseKeyValue(rest)
      if (inlineMapping) {
        stack.push({ indent, path: itemPath, kind: 'object', nextIndex: 0 })
        const childPath = joinPath(itemPath, inlineMapping.key)
        setIfAbsent(map, childPath, index + 1)
        if (!inlineMapping.value) {
          stack.push({ indent: indent + 1, path: childPath, kind: 'unknown', nextIndex: 0 })
        }
      }
      continue
    }

    const mapping = parseKeyValue(trimmed)
    if (!mapping) {
      continue
    }

    if (parent.kind === 'unknown') {
      parent.kind = 'object'
    }

    const currentPath = joinPath(parent.path, mapping.key)
    setIfAbsent(map, currentPath, index + 1)

    if (!mapping.value) {
      stack.push({ indent, path: currentPath, kind: 'unknown', nextIndex: 0 })
    }
  }

  return map
}

function resolveBestLineNumber(lineMap: Map<string, number>, rawPath: string): number | null {
  const path = rawPath.trim()
  if (!path) {
    return null
  }

  let current = path
  while (current) {
    const lineNumber = lineMap.get(current)
    if (lineNumber !== undefined) {
      return lineNumber
    }
    const next = current.split('.')
    next.pop()
    current = next.join('.')
  }
  return null
}

function findCollectionBlockEnd(lines: string[], matchedLineNumber: number): number {
  const headerLine = lines[matchedLineNumber - 1] ?? ''
  const headerIndent = countIndent(headerLine)
  let blockEnd = matchedLineNumber

  for (let lineNumber = matchedLineNumber + 1; lineNumber <= lines.length; lineNumber += 1) {
    const raw = lines[lineNumber - 1] ?? ''
    const trimmed = raw.trim()

    if (!trimmed) {
      blockEnd = lineNumber
      continue
    }
    if (trimmed.startsWith('#')) {
      blockEnd = lineNumber
      continue
    }

    if (countIndent(raw) <= headerIndent) {
      break
    }
    blockEnd = lineNumber
  }

  return blockEnd
}

function tokenizeYamlLine(line: string): YamlContextToken[] {
  const indent = line.match(/^\s*/)?.[0] ?? ''
  const trimmed = line.slice(indent.length)
  if (!trimmed) {
    return [{ text: line, kind: 'plain' }]
  }
  if (trimmed.startsWith('#')) {
    return [
      { text: indent, kind: 'plain' },
      { text: trimmed, kind: 'comment' },
    ]
  }

  const listPrefix = trimmed.startsWith('- ') ? '- ' : ''
  const content = listPrefix ? trimmed.slice(2) : trimmed
  const mapping = parseKeyValue(content)

  const tokens: YamlContextToken[] = []
  if (indent) {
    tokens.push({ text: indent, kind: 'plain' })
  }
  if (listPrefix) {
    tokens.push({ text: listPrefix, kind: 'punctuation' })
  }

  if (mapping) {
    tokens.push({ text: mapping.key, kind: 'key' })
    tokens.push({ text: ':', kind: 'punctuation' })
    if (mapping.value) {
      tokens.push({ text: ' ', kind: 'plain' })
      tokens.push(...tokenizeScalar(mapping.value))
    }
    return tokens
  }

  tokens.push(...tokenizeScalar(content))
  return tokens
}

function tokenizeScalar(value: string): YamlContextToken[] {
  if (!value) {
    return []
  }
  const commentIndex = value.indexOf(' #')
  const scalar = commentIndex === -1 ? value : value.slice(0, commentIndex)
  const comment = commentIndex === -1 ? '' : value.slice(commentIndex + 1)

  const tokens: YamlContextToken[] = [{ text: scalar, kind: classifyScalar(scalar.trim()) }]
  if (comment) {
    tokens.push({ text: ' ', kind: 'plain' })
    tokens.push({ text: comment, kind: 'comment' })
  }
  return tokens
}

function classifyScalar(value: string): YamlContextToken['kind'] {
  if (!value) {
    return 'plain'
  }
  if (/^(true|false)$/i.test(value)) {
    return 'boolean'
  }
  if (/^(null|~)$/i.test(value)) {
    return 'null'
  }
  if (/^-?\d+(\.\d+)?$/.test(value)) {
    return 'number'
  }
  return 'string'
}

function parseKeyValue(value: string): { key: string; value: string } | null {
  const match = value.match(/^([^:#][^:]*):(?:\s*(.*))?$/)
  if (!match) {
    return null
  }
  return {
    key: match[1].trim(),
    value: match[2] ?? '',
  }
}

function countIndent(value: string): number {
  return value.match(/^\s*/)?.[0].length ?? 0
}

function joinPath(parent: string, segment: string): string {
  return parent ? `${parent}.${segment}` : segment
}

function setIfAbsent(map: Map<string, number>, key: string, lineNumber: number): void {
  if (!map.has(key)) {
    map.set(key, lineNumber)
  }
}

function isPlainObject(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === 'object' && !Array.isArray(value)
}
