import { storeToRefs } from 'pinia';
import { computed, reactive, ref } from 'vue';
import { useManagerStore } from '../stores/manager';
const store = useManagerStore();
const { busy, subscriptions, templates } = storeToRefs(store);
const dialog = ref(false);
const editingId = ref(null);
const sourceMode = ref('content');
const form = reactive({
    name: '',
    source: '',
    proxy: '',
    followRedirects: true,
    enabled: true,
    templateId: null,
});
const headers = [
    { title: '名称', key: 'name' },
    { title: '来源', key: 'source' },
    { title: '模板', key: 'template' },
    { title: '状态', key: 'status', sortable: false },
    { title: '操作', key: 'actions', sortable: false, align: 'end' },
];
const sourceLabel = computed(() => {
    return sourceMode.value === 'content' ? '内联内容或分享链接' : '订阅 URL';
});
const dialogTitle = computed(() => {
    return editingId.value === null ? '新建订阅' : '编辑订阅';
});
const canSubmit = computed(() => {
    return form.name.trim().length > 0 && form.source.trim().length > 0;
});
function resetForm() {
    editingId.value = null;
    sourceMode.value = 'content';
    form.name = '';
    form.source = '';
    form.proxy = '';
    form.followRedirects = true;
    form.enabled = true;
    form.templateId = null;
}
function templateNameFor(subscription) {
    return templates.value.find((template) => template.id === subscription.template_id)?.name ?? '未指定';
}
function openCreateDialog() {
    resetForm();
    dialog.value = true;
}
function openEditDialog(subscription) {
    editingId.value = subscription.id;
    sourceMode.value = subscription.url ? 'url' : 'content';
    form.name = subscription.name;
    form.source = subscription.url ?? subscription.content ?? '';
    form.proxy = subscription.proxy ?? '';
    form.followRedirects = subscription.follow_redirects;
    form.enabled = subscription.enabled;
    form.templateId = subscription.template_id;
    dialog.value = true;
}
async function saveSubscription() {
    const payload = {
        name: form.name.trim(),
        proxy: form.proxy.trim() ? form.proxy.trim() : null,
        follow_redirects: form.followRedirects,
        enabled: form.enabled,
        template_id: form.templateId,
    };
    if (sourceMode.value === 'content') {
        payload.content = form.source.trim();
    }
    else {
        payload.url = form.source.trim();
    }
    const succeeded = editingId.value === null
        ? await store.createSubscription(payload)
        : await store.updateSubscription(editingId.value, payload);
    if (succeeded) {
        dialog.value = false;
        resetForm();
    }
}
const __VLS_ctx = {
    ...{},
    ...{},
};
let __VLS_components;
let __VLS_intrinsics;
let __VLS_directives;
let __VLS_0;
/** @ts-ignore @type {typeof __VLS_components.vCard | typeof __VLS_components.VCard | typeof __VLS_components.vCard | typeof __VLS_components.VCard} */
vCard;
// @ts-ignore
const __VLS_1 = __VLS_asFunctionalComponent1(__VLS_0, new __VLS_0({}));
const __VLS_2 = __VLS_1({}, ...__VLS_functionalComponentArgsRest(__VLS_1));
const { default: __VLS_5 } = __VLS_3.slots;
let __VLS_6;
/** @ts-ignore @type {typeof __VLS_components.vCardItem | typeof __VLS_components.VCardItem | typeof __VLS_components.vCardItem | typeof __VLS_components.VCardItem} */
vCardItem;
// @ts-ignore
const __VLS_7 = __VLS_asFunctionalComponent1(__VLS_6, new __VLS_6({}));
const __VLS_8 = __VLS_7({}, ...__VLS_functionalComponentArgsRest(__VLS_7));
const { default: __VLS_11 } = __VLS_9.slots;
__VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "d-flex flex-column flex-sm-row ga-4 align-sm-center justify-space-between" },
});
/** @type {__VLS_StyleScopedClasses['d-flex']} */ ;
/** @type {__VLS_StyleScopedClasses['flex-column']} */ ;
/** @type {__VLS_StyleScopedClasses['flex-sm-row']} */ ;
/** @type {__VLS_StyleScopedClasses['ga-4']} */ ;
/** @type {__VLS_StyleScopedClasses['align-sm-center']} */ ;
/** @type {__VLS_StyleScopedClasses['justify-space-between']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({});
let __VLS_12;
/** @ts-ignore @type {typeof __VLS_components.vCardTitle | typeof __VLS_components.VCardTitle | typeof __VLS_components.vCardTitle | typeof __VLS_components.VCardTitle} */
vCardTitle;
// @ts-ignore
const __VLS_13 = __VLS_asFunctionalComponent1(__VLS_12, new __VLS_12({
    ...{ class: "px-0" },
}));
const __VLS_14 = __VLS_13({
    ...{ class: "px-0" },
}, ...__VLS_functionalComponentArgsRest(__VLS_13));
/** @type {__VLS_StyleScopedClasses['px-0']} */ ;
const { default: __VLS_17 } = __VLS_15.slots;
var __VLS_15;
let __VLS_18;
/** @ts-ignore @type {typeof __VLS_components.vCardSubtitle | typeof __VLS_components.VCardSubtitle | typeof __VLS_components.vCardSubtitle | typeof __VLS_components.VCardSubtitle} */
vCardSubtitle;
// @ts-ignore
const __VLS_19 = __VLS_asFunctionalComponent1(__VLS_18, new __VLS_18({
    ...{ class: "px-0" },
}));
const __VLS_20 = __VLS_19({
    ...{ class: "px-0" },
}, ...__VLS_functionalComponentArgsRest(__VLS_19));
/** @type {__VLS_StyleScopedClasses['px-0']} */ ;
const { default: __VLS_23 } = __VLS_21.slots;
var __VLS_21;
let __VLS_24;
/** @ts-ignore @type {typeof __VLS_components.vBtn | typeof __VLS_components.VBtn | typeof __VLS_components.vBtn | typeof __VLS_components.VBtn} */
vBtn;
// @ts-ignore
const __VLS_25 = __VLS_asFunctionalComponent1(__VLS_24, new __VLS_24({
    ...{ 'onClick': {} },
    color: "primary",
    prependIcon: "mdi-plus",
}));
const __VLS_26 = __VLS_25({
    ...{ 'onClick': {} },
    color: "primary",
    prependIcon: "mdi-plus",
}, ...__VLS_functionalComponentArgsRest(__VLS_25));
let __VLS_29;
const __VLS_30 = ({ click: {} },
    { onClick: (__VLS_ctx.openCreateDialog) });
