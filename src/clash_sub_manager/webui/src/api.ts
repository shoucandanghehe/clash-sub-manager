export interface SubscriptionRecord {
  id: number
  name: string
  url: string | null
  content: string | null
  proxy: string | null
  headers: Record<string, string>
  follow_redirects: boolean
  enabled: boolean
  template_id: number | null
}

export interface TemplateRecord {
  id: number
  name: string
  content: string
  is_default: boolean
}

export interface RuleSourceRecord {
  id: number
  name: string
  url: string
  auto_update: boolean
  content: string | null
}

export interface SubscriptionSummaryRecord {
  id: number
  name: string
  enabled: boolean
}

export interface TemplateSummaryRecord {
  id: number
  name: string
}

export interface TemplatePatchOperation {
  op: 'delete' | 'list_append' | 'list_insert' | 'list_remove' | 'list_replace' | 'merge' | 'set'
  path: string
  value?: unknown
  index?: number
  old_value?: unknown
}

export interface TemplatePatchRecord {
  id: number
  name: string
  description: string | null
  operations: TemplatePatchOperation[]
  created_at: string
  updated_at: string
}

export interface TemplatePatchSummaryRecord {
  id: number
  name: string
  description: string | null
}

export interface CompositeTemplateRecord {
  id: number
  name: string
  base_template_id: number
  patch_sequence: number[]
  cached_content: string
  created_at: string
  updated_at: string
  base_template: TemplateSummaryRecord
  patches: TemplatePatchSummaryRecord[]
}

export interface MergeProfileRecord {
  id: number
  name: string
  enabled: boolean
  template_id: number | null
  template: TemplateSummaryRecord | null
  subscriptions: SubscriptionSummaryRecord[]
}

export interface SubscriptionPayload {
  name: string
  url?: string
  content?: string
  proxy?: string | null
  headers?: Record<string, string>
  follow_redirects?: boolean
  enabled?: boolean
  template_id?: number | null
}

export interface TemplatePayload {
  name: string
  content: string
  is_default?: boolean
}

export interface TemplatePatchPayload {
  name: string
  description?: string | null
  operations: TemplatePatchOperation[]
}

export interface CompositeTemplatePayload {
  name: string
  base_template_id: number
  patch_sequence: number[]
}

export interface RuleSourcePayload {
  name: string
  url: string
  auto_update?: boolean
  content?: string | null
}

export interface MergeProfilePayload {
  name: string
  template_id?: number | null
  enabled?: boolean
  subscription_ids: number[]
}

export interface ConvertPayload {
  url?: string
  content?: string
}

export interface MergePayload {
  configs: Array<{
    url?: string
    content?: string
    name?: string
    enabled?: boolean
    proxy?: string | null
    headers?: Record<string, string>
    follow_redirects?: boolean
  }>
  template?: Record<string, unknown>
}

export interface CompositePreviewPayload {
  base_template_id: number
  patch_sequence: number[]
}

export interface CompositePreviewResponse {
  content: string
}

async function readErrorMessage(response: Response): Promise<string> {
  const fallback = `${response.status} ${response.statusText}`
  const raw = await response.text()
  if (!raw) {
    return fallback
  }

  try {
    const parsed = JSON.parse(raw) as { detail?: unknown }
    if (typeof parsed.detail === 'string') {
      return parsed.detail
    }
    if (Array.isArray(parsed.detail)) {
      return parsed.detail
        .map((item) => (typeof item === 'string' ? item : JSON.stringify(item)))
        .join('\n')
    }
  } catch {
    return raw
  }

  return raw
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    headers: { 'Content-Type': 'application/json', ...(init?.headers ?? {}) },
    ...init,
  })

  if (!response.ok) {
    throw new Error(await readErrorMessage(response))
  }

  if (response.status === 204) {
    return undefined as T
  }
  return (await response.json()) as T
}

