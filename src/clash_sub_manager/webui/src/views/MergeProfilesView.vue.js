import { storeToRefs } from 'pinia';
import { computed, reactive, ref } from 'vue';
import { useManagerStore } from '../stores/manager';
const emit = defineEmits();
const store = useManagerStore();
const { busy, mergeProfiles, subscriptions, templates } = storeToRefs(store);
const dialog = ref(false);
const editingId = ref(null);
const form = reactive({
    name: '',
    templateId: null,
    subscriptionIds: [],
    enabled: true,
});
const headers = [
    { title: '名称', key: 'name' },
    { title: '订阅', key: 'subscriptions', sortable: false },
    { title: '模板', key: 'template' },
    { title: '状态', key: 'enabled' },
    { title: '操作', key: 'actions', sortable: false, align: 'end' },
];
const dialogTitle = computed(() => {
    return editingId.value === null ? '新建合并配置' : '编辑合并配置';
});
const canSubmit = computed(() => {
    return form.name.trim().length > 0 && form.subscriptionIds.length > 0;
});
function resetForm() {
    editingId.value = null;
    form.name = '';
    form.templateId = null;
    form.subscriptionIds = [];
    form.enabled = true;
}
function openCreateDialog() {
    resetForm();
    dialog.value = true;
}
function openEditDialog(profile) {
    editingId.value = profile.id;
    form.name = profile.name;
    form.templateId = profile.template_id;
    form.subscriptionIds = profile.subscriptions.map((subscription) => subscription.id);
    form.enabled = profile.enabled;
    dialog.value = true;
}
async function saveProfile() {
    const payload = {
        name: form.name.trim(),
        template_id: form.templateId,
        enabled: form.enabled,
        subscription_ids: [...form.subscriptionIds],
    };
    const succeeded = editingId.value === null
        ? await store.createMergeProfile(payload)
        : await store.updateMergeProfile(editingId.value, payload);
    if (succeeded) {
        dialog.value = false;
        resetForm();
    }
}
async function generateProfile(profile) {
    if (await store.runMergeProfilePreview(profile.id)) {
        emit('navigatePreview');
    }
}
const __VLS_ctx = {
    ...{},
    ...{},
    ...{},
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
    items: (__VLS_ctx.mergeProfiles),
    itemValue: "id",
}));
const __VLS_34 = __VLS_33({
    headers: (__VLS_ctx.headers),
    items: (__VLS_ctx.mergeProfiles),
    itemValue: "id",
}, ...__VLS_functionalComponentArgsRest(__VLS_33));
const { default: __VLS_37 } = __VLS_35.slots;
{
    const { 'item.subscriptions': __VLS_38 } = __VLS_35.slots;
    const [{ item }] = __VLS_vSlot(__VLS_38);
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "d-flex flex-wrap ga-2 py-2" },
    });
    /** @type {__VLS_StyleScopedClasses['d-flex']} */ ;
    /** @type {__VLS_StyleScopedClasses['flex-wrap']} */ ;
    /** @type {__VLS_StyleScopedClasses['ga-2']} */ ;
    /** @type {__VLS_StyleScopedClasses['py-2']} */ ;
    for (const [subscription] of __VLS_vFor((item.subscriptions))) {
        let __VLS_39;
        /** @ts-ignore @type {typeof __VLS_components.vChip | typeof __VLS_components.VChip | typeof __VLS_components.vChip | typeof __VLS_components.VChip} */
        vChip;
        // @ts-ignore
        const __VLS_40 = __VLS_asFunctionalComponent1(__VLS_39, new __VLS_39({
            key: (subscription.id),
            size: "small",
            variant: "tonal",
        }));
        const __VLS_41 = __VLS_40({
            key: (subscription.id),
            size: "small",
            variant: "tonal",
        }, ...__VLS_functionalComponentArgsRest(__VLS_40));
        const { default: __VLS_44 } = __VLS_42.slots;
        (subscription.name);
        // @ts-ignore
        [headers, mergeProfiles,];
        var __VLS_42;
        // @ts-ignore
        [];
    }
    if (item.subscriptions.length === 0) {
        __VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({
            ...{ class: "text-caption text-medium-emphasis" },
        });
        /** @type {__VLS_StyleScopedClasses['text-caption']} */ ;
        /** @type {__VLS_StyleScopedClasses['text-medium-emphasis']} */ ;
    }
    // @ts-ignore
    [];
}
{
    const { 'item.template': __VLS_45 } = __VLS_35.slots;
    const [{ item }] = __VLS_vSlot(__VLS_45);
    let __VLS_46;
    /** @ts-ignore @type {typeof __VLS_components.vChip | typeof __VLS_components.VChip | typeof __VLS_components.vChip | typeof __VLS_components.VChip} */
    vChip;
    // @ts-ignore
    const __VLS_47 = __VLS_asFunctionalComponent1(__VLS_46, new __VLS_46({
        size: "small",
        variant: "tonal",
    }));
    const __VLS_48 = __VLS_47({
        size: "small",
        variant: "tonal",
    }, ...__VLS_functionalComponentArgsRest(__VLS_47));
    const { default: __VLS_51 } = __VLS_49.slots;
    (item.template?.name ?? '无模板');
    // @ts-ignore
    [];
    var __VLS_49;
    // @ts-ignore
    [];
}
{
    const { 'item.enabled': __VLS_52 } = __VLS_35.slots;
    const [{ item }] = __VLS_vSlot(__VLS_52);
    let __VLS_53;
    /** @ts-ignore @type {typeof __VLS_components.vChip | typeof __VLS_components.VChip | typeof __VLS_components.vChip | typeof __VLS_components.VChip} */
    vChip;
    // @ts-ignore
    const __VLS_54 = __VLS_asFunctionalComponent1(__VLS_53, new __VLS_53({
        color: (item.enabled ? 'primary' : 'default'),
        size: "small",
        variant: "tonal",
    }));
    const __VLS_55 = __VLS_54({
        color: (item.enabled ? 'primary' : 'default'),
        size: "small",
        variant: "tonal",
    }, ...__VLS_functionalComponentArgsRest(__VLS_54));
    const { default: __VLS_58 } = __VLS_56.slots;
    (item.enabled ? '启用' : '停用');
    // @ts-ignore
    [];
    var __VLS_56;
    // @ts-ignore
    [];
}
{
    const { 'item.actions': __VLS_59 } = __VLS_35.slots;
    const [{ item }] = __VLS_vSlot(__VLS_59);
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "d-flex justify-end ga-2 py-2" },
    });
    /** @type {__VLS_StyleScopedClasses['d-flex']} */ ;
    /** @type {__VLS_StyleScopedClasses['justify-end']} */ ;
    /** @type {__VLS_StyleScopedClasses['ga-2']} */ ;
    /** @type {__VLS_StyleScopedClasses['py-2']} */ ;
    let __VLS_60;
    /** @ts-ignore @type {typeof __VLS_components.vBtn | typeof __VLS_components.VBtn} */
    vBtn;
    // @ts-ignore
    const __VLS_61 = __VLS_asFunctionalComponent1(__VLS_60, new __VLS_60({
        ...{ 'onClick': {} },
        icon: "mdi-play-circle-outline",
        size: "small",
        variant: "text",
        color: "primary",
    }));
    const __VLS_62 = __VLS_61({
        ...{ 'onClick': {} },
        icon: "mdi-play-circle-outline",
        size: "small",
        variant: "text",
        color: "primary",
    }, ...__VLS_functionalComponentArgsRest(__VLS_61));
    let __VLS_65;
    const __VLS_66 = ({ click: {} },
        { onClick: (...[$event]) => {
                __VLS_ctx.generateProfile(item);
                // @ts-ignore
                [generateProfile,];
            } });
    var __VLS_63;
    var __VLS_64;
    let __VLS_67;
    /** @ts-ignore @type {typeof __VLS_components.vBtn | typeof __VLS_components.VBtn} */
    vBtn;
    // @ts-ignore
    const __VLS_68 = __VLS_asFunctionalComponent1(__VLS_67, new __VLS_67({
        ...{ 'onClick': {} },
        icon: "mdi-pencil",
        size: "small",
        variant: "text",
    }));
    const __VLS_69 = __VLS_68({
        ...{ 'onClick': {} },
        icon: "mdi-pencil",
        size: "small",
        variant: "text",
    }, ...__VLS_functionalComponentArgsRest(__VLS_68));
    let __VLS_72;
    const __VLS_73 = ({ click: {} },
        { onClick: (...[$event]) => {
                __VLS_ctx.openEditDialog(item);
                // @ts-ignore
                [openEditDialog,];
            } });
    var __VLS_70;
    var __VLS_71;
    let __VLS_74;
    /** @ts-ignore @type {typeof __VLS_components.vBtn | typeof __VLS_components.VBtn} */
    vBtn;
    // @ts-ignore
    const __VLS_75 = __VLS_asFunctionalComponent1(__VLS_74, new __VLS_74({
        ...{ 'onClick': {} },
        icon: "mdi-delete-outline",
        size: "small",
        variant: "text",
        color: "error",
    }));
    const __VLS_76 = __VLS_75({
        ...{ 'onClick': {} },
        icon: "mdi-delete-outline",
        size: "small",
        variant: "text",
        color: "error",
    }, ...__VLS_functionalComponentArgsRest(__VLS_75));
    let __VLS_79;
    const __VLS_80 = ({ click: {} },
        { onClick: (...[$event]) => {
                __VLS_ctx.store.deleteMergeProfile(item.id);
                // @ts-ignore
                [store,];
            } });
    var __VLS_77;
    var __VLS_78;
    // @ts-ignore
    [];
}
// @ts-ignore
[];
var __VLS_35;
// @ts-ignore
[];
var __VLS_3;
let __VLS_81;
/** @ts-ignore @type {typeof __VLS_components.vDialog | typeof __VLS_components.VDialog | typeof __VLS_components.vDialog | typeof __VLS_components.VDialog} */
vDialog;
// @ts-ignore
const __VLS_82 = __VLS_asFunctionalComponent1(__VLS_81, new __VLS_81({
    modelValue: (__VLS_ctx.dialog),
}));
const __VLS_83 = __VLS_82({
    modelValue: (__VLS_ctx.dialog),
}, ...__VLS_functionalComponentArgsRest(__VLS_82));
const { default: __VLS_86 } = __VLS_84.slots;
let __VLS_87;
/** @ts-ignore @type {typeof __VLS_components.vCard | typeof __VLS_components.VCard | typeof __VLS_components.vCard | typeof __VLS_components.VCard} */
vCard;
// @ts-ignore
const __VLS_88 = __VLS_asFunctionalComponent1(__VLS_87, new __VLS_87({}));
const __VLS_89 = __VLS_88({}, ...__VLS_functionalComponentArgsRest(__VLS_88));
const { default: __VLS_92 } = __VLS_90.slots;
let __VLS_93;
/** @ts-ignore @type {typeof __VLS_components.vCardItem | typeof __VLS_components.VCardItem | typeof __VLS_components.vCardItem | typeof __VLS_components.VCardItem} */
vCardItem;
// @ts-ignore
const __VLS_94 = __VLS_asFunctionalComponent1(__VLS_93, new __VLS_93({}));
const __VLS_95 = __VLS_94({}, ...__VLS_functionalComponentArgsRest(__VLS_94));
const { default: __VLS_98 } = __VLS_96.slots;
let __VLS_99;
/** @ts-ignore @type {typeof __VLS_components.vCardTitle | typeof __VLS_components.VCardTitle | typeof __VLS_components.vCardTitle | typeof __VLS_components.VCardTitle} */
vCardTitle;
// @ts-ignore
const __VLS_100 = __VLS_asFunctionalComponent1(__VLS_99, new __VLS_99({}));
const __VLS_101 = __VLS_100({}, ...__VLS_functionalComponentArgsRest(__VLS_100));
const { default: __VLS_104 } = __VLS_102.slots;
(__VLS_ctx.dialogTitle);
// @ts-ignore
[dialog, dialogTitle,];
var __VLS_102;
let __VLS_105;
/** @ts-ignore @type {typeof __VLS_components.vCardSubtitle | typeof __VLS_components.VCardSubtitle | typeof __VLS_components.vCardSubtitle | typeof __VLS_components.VCardSubtitle} */
vCardSubtitle;
// @ts-ignore
const __VLS_106 = __VLS_asFunctionalComponent1(__VLS_105, new __VLS_105({}));
const __VLS_107 = __VLS_106({}, ...__VLS_functionalComponentArgsRest(__VLS_106));
const { default: __VLS_110 } = __VLS_108.slots;
// @ts-ignore
[];
var __VLS_108;
// @ts-ignore
[];
var __VLS_96;
let __VLS_111;
/** @ts-ignore @type {typeof __VLS_components.vCardText | typeof __VLS_components.VCardText | typeof __VLS_components.vCardText | typeof __VLS_components.VCardText} */
vCardText;
// @ts-ignore
const __VLS_112 = __VLS_asFunctionalComponent1(__VLS_111, new __VLS_111({}));
const __VLS_113 = __VLS_112({}, ...__VLS_functionalComponentArgsRest(__VLS_112));
const { default: __VLS_116 } = __VLS_114.slots;
let __VLS_117;
/** @ts-ignore @type {typeof __VLS_components.vRow | typeof __VLS_components.VRow | typeof __VLS_components.vRow | typeof __VLS_components.VRow} */
vRow;
// @ts-ignore
const __VLS_118 = __VLS_asFunctionalComponent1(__VLS_117, new __VLS_117({}));
const __VLS_119 = __VLS_118({}, ...__VLS_functionalComponentArgsRest(__VLS_118));
const { default: __VLS_122 } = __VLS_120.slots;
let __VLS_123;
/** @ts-ignore @type {typeof __VLS_components.vCol | typeof __VLS_components.VCol | typeof __VLS_components.vCol | typeof __VLS_components.VCol} */
vCol;
// @ts-ignore
const __VLS_124 = __VLS_asFunctionalComponent1(__VLS_123, new __VLS_123({
    cols: "12",
    md: "6",
}));
const __VLS_125 = __VLS_124({
    cols: "12",
    md: "6",
}, ...__VLS_functionalComponentArgsRest(__VLS_124));
const { default: __VLS_128 } = __VLS_126.slots;
let __VLS_129;
/** @ts-ignore @type {typeof __VLS_components.vTextField | typeof __VLS_components.VTextField} */
vTextField;
// @ts-ignore
const __VLS_130 = __VLS_asFunctionalComponent1(__VLS_129, new __VLS_129({
    modelValue: (__VLS_ctx.form.name),
    label: "名称",
    maxlength: "255",
}));
const __VLS_131 = __VLS_130({
    modelValue: (__VLS_ctx.form.name),
    label: "名称",
    maxlength: "255",
}, ...__VLS_functionalComponentArgsRest(__VLS_130));
// @ts-ignore
[form,];
var __VLS_126;
let __VLS_134;
/** @ts-ignore @type {typeof __VLS_components.vCol | typeof __VLS_components.VCol | typeof __VLS_components.vCol | typeof __VLS_components.VCol} */
vCol;
// @ts-ignore
const __VLS_135 = __VLS_asFunctionalComponent1(__VLS_134, new __VLS_134({
    cols: "12",
    md: "6",
}));
const __VLS_136 = __VLS_135({
    cols: "12",
    md: "6",
}, ...__VLS_functionalComponentArgsRest(__VLS_135));
const { default: __VLS_139 } = __VLS_137.slots;
let __VLS_140;
/** @ts-ignore @type {typeof __VLS_components.vSelect | typeof __VLS_components.VSelect} */
vSelect;
// @ts-ignore
const __VLS_141 = __VLS_asFunctionalComponent1(__VLS_140, new __VLS_140({
    modelValue: (__VLS_ctx.form.templateId),
    items: (__VLS_ctx.templates),
    itemTitle: "name",
    itemValue: "id",
    label: "模板",
    clearable: true,
}));
const __VLS_142 = __VLS_141({
    modelValue: (__VLS_ctx.form.templateId),
    items: (__VLS_ctx.templates),
    itemTitle: "name",
    itemValue: "id",
    label: "模板",
    clearable: true,
}, ...__VLS_functionalComponentArgsRest(__VLS_141));
// @ts-ignore
[form, templates,];
var __VLS_137;
let __VLS_145;
/** @ts-ignore @type {typeof __VLS_components.vCol | typeof __VLS_components.VCol | typeof __VLS_components.vCol | typeof __VLS_components.VCol} */
vCol;
// @ts-ignore
const __VLS_146 = __VLS_asFunctionalComponent1(__VLS_145, new __VLS_145({
    cols: "12",
}));
const __VLS_147 = __VLS_146({
    cols: "12",
}, ...__VLS_functionalComponentArgsRest(__VLS_146));
const { default: __VLS_150 } = __VLS_148.slots;
let __VLS_151;
/** @ts-ignore @type {typeof __VLS_components.vAutocomplete | typeof __VLS_components.VAutocomplete} */
vAutocomplete;
// @ts-ignore
const __VLS_152 = __VLS_asFunctionalComponent1(__VLS_151, new __VLS_151({
    modelValue: (__VLS_ctx.form.subscriptionIds),
    items: (__VLS_ctx.subscriptions),
    itemTitle: "name",
    itemValue: "id",
    label: "订阅多选",
    multiple: true,
}));
const __VLS_153 = __VLS_152({
    modelValue: (__VLS_ctx.form.subscriptionIds),
    items: (__VLS_ctx.subscriptions),
    itemTitle: "name",
    itemValue: "id",
    label: "订阅多选",
    multiple: true,
}, ...__VLS_functionalComponentArgsRest(__VLS_152));
// @ts-ignore
[form, subscriptions,];
var __VLS_148;
let __VLS_156;
/** @ts-ignore @type {typeof __VLS_components.vCol | typeof __VLS_components.VCol | typeof __VLS_components.vCol | typeof __VLS_components.VCol} */
vCol;
// @ts-ignore
const __VLS_157 = __VLS_asFunctionalComponent1(__VLS_156, new __VLS_156({
    cols: "12",
    md: "4",
}));
const __VLS_158 = __VLS_157({
    cols: "12",
    md: "4",
}, ...__VLS_functionalComponentArgsRest(__VLS_157));
const { default: __VLS_161 } = __VLS_159.slots;
let __VLS_162;
/** @ts-ignore @type {typeof __VLS_components.vSwitch | typeof __VLS_components.VSwitch} */
vSwitch;
// @ts-ignore
const __VLS_163 = __VLS_asFunctionalComponent1(__VLS_162, new __VLS_162({
    modelValue: (__VLS_ctx.form.enabled),
    label: "启用此配置",
    hideDetails: true,
}));
const __VLS_164 = __VLS_163({
    modelValue: (__VLS_ctx.form.enabled),
    label: "启用此配置",
    hideDetails: true,
}, ...__VLS_functionalComponentArgsRest(__VLS_163));
// @ts-ignore
[form,];
var __VLS_159;
// @ts-ignore
[];
var __VLS_120;
// @ts-ignore
[];
var __VLS_114;
let __VLS_167;
/** @ts-ignore @type {typeof __VLS_components.vCardActions | typeof __VLS_components.VCardActions | typeof __VLS_components.vCardActions | typeof __VLS_components.VCardActions} */
vCardActions;
// @ts-ignore
const __VLS_168 = __VLS_asFunctionalComponent1(__VLS_167, new __VLS_167({}));
const __VLS_169 = __VLS_168({}, ...__VLS_functionalComponentArgsRest(__VLS_168));
const { default: __VLS_172 } = __VLS_170.slots;
let __VLS_173;
/** @ts-ignore @type {typeof __VLS_components.vSpacer | typeof __VLS_components.VSpacer} */
vSpacer;
// @ts-ignore
const __VLS_174 = __VLS_asFunctionalComponent1(__VLS_173, new __VLS_173({}));
const __VLS_175 = __VLS_174({}, ...__VLS_functionalComponentArgsRest(__VLS_174));
let __VLS_178;
/** @ts-ignore @type {typeof __VLS_components.vBtn | typeof __VLS_components.VBtn | typeof __VLS_components.vBtn | typeof __VLS_components.VBtn} */
vBtn;
// @ts-ignore
const __VLS_179 = __VLS_asFunctionalComponent1(__VLS_178, new __VLS_178({
    ...{ 'onClick': {} },
    variant: "text",
}));
const __VLS_180 = __VLS_179({
    ...{ 'onClick': {} },
    variant: "text",
}, ...__VLS_functionalComponentArgsRest(__VLS_179));
let __VLS_183;
const __VLS_184 = ({ click: {} },
    { onClick: (...[$event]) => {
            __VLS_ctx.dialog = false;
            // @ts-ignore
            [dialog,];
        } });
