async function readErrorMessage(response) {
    const fallback = `${response.status} ${response.statusText}`;
    const raw = await response.text();
    if (!raw) {
        return fallback;
    }
    try {
        const parsed = JSON.parse(raw);
        if (typeof parsed.detail === 'string') {
            return parsed.detail;
        }
        if (Array.isArray(parsed.detail)) {
            return parsed.detail
                .map((item) => (typeof item === 'string' ? item : JSON.stringify(item)))
                .join('\n');
        }
    }
    catch {
        return raw;
    }
    return raw;
}
async function request(path, init) {
    const response = await fetch(path, {
        headers: { 'Content-Type': 'application/json', ...(init?.headers ?? {}) },
        ...init,
    });
    if (!response.ok) {
        throw new Error(await readErrorMessage(response));
    }
    if (response.status === 204) {
        return undefined;
    }
    return (await response.json());
}
export const api = {
    listSubscriptions: () => request('/subscriptions'),
    createSubscription: (payload) => request('/subscriptions', { method: 'POST', body: JSON.stringify(payload) }),
    updateSubscription: (id, payload) => request(`/subscriptions/${id}`, { method: 'PUT', body: JSON.stringify(payload) }),
    deleteSubscription: (id) => request(`/subscriptions/${id}`, { method: 'DELETE' }),
    listTemplates: () => request('/templates'),
    createTemplate: (payload) => request('/templates', { method: 'POST', body: JSON.stringify(payload) }),
    updateTemplate: (id, payload) => request(`/templates/${id}`, { method: 'PUT', body: JSON.stringify(payload) }),
    deleteTemplate: (id) => request(`/templates/${id}`, { method: 'DELETE' }),
    listRuleSources: () => request('/rule-sources'),
    createRuleSource: (payload) => request('/rule-sources', { method: 'POST', body: JSON.stringify(payload) }),
    updateRuleSource: (id, payload) => request(`/rule-sources/${id}`, { method: 'PUT', body: JSON.stringify(payload) }),
    refreshRuleSource: (id) => request(`/rule-sources/${id}/update`, { method: 'POST' }),
    deleteRuleSource: (id) => request(`/rule-sources/${id}`, { method: 'DELETE' }),
    listRules: () => request('/rules'),
    listMergeProfiles: () => request('/merge-profiles'),
    createMergeProfile: (payload) => request('/merge-profiles', { method: 'POST', body: JSON.stringify(payload) }),
    updateMergeProfile: (id, payload) => request(`/merge-profiles/${id}`, { method: 'PUT', body: JSON.stringify(payload) }),
    deleteMergeProfile: (id) => request(`/merge-profiles/${id}`, { method: 'DELETE' }),
    generateMergeProfile: (id) => request(`/merge-profiles/${id}/generate`, { method: 'POST' }),
    convertPreview: (payload) => request('/convert', { method: 'POST', body: JSON.stringify(payload) }),
    mergePreview: (payload) => request('/merge', { method: 'POST', body: JSON.stringify(payload) }),
};