export const api = {
  listSubscriptions: () => request<SubscriptionRecord[]>('/subscriptions'),
  createSubscription: (payload: SubscriptionPayload) =>
    request<SubscriptionRecord>('/subscriptions', { method: 'POST', body: JSON.stringify(payload) }),
  updateSubscription: (id: number, payload: Partial<SubscriptionPayload>) =>
    request<SubscriptionRecord>(`/subscriptions/${id}`, { method: 'PUT', body: JSON.stringify(payload) }),
  deleteSubscription: (id: number) => request<void>(`/subscriptions/${id}`, { method: 'DELETE' }),
  listTemplates: () => request<TemplateRecord[]>('/templates'),
  createTemplate: (payload: TemplatePayload) =>
    request<TemplateRecord>('/templates', { method: 'POST', body: JSON.stringify(payload) }),
  updateTemplate: (id: number, payload: Partial<TemplatePayload>) =>
    request<TemplateRecord>(`/templates/${id}`, { method: 'PUT', body: JSON.stringify(payload) }),
  deleteTemplate: (id: number) => request<void>(`/templates/${id}`, { method: 'DELETE' }),
  listTemplatePatches: () => request<TemplatePatchRecord[]>('/template-patches'),
  createTemplatePatch: (payload: TemplatePatchPayload) =>
    request<TemplatePatchRecord>('/template-patches', { method: 'POST', body: JSON.stringify(payload) }),
  updateTemplatePatch: (id: number, payload: Partial<TemplatePatchPayload>) =>
    request<TemplatePatchRecord>(`/template-patches/${id}`, { method: 'PUT', body: JSON.stringify(payload) }),
  deleteTemplatePatch: (id: number) => request<void>(`/template-patches/${id}`, { method: 'DELETE' }),
  previewTemplatePatch: (id: number, baseTemplateId: number) =>
    request<CompositePreviewResponse>(`/template-patches/${id}/preview`, {
      method: 'POST',
      body: JSON.stringify({ base_template_id: baseTemplateId }),
    }),
  listCompositeTemplates: () => request<CompositeTemplateRecord[]>('/composite-templates'),
  createCompositeTemplate: (payload: CompositeTemplatePayload) =>
    request<CompositeTemplateRecord>('/composite-templates', { method: 'POST', body: JSON.stringify(payload) }),
  updateCompositeTemplate: (id: number, payload: Partial<CompositeTemplatePayload>) =>
    request<CompositeTemplateRecord>(`/composite-templates/${id}`, { method: 'PUT', body: JSON.stringify(payload) }),
  deleteCompositeTemplate: (id: number) => request<void>(`/composite-templates/${id}`, { method: 'DELETE' }),
  previewCompositeTemplate: (payload: CompositePreviewPayload) =>
    request<CompositePreviewResponse>('/composite-templates/preview', { method: 'POST', body: JSON.stringify(payload) }),
  listRuleSources: () => request<RuleSourceRecord[]>('/rule-sources'),
  createRuleSource: (payload: RuleSourcePayload) =>
    request<RuleSourceRecord>('/rule-sources', { method: 'POST', body: JSON.stringify(payload) }),
  updateRuleSource: (id: number, payload: Partial<RuleSourcePayload>) =>
    request<RuleSourceRecord>(`/rule-sources/${id}`, { method: 'PUT', body: JSON.stringify(payload) }),
  refreshRuleSource: (id: number) => request<string>(`/rule-sources/${id}/update`, { method: 'POST' }),
  deleteRuleSource: (id: number) => request<void>(`/rule-sources/${id}`, { method: 'DELETE' }),
  listMergeProfiles: () => request<MergeProfileRecord[]>('/merge-profiles'),
  createMergeProfile: (payload: MergeProfilePayload) =>
    request<MergeProfileRecord>('/merge-profiles', { method: 'POST', body: JSON.stringify(payload) }),
  updateMergeProfile: (id: number, payload: Partial<MergeProfilePayload>) =>
    request<MergeProfileRecord>(`/merge-profiles/${id}`, { method: 'PUT', body: JSON.stringify(payload) }),
  deleteMergeProfile: (id: number) => request<void>(`/merge-profiles/${id}`, { method: 'DELETE' }),
  generateMergeProfile: (id: number) => request<Record<string, unknown>>(`/merge-profiles/${id}/generate`, { method: 'POST' }),
  convertPreview: (payload: ConvertPayload) =>
    request<Record<string, unknown>>('/convert', { method: 'POST', body: JSON.stringify(payload) }),
  mergePreview: (payload: MergePayload) =>
    request<Record<string, unknown>>('/merge', { method: 'POST', body: JSON.stringify(payload) }),
}