const { default: __VLS_185 } = __VLS_181.slots;
// @ts-ignore
[];
var __VLS_181;
var __VLS_182;
let __VLS_186;
/** @ts-ignore @type {typeof __VLS_components.vBtn | typeof __VLS_components.VBtn | typeof __VLS_components.vBtn | typeof __VLS_components.VBtn} */
vBtn;
// @ts-ignore
const __VLS_187 = __VLS_asFunctionalComponent1(__VLS_186, new __VLS_186({
    ...{ 'onClick': {} },
    color: "primary",
    disabled: (__VLS_ctx.busy || !__VLS_ctx.canSubmit),
}));
const __VLS_188 = __VLS_187({
    ...{ 'onClick': {} },
    color: "primary",
    disabled: (__VLS_ctx.busy || !__VLS_ctx.canSubmit),
}, ...__VLS_functionalComponentArgsRest(__VLS_187));
let __VLS_191;
const __VLS_192 = ({ click: {} },
    { onClick: (__VLS_ctx.saveProfile) });
const { default: __VLS_193 } = __VLS_189.slots;
// @ts-ignore
[busy, canSubmit, saveProfile,];
var __VLS_189;
var __VLS_190;
// @ts-ignore
[];
var __VLS_170;
// @ts-ignore
[];
var __VLS_90;
// @ts-ignore
[];
var __VLS_84;
// @ts-ignore
[];
const __VLS_export = (await import('vue')).defineComponent({
    __typeEmits: {},
});
export default {};
