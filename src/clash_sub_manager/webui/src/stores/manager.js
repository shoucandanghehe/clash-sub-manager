import { dump as dumpYaml, load as loadYaml } from 'js-yaml';
import { defineStore } from 'pinia';
import { ref } from 'vue';
import { api, } from '../api';
function toMessage(caught) {
    return caught instanceof Error ? caught.message : '发生未知错误';
}
function formatDocument(document) {
    return dumpYaml(document, {
        lineWidth: -1,
        noRefs: true,
    });
}
function parseTemplateContent(content) {
    const parsed = loadYaml(content);
    if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) {
        throw new Error('模板内容必须是 YAML 映射对象。');
    }
    return parsed;
}
export const useManagerStore = defineStore('manager', () => {
    const subscriptions = ref([]);
    const templates = ref([]);
    const ruleSources = ref([]);
    const rules = ref([]);
    const mergeProfiles = ref([]);
    const convertPreview = ref('');
    const mergePreview = ref('');
    const mergeProfilePreview = ref('');
    const mergeProfilePreviewName = ref('');
    const busy = ref(false);
    const error = ref('');
    const notice = ref('');
    function clearNotice() {
        notice.value = '';
    }
    function clearError() {
        error.value = '';
    }
    function clearMessages() {
        clearNotice();
        clearError();
    }
    function setError(message) {
        error.value = message;
        if (message) {
            notice.value = '';
        }
    }
    function setNotice(message) {
        notice.value = message;
        if (message) {
            error.value = '';
        }
    }
    async function run(label, action) {
        busy.value = true;
        clearMessages();
        try {
            await action();
            setNotice(label);
            return true;
        }
        catch (caught) {
            setError(toMessage(caught));
            return false;
        }
        finally {
            busy.value = false;
        }
    }
    async function reloadSubscriptions() {
        subscriptions.value = await api.listSubscriptions();
    }
    async function reloadTemplates() {
        templates.value = await api.listTemplates();
    }
    async function reloadRuleSources() {
        ruleSources.value = await api.listRuleSources();
    }
    async function reloadRules() {
        rules.value = await api.listRules();
    }
    async function reloadMergeProfiles() {
        mergeProfiles.value = await api.listMergeProfiles();
    }
    async function refreshAll() {
        return run('数据已刷新。', async () => {
            await Promise.all([
                reloadSubscriptions(),
                reloadTemplates(),
                reloadRuleSources(),
                reloadRules(),
                reloadMergeProfiles(),
            ]);
        });
    }
    async function createSubscription(payload) {
        return run('订阅已创建。', async () => {
            await api.createSubscription(payload);
            await Promise.all([reloadSubscriptions(), reloadMergeProfiles()]);
        });
    }
    async function updateSubscription(id, payload) {
        return run('订阅已更新。', async () => {
            await api.updateSubscription(id, payload);
            await Promise.all([reloadSubscriptions(), reloadMergeProfiles()]);
        });
    }
    async function toggleSubscription(id, enabled) {
        return updateSubscription(id, { enabled });
    }
    async function deleteSubscription(id) {
        return run('订阅已删除。', async () => {
            await api.deleteSubscription(id);
            await Promise.all([reloadSubscriptions(), reloadMergeProfiles()]);
        });
    }
    async function createTemplate(payload) {
        return run('模板已创建。', async () => {
            await api.createTemplate(payload);
            await Promise.all([reloadTemplates(), reloadMergeProfiles()]);
        });
    }
    async function updateTemplate(id, payload) {
        return run('模板已更新。', async () => {
            await api.updateTemplate(id, payload);
            await Promise.all([reloadTemplates(), reloadMergeProfiles()]);
        });
    }
    async function deleteTemplate(id) {
        return run('模板已删除。', async () => {
            await api.deleteTemplate(id);
            await Promise.all([reloadTemplates(), reloadMergeProfiles()]);
        });
    }
    async function createRuleSource(payload) {
        return run('规则源已创建。', async () => {
            await api.createRuleSource(payload);
            await Promise.all([reloadRuleSources(), reloadRules()]);
        });
    }
    async function updateRuleSource(id, payload) {
        return run('规则源已更新。', async () => {
            await api.updateRuleSource(id, payload);
            await Promise.all([reloadRuleSources(), reloadRules()]);
        });
    }
    async function refreshRuleSource(id) {
        return run('规则源已刷新。', async () => {
            await api.refreshRuleSource(id);
            await Promise.all([reloadRuleSources(), reloadRules()]);
        });
    }
    async function deleteRuleSource(id) {
        return run('规则源已删除。', async () => {
            await api.deleteRuleSource(id);
            await Promise.all([reloadRuleSources(), reloadRules()]);
        });
    }
    async function createMergeProfile(payload) {
        return run('合并配置已创建。', async () => {
            await api.createMergeProfile(payload);
            await reloadMergeProfiles();
        });
    }
    async function updateMergeProfile(id, payload) {
        return run('合并配置已更新。', async () => {
            await api.updateMergeProfile(id, payload);
            await reloadMergeProfiles();
        });
    }
    async function deleteMergeProfile(id) {
        return run('合并配置已删除。', async () => {
            await api.deleteMergeProfile(id);
            await reloadMergeProfiles();
        });
    }
    async function runConvertPreview(payload) {
        return run('已生成转换预览。', async () => {
            const result = await api.convertPreview(payload);
            convertPreview.value = formatDocument(result);
        });
    }
    async function runMergePreview(templateId) {
        return run('已生成合并预览。', async () => {
            const templateContent = templateId === null
                ? undefined
                : templates.value.find((template) => template.id === templateId)?.content;
            const template = templateContent ? parseTemplateContent(templateContent) : undefined;
            const payload = {
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
            };
            const result = await api.mergePreview(payload);
            mergePreview.value = formatDocument(result);
        });
    }
    async function runMergeProfilePreview(id) {
        return run('已生成合并配置预览。', async () => {
            const result = await api.generateMergeProfile(id);
            mergeProfilePreview.value = formatDocument(result);
            mergeProfilePreviewName.value = mergeProfiles.value.find((profile) => profile.id === id)?.name ?? '合并配置';
        });
    }
    return {
        busy,
        clearError,
        clearMessages,
        clearNotice,
        convertPreview,
        createMergeProfile,
        createRuleSource,
        createSubscription,
        createTemplate,
        deleteMergeProfile,
        deleteRuleSource,
        deleteSubscription,
        deleteTemplate,
        error,
        mergePreview,
        mergeProfilePreview,
        mergeProfilePreviewName,
        mergeProfiles,
        notice,
        refreshAll,
        refreshRuleSource,
        ruleSources,
        rules,
        runConvertPreview,
        runMergePreview,
        runMergeProfilePreview,
        subscriptions,
        templates,
        toggleSubscription,
        updateMergeProfile,
        updateRuleSource,
        updateSubscription,
        updateTemplate,
    };
});