const { default: __VLS_31 } = __VLS_27.slots;
// @ts-ignore
[openCreateDialog,];
var __VLS_27;
var __VLS_28;
// @ts-ignore
[];
var __VLS_9;
let __VLS_32;
/** @ts-ignore @type {typeof __VLS_components.vDataTable | typeof __VLS_components.VDataTable | typeof __VLS_components.vDataTable | typeof __VLS_components.VDataTable} */
vDataTable;
// @ts-ignore
const __VLS_33 = __VLS_asFunctionalComponent1(__VLS_32, new __VLS_32({
    headers: (__VLS_ctx.headers),
    items: (__VLS_ctx.subscriptions),
    itemValue: "id",
}));
const __VLS_34 = __VLS_33({
    headers: (__VLS_ctx.headers),
    items: (__VLS_ctx.subscriptions),
    itemValue: "id",
}, ...__VLS_functionalComponentArgsRest(__VLS_33));
const { default: __VLS_37 } = __VLS_35.slots;
{
    const { 'item.source': __VLS_38 } = __VLS_35.slots;
    const [{ item }] = __VLS_vSlot(__VLS_38);
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "d-flex flex-column py-2" },
    });
    /** @type {__VLS_StyleScopedClasses['d-flex']} */ ;
    /** @type {__VLS_StyleScopedClasses['flex-column']} */ ;
    /** @type {__VLS_StyleScopedClasses['py-2']} */ ;
    __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({
        ...{ class: "font-weight-medium" },
    });
    /** @type {__VLS_StyleScopedClasses['font-weight-medium']} */ ;
    (item.url ? '远程订阅' : '内联内容');
    __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({
        ...{ class: "text-caption text-medium-emphasis text-break" },
    });
    /** @type {__VLS_StyleScopedClasses['text-caption']} */ ;
    /** @type {__VLS_StyleScopedClasses['text-medium-emphasis']} */ ;
    /** @type {__VLS_StyleScopedClasses['text-break']} */ ;
    (item.url ?? '已保存到数据库');
    // @ts-ignore
    [headers, subscriptions,];
}
{
    const { 'item.template': __VLS_39 } = __VLS_35.slots;
    const [{ item }] = __VLS_vSlot(__VLS_39);
    let __VLS_40;
    /** @ts-ignore @type {typeof __VLS_components.vChip | typeof __VLS_components.VChip | typeof __VLS_components.vChip | typeof __VLS_components.VChip} */
    vChip;
    // @ts-ignore
    const __VLS_41 = __VLS_asFunctionalComponent1(__VLS_40, new __VLS_40({
        size: "small",
        variant: "tonal",
    }));
    const __VLS_42 = __VLS_41({
        size: "small",
        variant: "tonal",
    }, ...__VLS_functionalComponentArgsRest(__VLS_41));
    const { default: __VLS_45 } = __VLS_43.slots;
    (__VLS_ctx.templateNameFor(item));
    // @ts-ignore
    [templateNameFor,];
    var __VLS_43;
    // @ts-ignore
    [];
}
{
    const { 'item.status': __VLS_46 } = __VLS_35.slots;
    const [{ item }] = __VLS_vSlot(__VLS_46);
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "d-flex align-center ga-3 py-2" },
    });
    /** @type {__VLS_StyleScopedClasses['d-flex']} */ ;
    /** @type {__VLS_StyleScopedClasses['align-center']} */ ;
    /** @type {__VLS_StyleScopedClasses['ga-3']} */ ;
    /** @type {__VLS_StyleScopedClasses['py-2']} */ ;
    let __VLS_47;
    /** @ts-ignore @type {typeof __VLS_components.vSwitch | typeof __VLS_components.VSwitch} */
    vSwitch;
    // @ts-ignore
    const __VLS_48 = __VLS_asFunctionalComponent1(__VLS_47, new __VLS_47({
        ...{ 'onUpdate:modelValue': {} },
        modelValue: (item.enabled),
        color: "primary",
        hideDetails: true,
        inset: true,
    }));
    const __VLS_49 = __VLS_48({
        ...{ 'onUpdate:modelValue': {} },
        modelValue: (item.enabled),
        color: "primary",
        hideDetails: true,
        inset: true,
    }, ...__VLS_functionalComponentArgsRest(__VLS_48));
    let __VLS_52;
    const __VLS_53 = ({ 'update:modelValue': {} },
        { 'onUpdate:modelValue': (...[$event]) => {
                __VLS_ctx.store.toggleSubscription(item.id, Boolean($event));
                // @ts-ignore
                [store,];
            } });
    var __VLS_50;
    var __VLS_51;
    let __VLS_54;
    /** @ts-ignore @type {typeof __VLS_components.vChip | typeof __VLS_components.VChip | typeof __VLS_components.vChip | typeof __VLS_components.VChip} */
    vChip;
    // @ts-ignore
    const __VLS_55 = __VLS_asFunctionalComponent1(__VLS_54, new __VLS_54({
        color: (item.enabled ? 'primary' : 'default'),
        size: "small",
        variant: "tonal",
    }));
    const __VLS_56 = __VLS_55({
        color: (item.enabled ? 'primary' : 'default'),
        size: "small",
        variant: "tonal",
    }, ...__VLS_functionalComponentArgsRest(__VLS_55));
    const { default: __VLS_59 } = __VLS_57.slots;
    (item.enabled ? '启用' : '停用');
    // @ts-ignore
    [];
    var __VLS_57;
    // @ts-ignore
    [];
}
{
    const { 'item.actions': __VLS_60 } = __VLS_35.slots;
    const [{ item }] = __VLS_vSlot(__VLS_60);
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "d-flex justify-end ga-2 py-2" },
    });
    /** @type {__VLS_StyleScopedClasses['d-flex']} */ ;
    /** @type {__VLS_StyleScopedClasses['justify-end']} */ ;
    /** @type {__VLS_StyleScopedClasses['ga-2']} */ ;
    /** @type {__VLS_StyleScopedClasses['py-2']} */ ;
    let __VLS_61;
    /** @ts-ignore @type {typeof __VLS_components.vBtn | typeof __VLS_components.VBtn} */
    vBtn;
    // @ts-ignore
    const __VLS_62 = __VLS_asFunctionalComponent1(__VLS_61, new __VLS_61({
        ...{ 'onClick': {} },
        icon: "mdi-pencil",
        size: "small",
        variant: "text",
    }));
    const __VLS_63 = __VLS_62({
        ...{ 'onClick': {} },
        icon: "mdi-pencil",
        size: "small",
        variant: "text",
    }, ...__VLS_functionalComponentArgsRest(__VLS_62));
    let __VLS_66;
    const __VLS_67 = ({ click: {} },
        { onClick: (...[$event]) => {
                __VLS_ctx.openEditDialog(item);
                // @ts-ignore
                [openEditDialog,];
            } });
    var __VLS_64;
    var __VLS_65;
    let __VLS_68;
    /** @ts-ignore @type {typeof __VLS_components.vBtn | typeof __VLS_components.VBtn} */
    vBtn;
    // @ts-ignore
    const __VLS_69 = __VLS_asFunctionalComponent1(__VLS_68, new __VLS_68({
        ...{ 'onClick': {} },
        icon: "mdi-delete-outline",
        size: "small",
        variant: "text",
        color: "error",
    }));
    const __VLS_70 = __VLS_69({
        ...{ 'onClick': {} },
        icon: "mdi-delete-outline",
        size: "small",
        variant: "text",
        color: "error",
    }, ...__VLS_functionalComponentArgsRest(__VLS_69));
    let __VLS_73;
    const __VLS_74 = ({ click: {} },
        { onClick: (...[$event]) => {
                __VLS_ctx.store.deleteSubscription(item.id);
                // @ts-ignore
                [store,];
            } });
    var __VLS_71;
    var __VLS_72;
    // @ts-ignore
    [];
}
// @ts-ignore
[];
var __VLS_35;
// @ts-ignore
[];
var __VLS_3;
let __VLS_75;
/** @ts-ignore @type {typeof __VLS_components.vDialog | typeof __VLS_components.VDialog | typeof __VLS_components.vDialog | typeof __VLS_components.VDialog} */
vDialog;
// @ts-ignore
const __VLS_76 = __VLS_asFunctionalComponent1(__VLS_75, new __VLS_75({
    modelValue: (__VLS_ctx.dialog),
}));
const __VLS_77 = __VLS_76({
    modelValue: (__VLS_ctx.dialog),
}, ...__VLS_functionalComponentArgsRest(__VLS_76));
const { default: __VLS_80 } = __VLS_78.slots;
let __VLS_81;
/** @ts-ignore @type {typeof __VLS_components.vCard | typeof __VLS_components.VCard | typeof __VLS_components.vCard | typeof __VLS_components.VCard} */
vCard;
// @ts-ignore
const __VLS_82 = __VLS_asFunctionalComponent1(__VLS_81, new __VLS_81({}));
const __VLS_83 = __VLS_82({}, ...__VLS_functionalComponentArgsRest(__VLS_82));
const { default: __VLS_86 } = __VLS_84.slots;
let __VLS_87;
/** @ts-ignore @type {typeof __VLS_components.vCardItem | typeof __VLS_components.VCardItem | typeof __VLS_components.vCardItem | typeof __VLS_components.VCardItem} */
vCardItem;
// @ts-ignore
const __VLS_88 = __VLS_asFunctionalComponent1(__VLS_87, new __VLS_87({}));
const __VLS_89 = __VLS_88({}, ...__VLS_functionalComponentArgsRest(__VLS_88));
const { default: __VLS_92 } = __VLS_90.slots;
let __VLS_93;
/** @ts-ignore @type {typeof __VLS_components.vCardTitle | typeof __VLS_components.VCardTitle | typeof __VLS_components.vCardTitle | typeof __VLS_components.VCardTitle} */
vCardTitle;
// @ts-ignore
const __VLS_94 = __VLS_asFunctionalComponent1(__VLS_93, new __VLS_93({}));
const __VLS_95 = __VLS_94({}, ...__VLS_functionalComponentArgsRest(__VLS_94));
const { default: __VLS_98 } = __VLS_96.slots;
(__VLS_ctx.dialogTitle);
// @ts-ignore
[dialog, dialogTitle,];
var __VLS_96;
let __VLS_99;
/** @ts-ignore @type {typeof __VLS_components.vCardSubtitle | typeof __VLS_components.VCardSubtitle | typeof __VLS_components.vCardSubtitle | typeof __VLS_components.VCardSubtitle} */
vCardSubtitle;
// @ts-ignore
const __VLS_100 = __VLS_asFunctionalComponent1(__VLS_99, new __VLS_99({}));
const __VLS_101 = __VLS_100({}, ...__VLS_functionalComponentArgsRest(__VLS_100));
const { default: __VLS_104 } = __VLS_102.slots;
// @ts-ignore
[];
var __VLS_102;
// @ts-ignore
[];
var __VLS_90;
let __VLS_105;
/** @ts-ignore @type {typeof __VLS_components.vCardText | typeof __VLS_components.VCardText | typeof __VLS_components.vCardText | typeof __VLS_components.VCardText} */
vCardText;
// @ts-ignore
const __VLS_106 = __VLS_asFunctionalComponent1(__VLS_105, new __VLS_105({}));
const __VLS_107 = __VLS_106({}, ...__VLS_functionalComponentArgsRest(__VLS_106));
const { default: __VLS_110 } = __VLS_108.slots;
let __VLS_111;
/** @ts-ignore @type {typeof __VLS_components.vRow | typeof __VLS_components.VRow | typeof __VLS_components.vRow | typeof __VLS_components.VRow} */
vRow;
// @ts-ignore
const __VLS_112 = __VLS_asFunctionalComponent1(__VLS_111, new __VLS_111({}));
const __VLS_113 = __VLS_112({}, ...__VLS_functionalComponentArgsRest(__VLS_112));
const { default: __VLS_116 } = __VLS_114.slots;
let __VLS_117;
/** @ts-ignore @type {typeof __VLS_components.vCol | typeof __VLS_components.VCol | typeof __VLS_components.vCol | typeof __VLS_components.VCol} */
vCol;
// @ts-ignore
const __VLS_118 = __VLS_asFunctionalComponent1(__VLS_117, new __VLS_117({
    cols: "12",
    md: "6",
}));
const __VLS_119 = __VLS_118({
    cols: "12",
    md: "6",
}, ...__VLS_functionalComponentArgsRest(__VLS_118));
const { default: __VLS_122 } = __VLS_120.slots;
let __VLS_123;
/** @ts-ignore @type {typeof __VLS_components.vTextField | typeof __VLS_components.VTextField} */
vTextField;
// @ts-ignore
const __VLS_124 = __VLS_asFunctionalComponent1(__VLS_123, new __VLS_123({
    modelValue: (__VLS_ctx.form.name),
    label: "名称",
    maxlength: "255",
}));
const __VLS_125 = __VLS_124({
    modelValue: (__VLS_ctx.form.name),
    label: "名称",
    maxlength: "255",
}, ...__VLS_functionalComponentArgsRest(__VLS_124));
// @ts-ignore
[form,];
var __VLS_120;
let __VLS_128;
/** @ts-ignore @type {typeof __VLS_components.vCol | typeof __VLS_components.VCol | typeof __VLS_components.vCol | typeof __VLS_components.VCol} */
vCol;
// @ts-ignore
const __VLS_129 = __VLS_asFunctionalComponent1(__VLS_128, new __VLS_128({
    cols: "12",
    md: "6",
}));
const __VLS_130 = __VLS_129({
    cols: "12",
    md: "6",
}, ...__VLS_functionalComponentArgsRest(__VLS_129));
const { default: __VLS_133 } = __VLS_131.slots;
let __VLS_134;
/** @ts-ignore @type {typeof __VLS_components.vSelect | typeof __VLS_components.VSelect} */
vSelect;
// @ts-ignore
const __VLS_135 = __VLS_asFunctionalComponent1(__VLS_134, new __VLS_134({
    modelValue: (__VLS_ctx.form.templateId),
    items: (__VLS_ctx.templates),
    itemTitle: "name",
    itemValue: "id",
    label: "关联模板",
    clearable: true,
}));
const __VLS_136 = __VLS_135({
    modelValue: (__VLS_ctx.form.templateId),
    items: (__VLS_ctx.templates),
    itemTitle: "name",
    itemValue: "id",
    label: "关联模板",
    clearable: true,
}, ...__VLS_functionalComponentArgsRest(__VLS_135));
// @ts-ignore
[form, templates,];
var __VLS_131;
let __VLS_139;
/** @ts-ignore @type {typeof __VLS_components.vCol | typeof __VLS_components.VCol | typeof __VLS_components.vCol | typeof __VLS_components.VCol} */
vCol;
// @ts-ignore
const __VLS_140 = __VLS_asFunctionalComponent1(__VLS_139, new __VLS_139({
    cols: "12",
}));
const __VLS_141 = __VLS_140({
    cols: "12",
}, ...__VLS_functionalComponentArgsRest(__VLS_140));
const { default: __VLS_144 } = __VLS_142.slots;
let __VLS_145;
/** @ts-ignore @type {typeof __VLS_components.vBtnToggle | typeof __VLS_components.VBtnToggle | typeof __VLS_components.vBtnToggle | typeof __VLS_components.VBtnToggle} */
vBtnToggle;
// @ts-ignore
const __VLS_146 = __VLS_asFunctionalComponent1(__VLS_145, new __VLS_145({
    modelValue: (__VLS_ctx.sourceMode),
    color: "primary",
    mandatory: true,
}));
const __VLS_147 = __VLS_146({
    modelValue: (__VLS_ctx.sourceMode),
    color: "primary",
    mandatory: true,
}, ...__VLS_functionalComponentArgsRest(__VLS_146));
const { default: __VLS_150 } = __VLS_148.slots;
let __VLS_151;
/** @ts-ignore @type {typeof __VLS_components.vBtn | typeof __VLS_components.VBtn | typeof __VLS_components.vBtn | typeof __VLS_components.VBtn} */
vBtn;
// @ts-ignore
const __VLS_152 = __VLS_asFunctionalComponent1(__VLS_151, new __VLS_151({
    value: "content",
}));
const __VLS_153 = __VLS_152({
    value: "content",
}, ...__VLS_functionalComponentArgsRest(__VLS_152));
const { default: __VLS_156 } = __VLS_154.slots;
// @ts-ignore
[sourceMode,];
var __VLS_154;
let __VLS_157;
/** @ts-ignore @type {typeof __VLS_components.vBtn | typeof __VLS_components.VBtn | typeof __VLS_components.vBtn | typeof __VLS_components.VBtn} */
vBtn;
// @ts-ignore
const __VLS_158 = __VLS_asFunctionalComponent1(__VLS_157, new __VLS_157({
    value: "url",
}));
const __VLS_159 = __VLS_158({
    value: "url",
}, ...__VLS_functionalComponentArgsRest(__VLS_158));
const { default: __VLS_162 } = __VLS_160.slots;
// @ts-ignore
[];
var __VLS_160;
// @ts-ignore
[];
var __VLS_148;
// @ts-ignore
[];
var __VLS_142;
let __VLS_163;
/** @ts-ignore @type {typeof __VLS_components.vCol | typeof __VLS_components.VCol | typeof __VLS_components.vCol | typeof __VLS_components.VCol} */
vCol;
// @ts-ignore
const __VLS_164 = __VLS_asFunctionalComponent1(__VLS_163, new __VLS_163({
    cols: "12",
}));
const __VLS_165 = __VLS_164({
    cols: "12",
}, ...__VLS_functionalComponentArgsRest(__VLS_164));
const { default: __VLS_168 } = __VLS_166.slots;
let __VLS_169;
/** @ts-ignore @type {typeof __VLS_components.vTextarea | typeof __VLS_components.VTextarea} */
vTextarea;
// @ts-ignore
const __VLS_170 = __VLS_asFunctionalComponent1(__VLS_169, new __VLS_169({
    modelValue: (__VLS_ctx.form.source),
    label: (__VLS_ctx.sourceLabel),
    rows: "8",
}));
const __VLS_171 = __VLS_170({
    modelValue: (__VLS_ctx.form.source),
    label: (__VLS_ctx.sourceLabel),
    rows: "8",
}, ...__VLS_functionalComponentArgsRest(__VLS_170));
// @ts-ignore
[form, sourceLabel,];
var __VLS_166;
let __VLS_174;
/** @ts-ignore @type {typeof __VLS_components.vCol | typeof __VLS_components.VCol | typeof __VLS_components.vCol | typeof __VLS_components.VCol} */
vCol;
// @ts-ignore
const __VLS_175 = __VLS_asFunctionalComponent1(__VLS_174, new __VLS_174({
    cols: "12",
    md: "6",
}));
const __VLS_176 = __VLS_175({
    cols: "12",
    md: "6",
}, ...__VLS_functionalComponentArgsRest(__VLS_175));
const { default: __VLS_179 } = __VLS_177.slots;
let __VLS_180;
/** @ts-ignore @type {typeof __VLS_components.vTextField | typeof __VLS_components.VTextField} */
vTextField;
// @ts-ignore
const __VLS_181 = __VLS_asFunctionalComponent1(__VLS_180, new __VLS_180({
    modelValue: (__VLS_ctx.form.proxy),
    label: "代理 URL（可选）",
    placeholder: "http://127.0.0.1:7890",
}));
const __VLS_182 = __VLS_181({
    modelValue: (__VLS_ctx.form.proxy),
    label: "代理 URL（可选）",
    placeholder: "http://127.0.0.1:7890",
}, ...__VLS_functionalComponentArgsRest(__VLS_181));
// @ts-ignore
[form,];
var __VLS_177;
let __VLS_185;
/** @ts-ignore @type {typeof __VLS_components.vCol | typeof __VLS_components.VCol | typeof __VLS_components.vCol | typeof __VLS_components.VCol} */
vCol;
// @ts-ignore
const __VLS_186 = __VLS_asFunctionalComponent1(__VLS_185, new __VLS_185({
    cols: "12",
    md: "3",
}));
const __VLS_187 = __VLS_186({
    cols: "12",
    md: "3",
}, ...__VLS_functionalComponentArgsRest(__VLS_186));
const { default: __VLS_190 } = __VLS_188.slots;
let __VLS_191;
/** @ts-ignore @type {typeof __VLS_components.vSwitch | typeof __VLS_components.VSwitch} */
vSwitch;
// @ts-ignore
const __VLS_192 = __VLS_asFunctionalComponent1(__VLS_191, new __VLS_191({
    modelValue: (__VLS_ctx.form.followRedirects),
    label: "跟随重定向",
    hideDetails: true,
}));
const __VLS_193 = __VLS_192({
    modelValue: (__VLS_ctx.form.followRedirects),
    label: "跟随重定向",
    hideDetails: true,
}, ...__VLS_functionalComponentArgsRest(__VLS_192));
// @ts-ignore
[form,];
var __VLS_188;
let __VLS_196;
/** @ts-ignore @type {typeof __VLS_components.vCol | typeof __VLS_components.VCol | typeof __VLS_components.vCol | typeof __VLS_components.VCol} */
vCol;
// @ts-ignore
const __VLS_197 = __VLS_asFunctionalComponent1(__VLS_196, new __VLS_196({
    cols: "12",
    md: "3",
}));
const __VLS_198 = __VLS_197({
    cols: "12",
    md: "3",
}, ...__VLS_functionalComponentArgsRest(__VLS_197));
const { default: __VLS_201 } = __VLS_199.slots;
let __VLS_202;
/** @ts-ignore @type {typeof __VLS_components.vSwitch | typeof __VLS_components.VSwitch} */
vSwitch;
// @ts-ignore
const __VLS_203 = __VLS_asFunctionalComponent1(__VLS_202, new __VLS_202({
    modelValue: (__VLS_ctx.form.enabled),
    label: "启用",
    hideDetails: true,
}));
const __VLS_204 = __VLS_203({
    modelValue: (__VLS_ctx.form.enabled),
    label: "启用",
    hideDetails: true,
}, ...__VLS_functionalComponentArgsRest(__VLS_203));
// @ts-ignore
[form,];
var __VLS_199;
// @ts-ignore
[];
var __VLS_114;
// @ts-ignore
[];
var __VLS_108;
let __VLS_207;
/** @ts-ignore @type {typeof __VLS_components.vCardActions | typeof __VLS_components.VCardActions | typeof __VLS_components.vCardActions | typeof __VLS_components.VCardActions} */
vCardActions;
// @ts-ignore
const __VLS_208 = __VLS_asFunctionalComponent1(__VLS_207, new __VLS_207({}));
const __VLS_209 = __VLS_208({}, ...__VLS_functionalComponentArgsRest(__VLS_208));
const { default: __VLS_212 } = __VLS_210.slots;
let __VLS_213;
/** @ts-ignore @type {typeof __VLS_components.vSpacer | typeof __VLS_components.VSpacer} */
vSpacer;
// @ts-ignore
const __VLS_214 = __VLS_asFunctionalComponent1(__VLS_213, new __VLS_213({}));
const __VLS_215 = __VLS_214({}, ...__VLS_functionalComponentArgsRest(__VLS_214));
let __VLS_218;
/** @ts-ignore @type {typeof __VLS_components.vBtn | typeof __VLS_components.VBtn | typeof __VLS_components.vBtn | typeof __VLS_components.VBtn} */
vBtn;
// @ts-ignore
const __VLS_219 = __VLS_asFunctionalComponent1(__VLS_218, new __VLS_218({
    ...{ 'onClick': {} },
    variant: "text",
}));
const __VLS_220 = __VLS_219({
    ...{ 'onClick': {} },
    variant: "text",
}, ...__VLS_functionalComponentArgsRest(__VLS_219));
let __VLS_223;
const __VLS_224 = ({ click: {} },
    { onClick: (...[$event]) => {
            __VLS_ctx.dialog = false;
            // @ts-ignore
            [dialog,];
        } });
