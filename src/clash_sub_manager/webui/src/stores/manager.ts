import { dump as dumpYaml, load as loadYaml } from 'js-yaml'
import { defineStore } from 'pinia'
import { ref } from 'vue'

import {
  api,
  type CompositeTemplatePayload,
  type CompositeTemplateRecord,
  type ConvertPayload,
  type MergePayload,
  type MergeProfilePayload,
  type MergeProfileRecord,
  type RuleSourcePayload,
  type RuleSourceRecord,
  type SubscriptionPayload,
  type SubscriptionRecord,
  type TemplatePatchPayload,
  type TemplatePatchRecord,
  type TemplatePayload,
  type TemplateRecord,
} from '../api'

function toMessage(caught: unknown): string {
  return caught instanceof Error ? caught.message : '发生未知错误'
}

function formatDocument(document: Record<string, unknown>): string {
  return dumpYaml(document, {
    lineWidth: -1,
    noRefs: true,
  })
}

function parseTemplateContent(content: string): Record<string, unknown> {
  const parsed = loadYaml(content)
  if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) {
    throw new Error('模板内容必须是 YAML 映射对象。')
  }
  return parsed as Record<string, unknown>
}

export const useManagerStore = defineStore('manager', () => {
  const subscriptions = ref<SubscriptionRecord[]>([])
  const templates = ref<TemplateRecord[]>([])
  const templatePatches = ref<TemplatePatchRecord[]>([])
  const compositeTemplates = ref<CompositeTemplateRecord[]>([])
  const ruleSources = ref<RuleSourceRecord[]>([])
  const mergeProfiles = ref<MergeProfileRecord[]>([])
  const convertPreview = ref('')
  const mergePreview = ref('')
  const mergeProfilePreview = ref('')
  const mergeProfilePreviewName = ref('')
  const templatePatchPreview = ref('')
  const templatePatchPreviewName = ref('')
  const compositeTemplatePreview = ref('')
  const compositeTemplatePreviewName = ref('')
  const busy = ref(false)
  const error = ref('')
  const notice = ref('')

  function clearNotice(): void {
    notice.value = ''
  }

  function clearError(): void {
    error.value = ''
  }

  function clearMessages(): void {
    clearNotice()
    clearError()
  }

  function setError(message: string): void {
    error.value = message
    if (message) {
      notice.value = ''
    }
  }

  function setNotice(message: string): void {
    notice.value = message
    if (message) {
      error.value = ''
    }
  }

  function showError(message: string): void {
    setError(message)
  }

  function showNotice(message: string): void {
    setNotice(message)
  }

  async function run(label: string, action: () => Promise<void>): Promise<boolean> {
    busy.value = true
    clearMessages()
    try {
      await action()
      setNotice(label)
      return true
    } catch (caught) {
      setError(toMessage(caught))
      return false
    } finally {
      busy.value = false
    }
  }

  async function reloadSubscriptions(): Promise<void> {
    subscriptions.value = await api.listSubscriptions()
  }

  async function reloadTemplates(): Promise<void> {
    templates.value = await api.listTemplates()
  }

  async function reloadTemplatePatches(): Promise<void> {
    templatePatches.value = await api.listTemplatePatches()
  }

  async function reloadCompositeTemplates(): Promise<void> {
    compositeTemplates.value = await api.listCompositeTemplates()
  }

  async function reloadRuleSources(): Promise<void> {
    ruleSources.value = await api.listRuleSources()
  }

  async function reloadMergeProfiles(): Promise<void> {
    mergeProfiles.value = await api.listMergeProfiles()
  }

  async function refreshAll(): Promise<boolean> {
    return run('数据已刷新。', async () => {
      await Promise.all([
        reloadSubscriptions(),
        reloadTemplates(),
        reloadTemplatePatches(),
        reloadCompositeTemplates(),
        reloadRuleSources(),
        reloadMergeProfiles(),
      ])
    })
  }

  async function createSubscription(payload: SubscriptionPayload): Promise<boolean> {
    return run('订阅已创建。', async () => {
      await api.createSubscription(payload)
      await Promise.all([reloadSubscriptions(), reloadMergeProfiles()])
    })
  }

  async function updateSubscription(id: number, payload: Partial<SubscriptionPayload>): Promise<boolean> {
    return run('订阅已更新。', async () => {
      await api.updateSubscription(id, payload)
      await Promise.all([reloadSubscriptions(), reloadMergeProfiles()])
    })
  }

  async function toggleSubscription(id: number, enabled: boolean): Promise<boolean> {
    return updateSubscription(id, { enabled })
  }

  async function deleteSubscription(id: number): Promise<boolean> {
    return run('订阅已删除。', async () => {
      await api.deleteSubscription(id)
      await Promise.all([reloadSubscriptions(), reloadMergeProfiles()])
    })
  }

  async function createTemplate(payload: TemplatePayload): Promise<boolean> {
    return run('模板已创建。', async () => {
      await api.createTemplate(payload)
      await Promise.all([reloadTemplates(), reloadMergeProfiles(), reloadCompositeTemplates()])
    })
  }

  async function updateTemplate(id: number, payload: Partial<TemplatePayload>): Promise<boolean> {
    return run('模板已更新。', async () => {
      await api.updateTemplate(id, payload)
      await Promise.all([reloadTemplates(), reloadMergeProfiles(), reloadCompositeTemplates()])
    })
  }

  async function deleteTemplate(id: number): Promise<boolean> {
    return run('模板已删除。', async () => {
      await api.deleteTemplate(id)
      await Promise.all([reloadTemplates(), reloadMergeProfiles(), reloadCompositeTemplates()])
    })
  }

  async function createTemplatePatch(payload: TemplatePatchPayload): Promise<boolean> {
    return run('模板补丁已创建。', async () => {
      await api.createTemplatePatch(payload)
      await Promise.all([reloadTemplatePatches(), reloadCompositeTemplates()])
    })
  }

  async function updateTemplatePatch(id: number, payload: Partial<TemplatePatchPayload>): Promise<boolean> {
    return run('模板补丁已更新。', async () => {
      await api.updateTemplatePatch(id, payload)
      await Promise.all([reloadTemplatePatches(), reloadCompositeTemplates()])
    })
  }

  async function deleteTemplatePatch(id: number): Promise<boolean> {
    return run('模板补丁已删除。', async () => {
      await api.deleteTemplatePatch(id)
      await Promise.all([reloadTemplatePatches(), reloadCompositeTemplates()])
    })
  }

  async function previewTemplatePatch(id: number, baseTemplateId: number): Promise<boolean> {
    return run('已生成模板补丁预览。', async () => {
      const result = await api.previewTemplatePatch(id, baseTemplateId)
      const patch = templatePatches.value.find((item) => item.id === id)
      templatePatchPreview.value = result.content
      templatePatchPreviewName.value = patch?.name ?? '模板补丁预览'
    })
  }

  async function createCompositeTemplate(payload: CompositeTemplatePayload): Promise<boolean> {
    return run('组合模板已创建。', async () => {
      await api.createCompositeTemplate(payload)
      await reloadCompositeTemplates()
    })
  }

  async function updateCompositeTemplate(id: number, payload: Partial<CompositeTemplatePayload>): Promise<boolean> {
    return run('组合模板已更新。', async () => {
      await api.updateCompositeTemplate(id, payload)
      await reloadCompositeTemplates()
    })
  }

  async function deleteCompositeTemplate(id: number): Promise<boolean> {
    return run('组合模板已删除。', async () => {
      await api.deleteCompositeTemplate(id)
      await reloadCompositeTemplates()
    })
  }

  async function previewCompositeTemplate(payload: CompositeTemplatePayload): Promise<boolean> {
    return run('已生成组合模板预览。', async () => {
      const result = await api.previewCompositeTemplate(payload)
      compositeTemplatePreview.value = result.content
      compositeTemplatePreviewName.value = payload.name.trim() || '组合模板预览'
    })
  }

  async function createRuleSource(payload: RuleSourcePayload): Promise<boolean> {
    return run('规则源已创建。', async () => {
      await api.createRuleSource(payload)
      await reloadRuleSources()
    })
  }

  async function updateRuleSource(id: number, payload: Partial<RuleSourcePayload>): Promise<boolean> {
    return run('规则源已更新。', async () => {
      await api.updateRuleSource(id, payload)
      await reloadRuleSources()
    })
  }

  async function refreshRuleSource(id: number): Promise<boolean> {
    return run('规则源已刷新。', async () => {
      await api.refreshRuleSource(id)
      await reloadRuleSources()
    })
  }

  async function deleteRuleSource(id: number): Promise<boolean> {
    return run('规则源已删除。', async () => {
      await api.deleteRuleSource(id)
      await reloadRuleSources()
    })
  }

  async function createMergeProfile(payload: MergeProfilePayload): Promise<boolean> {
    return run('合并配置已创建。', async () => {
      await api.createMergeProfile(payload)
      await reloadMergeProfiles()
    })
  }

  async function updateMergeProfile(id: number, payload: Partial<MergeProfilePayload>): Promise<boolean> {
    return run('合并配置已更新。', async () => {
      await api.updateMergeProfile(id, payload)
      await reloadMergeProfiles()
    })
  }

  async function deleteMergeProfile(id: number): Promise<boolean> {
    return run('合并配置已删除。', async () => {
      await api.deleteMergeProfile(id)
      await reloadMergeProfiles()
    })
  }

  async function runConvertPreview(payload: ConvertPayload): Promise<boolean> {
    return run('已生成转换预览。', async () => {
      const result = await api.convertPreview(payload)
      convertPreview.value = result.content
    })
  }

  async function runMergePreview(templateId: number | null): Promise<boolean> {
    return run('已生成合并预览。', async () => {
      const templateContent = templateId === null
        ? undefined
        : templates.value.find((template) => template.id === templateId)?.content
      const template = templateContent ? parseTemplateContent(templateContent) : undefined
      const payload: MergePayload = {
        configs: subscriptions.value
          .filter((subscription) => subscription.enabled)
          .map((subscription) => ({
            name: subscription.name,
            url: subscription.url ?? undefined,
            content: subscription.content ?? undefined,
            proxy: subscription.proxy,
            headers: subscription.headers,
            follow_redirects: subscription.follow_redirects,
            enabled: subscription.enabled,
          })),
        template,
      }
      const result = await api.mergePreview(payload)
      mergePreview.value = result.content
    })
  }

  async function runMergeProfilePreview(id: number): Promise<boolean> {
    return run('已生成合并配置预览。', async () => {
      const result = await api.generateMergeProfile(id)
      mergeProfilePreview.value = result.content
      mergeProfilePreviewName.value = mergeProfiles.value.find((profile) => profile.id === id)?.name ?? '合并配置'
    })
  }

  return {
    busy,
    clearError,
    clearMessages,
    clearNotice,
    compositeTemplatePreview,
    compositeTemplatePreviewName,
    compositeTemplates,
    convertPreview,
    createCompositeTemplate,
    createMergeProfile,
    createRuleSource,
    createSubscription,
    createTemplate,
    createTemplatePatch,
    deleteCompositeTemplate,
    deleteMergeProfile,
    deleteRuleSource,
    deleteSubscription,
    deleteTemplate,
    deleteTemplatePatch,
    error,
    mergePreview,
    mergeProfilePreview,
    mergeProfilePreviewName,
    mergeProfiles,
    notice,
    previewCompositeTemplate,
    previewTemplatePatch,
    refreshAll,
    refreshRuleSource,
    ruleSources,
    runConvertPreview,
    runMergePreview,
    runMergeProfilePreview,
    showError,
    showNotice,
    subscriptions,
    templatePatchPreview,
    templatePatchPreviewName,
    templatePatches,
    templates,
    toggleSubscription,
    updateCompositeTemplate,
    updateMergeProfile,
    updateRuleSource,
    updateSubscription,
    updateTemplate,
    updateTemplatePatch,
  }
})