const { default: __VLS_225 } = __VLS_221.slots;
// @ts-ignore
[];
var __VLS_221;
var __VLS_222;
let __VLS_226;
/** @ts-ignore @type {typeof __VLS_components.vBtn | typeof __VLS_components.VBtn | typeof __VLS_components.vBtn | typeof __VLS_components.VBtn} */
vBtn;
// @ts-ignore
const __VLS_227 = __VLS_asFunctionalComponent1(__VLS_226, new __VLS_226({
    ...{ 'onClick': {} },
    color: "primary",
    disabled: (__VLS_ctx.busy || !__VLS_ctx.canSubmit),
}));
const __VLS_228 = __VLS_227({
    ...{ 'onClick': {} },
    color: "primary",
    disabled: (__VLS_ctx.busy || !__VLS_ctx.canSubmit),
}, ...__VLS_functionalComponentArgsRest(__VLS_227));
let __VLS_231;
const __VLS_232 = ({ click: {} },
    { onClick: (__VLS_ctx.saveSubscription) });
const { default: __VLS_233 } = __VLS_229.slots;
// @ts-ignore
[busy, canSubmit, saveSubscription,];
var __VLS_229;
var __VLS_230;
// @ts-ignore
[];
var __VLS_210;
// @ts-ignore
[];
var __VLS_84;
// @ts-ignore
[];
var __VLS_78;
// @ts-ignore
[];
const __VLS_export = (await import('vue')).defineComponent({});
export default {};
