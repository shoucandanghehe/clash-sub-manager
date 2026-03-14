import { storeToRefs } from 'pinia';
import { computed, reactive, ref, watch } from 'vue';
import { useManagerStore } from '../stores/manager';
const DEFAULT_TEMPLATE = 'proxies: []\nproxy-groups: []\nrules: []\n';
const store = useManagerStore();
const { busy, templates } = storeToRefs(store);
const dialog = ref(false);
const editingId = ref(null);
const selectedTemplateId = ref(null);
const form = reactive({
    name: '',
    content: DEFAULT_TEMPLATE,
    isDefault: false,
});
const headers = [
    { title: '名称', key: 'name' },
    { title: '默认', key: 'is_default' },
    { title: '预览', key: 'preview' },
    { title: '操作', key: 'actions', sortable: false, align: 'end' },
];
const dialogTitle = computed(() => {
    return editingId.value === null ? '新建模板' : '编辑模板';
});
const canSubmit = computed(() => {
    return form.name.trim().length > 0 && form.content.trim().length > 0;
});
const selectedTemplate = computed(() => {
    return templates.value.find((template) => template.id === selectedTemplateId.value) ?? null;
});
watch(templates, (items) => {
    if (items.length === 0) {
        selectedTemplateId.value = null;
        return;
    }
    const stillExists = items.some((template) => template.id === selectedTemplateId.value);
    if (!stillExists) {
        selectedTemplateId.value = items.find((template) => template.is_default)?.id ?? items[0].id;
    }
}, { immediate: true });
function resetForm() {
    editingId.value = null;
    form.name = '';
    form.content = DEFAULT_TEMPLATE;
    form.isDefault = false;
}
function openCreateDialog() {
    resetForm();
    dialog.value = true;
}
function openEditDialog(template) {
    editingId.value = template.id;
    selectedTemplateId.value = template.id;
    form.name = template.name;
    form.content = template.content;
    form.isDefault = template.is_default;
    dialog.value = true;
}
async function saveTemplate() {
    const payload = {
        name: form.name.trim(),
        content: form.content,
        is_default: form.isDefault,
    };
    const succeeded = editingId.value === null
        ? await store.createTemplate(payload)
        : await store.updateTemplate(editingId.value, payload);
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
/** @ts-ignore @type {typeof __VLS_components.vRow | typeof __VLS_components.VRow | typeof __VLS_components.vRow | typeof __VLS_components.VRow} */
vRow;
// @ts-ignore
const __VLS_1 = __VLS_asFunctionalComponent1(__VLS_0, new __VLS_0({}));
const __VLS_2 = __VLS_1({}, ...__VLS_functionalComponentArgsRest(__VLS_1));
const { default: __VLS_5 } = __VLS_3.slots;
let __VLS_6;
/** @ts-ignore @type {typeof __VLS_components.vCol | typeof __VLS_components.VCol | typeof __VLS_components.vCol | typeof __VLS_components.VCol} */
vCol;
// @ts-ignore
const __VLS_7 = __VLS_asFunctionalComponent1(__VLS_6, new __VLS_6({
    cols: "12",
    lg: "7",
}));
const __VLS_8 = __VLS_7({
    cols: "12",
    lg: "7",
}, ...__VLS_functionalComponentArgsRest(__VLS_7));
const { default: __VLS_11 } = __VLS_9.slots;
let __VLS_12;
/** @ts-ignore @type {typeof __VLS_components.vCard | typeof __VLS_components.VCard | typeof __VLS_components.vCard | typeof __VLS_components.VCard} */
vCard;
// @ts-ignore
const __VLS_13 = __VLS_asFunctionalComponent1(__VLS_12, new __VLS_12({}));
const __VLS_14 = __VLS_13({}, ...__VLS_functionalComponentArgsRest(__VLS_13));
const { default: __VLS_17 } = __VLS_15.slots;
let __VLS_18;
/** @ts-ignore @type {typeof __VLS_components.vCardItem | typeof __VLS_components.VCardItem | typeof __VLS_components.vCardItem | typeof __VLS_components.VCardItem} */
vCardItem;
// @ts-ignore
const __VLS_19 = __VLS_asFunctionalComponent1(__VLS_18, new __VLS_18({}));
const __VLS_20 = __VLS_19({}, ...__VLS_functionalComponentArgsRest(__VLS_19));
const { default: __VLS_23 } = __VLS_21.slots;
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
let __VLS_24;
/** @ts-ignore @type {typeof __VLS_components.vCardTitle | typeof __VLS_components.VCardTitle | typeof __VLS_components.vCardTitle | typeof __VLS_components.VCardTitle} */
vCardTitle;
// @ts-ignore
const __VLS_25 = __VLS_asFunctionalComponent1(__VLS_24, new __VLS_24({
    ...{ class: "px-0" },
}));
const __VLS_26 = __VLS_25({
    ...{ class: "px-0" },
}, ...__VLS_functionalComponentArgsRest(__VLS_25));
/** @type {__VLS_StyleScopedClasses['px-0']} */ ;
const { default: __VLS_29 } = __VLS_27.slots;
var __VLS_27;
let __VLS_30;
/** @ts-ignore @type {typeof __VLS_components.vCardSubtitle | typeof __VLS_components.VCardSubtitle | typeof __VLS_components.vCardSubtitle | typeof __VLS_components.VCardSubtitle} */
vCardSubtitle;
// @ts-ignore
const __VLS_31 = __VLS_asFunctionalComponent1(__VLS_30, new __VLS_30({
    ...{ class: "px-0" },
}));
const __VLS_32 = __VLS_31({
    ...{ class: "px-0" },
}, ...__VLS_functionalComponentArgsRest(__VLS_31));
/** @type {__VLS_StyleScopedClasses['px-0']} */ ;
const { default: __VLS_35 } = __VLS_33.slots;
var __VLS_33;
let __VLS_36;
/** @ts-ignore @type {typeof __VLS_components.vBtn | typeof __VLS_components.VBtn | typeof __VLS_components.vBtn | typeof __VLS_components.VBtn} */
vBtn;
// @ts-ignore
const __VLS_37 = __VLS_asFunctionalComponent1(__VLS_36, new __VLS_36({
    ...{ 'onClick': {} },
    color: "primary",
    prependIcon: "mdi-plus",
}));
const __VLS_38 = __VLS_37({
    ...{ 'onClick': {} },
    color: "primary",
    prependIcon: "mdi-plus",
}, ...__VLS_functionalComponentArgsRest(__VLS_37));
let __VLS_41;
const __VLS_42 = ({ click: {} },
    { onClick: (__VLS_ctx.openCreateDialog) });
const { default: __VLS_43 } = __VLS_39.slots;
// @ts-ignore
[openCreateDialog,];
var __VLS_39;
var __VLS_40;
// @ts-ignore
[];
var __VLS_21;
let __VLS_44;
/** @ts-ignore @type {typeof __VLS_components.vDataTable | typeof __VLS_components.VDataTable | typeof __VLS_components.vDataTable | typeof __VLS_components.VDataTable} */
vDataTable;
// @ts-ignore
const __VLS_45 = __VLS_asFunctionalComponent1(__VLS_44, new __VLS_44({
    headers: (__VLS_ctx.headers),
    items: (__VLS_ctx.templates),
    itemValue: "id",
}));
const __VLS_46 = __VLS_45({
    headers: (__VLS_ctx.headers),
    items: (__VLS_ctx.templates),
    itemValue: "id",
}, ...__VLS_functionalComponentArgsRest(__VLS_45));
const { default: __VLS_49 } = __VLS_47.slots;
{
    const { 'item.is_default': __VLS_50 } = __VLS_47.slots;
    const [{ item }] = __VLS_vSlot(__VLS_50);
    let __VLS_51;
    /** @ts-ignore @type {typeof __VLS_components.vChip | typeof __VLS_components.VChip | typeof __VLS_components.vChip | typeof __VLS_components.VChip} */
    vChip;
    // @ts-ignore
    const __VLS_52 = __VLS_asFunctionalComponent1(__VLS_51, new __VLS_51({
        color: (item.is_default ? 'primary' : 'default'),
        size: "small",
        variant: "tonal",
    }));
    const __VLS_53 = __VLS_52({
        color: (item.is_default ? 'primary' : 'default'),
        size: "small",
        variant: "tonal",
    }, ...__VLS_functionalComponentArgsRest(__VLS_52));
    const { default: __VLS_56 } = __VLS_54.slots;
    (item.is_default ? '默认模板' : '普通模板');
    // @ts-ignore
    [headers, templates,];
    var __VLS_54;
    // @ts-ignore
    [];
}
{
    const { 'item.preview': __VLS_57 } = __VLS_47.slots;
    const [{ item }] = __VLS_vSlot(__VLS_57);
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "text-caption text-medium-emphasis preview-ellipsis py-2" },
    });
    /** @type {__VLS_StyleScopedClasses['text-caption']} */ ;
    /** @type {__VLS_StyleScopedClasses['text-medium-emphasis']} */ ;
    /** @type {__VLS_StyleScopedClasses['preview-ellipsis']} */ ;
    /** @type {__VLS_StyleScopedClasses['py-2']} */ ;
    (item.content);
    // @ts-ignore
    [];
}
{
    const { 'item.actions': __VLS_58 } = __VLS_47.slots;
    const [{ item }] = __VLS_vSlot(__VLS_58);
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "d-flex justify-end ga-2 py-2" },
    });
    /** @type {__VLS_StyleScopedClasses['d-flex']} */ ;
    /** @type {__VLS_StyleScopedClasses['justify-end']} */ ;
    /** @type {__VLS_StyleScopedClasses['ga-2']} */ ;
    /** @type {__VLS_StyleScopedClasses['py-2']} */ ;
    let __VLS_59;
    /** @ts-ignore @type {typeof __VLS_components.vBtn | typeof __VLS_components.VBtn} */
    vBtn;
    // @ts-ignore
    const __VLS_60 = __VLS_asFunctionalComponent1(__VLS_59, new __VLS_59({
        ...{ 'onClick': {} },
        icon: "mdi-eye-outline",
        size: "small",
        variant: "text",
    }));
    const __VLS_61 = __VLS_60({
        ...{ 'onClick': {} },
        icon: "mdi-eye-outline",
        size: "small",
        variant: "text",
    }, ...__VLS_functionalComponentArgsRest(__VLS_60));
    let __VLS_64;
    const __VLS_65 = ({ click: {} },
        { onClick: (...[$event]) => {
                __VLS_ctx.selectedTemplateId = item.id;
                // @ts-ignore
                [selectedTemplateId,];
            } });
    var __VLS_62;
    var __VLS_63;
    let __VLS_66;
    /** @ts-ignore @type {typeof __VLS_components.vBtn | typeof __VLS_components.VBtn} */
    vBtn;
    // @ts-ignore
    const __VLS_67 = __VLS_asFunctionalComponent1(__VLS_66, new __VLS_66({
        ...{ 'onClick': {} },
        icon: "mdi-pencil",
        size: "small",
        variant: "text",
    }));
    const __VLS_68 = __VLS_67({
        ...{ 'onClick': {} },
        icon: "mdi-pencil",
        size: "small",
        variant: "text",
    }, ...__VLS_functionalComponentArgsRest(__VLS_67));
    let __VLS_71;
    const __VLS_72 = ({ click: {} },
        { onClick: (...[$event]) => {
                __VLS_ctx.openEditDialog(item);
                // @ts-ignore
                [openEditDialog,];
            } });
    var __VLS_69;
    var __VLS_70;
    let __VLS_73;
    /** @ts-ignore @type {typeof __VLS_components.vBtn | typeof __VLS_components.VBtn} */
    vBtn;
    // @ts-ignore
    const __VLS_74 = __VLS_asFunctionalComponent1(__VLS_73, new __VLS_73({
        ...{ 'onClick': {} },
        icon: "mdi-delete-outline",
        size: "small",
        variant: "text",
        color: "error",
    }));
    const __VLS_75 = __VLS_74({
        ...{ 'onClick': {} },
        icon: "mdi-delete-outline",
        size: "small",
        variant: "text",
        color: "error",
    }, ...__VLS_functionalComponentArgsRest(__VLS_74));
    let __VLS_78;
    const __VLS_79 = ({ click: {} },
        { onClick: (...[$event]) => {
                __VLS_ctx.store.deleteTemplate(item.id);
                // @ts-ignore
                [store,];
            } });
    var __VLS_76;
    var __VLS_77;
    // @ts-ignore
    [];
}
// @ts-ignore
[];
var __VLS_47;
// @ts-ignore
[];
var __VLS_15;
// @ts-ignore
[];
var __VLS_9;
let __VLS_80;
/** @ts-ignore @type {typeof __VLS_components.vCol | typeof __VLS_components.VCol | typeof __VLS_components.vCol | typeof __VLS_components.VCol} */
vCol;
// @ts-ignore
const __VLS_81 = __VLS_asFunctionalComponent1(__VLS_80, new __VLS_80({
    cols: "12",
    lg: "5",
}));
const __VLS_82 = __VLS_81({
    cols: "12",
    lg: "5",
}, ...__VLS_functionalComponentArgsRest(__VLS_81));
const { default: __VLS_85 } = __VLS_83.slots;
let __VLS_86;
/** @ts-ignore @type {typeof __VLS_components.vCard | typeof __VLS_components.VCard | typeof __VLS_components.vCard | typeof __VLS_components.VCard} */
vCard;
// @ts-ignore
const __VLS_87 = __VLS_asFunctionalComponent1(__VLS_86, new __VLS_86({
    ...{ class: "fill-height" },
}));
const __VLS_88 = __VLS_87({
    ...{ class: "fill-height" },
}, ...__VLS_functionalComponentArgsRest(__VLS_87));
/** @type {__VLS_StyleScopedClasses['fill-height']} */ ;
const { default: __VLS_91 } = __VLS_89.slots;
let __VLS_92;
/** @ts-ignore @type {typeof __VLS_components.vCardItem | typeof __VLS_components.VCardItem | typeof __VLS_components.vCardItem | typeof __VLS_components.VCardItem} */
vCardItem;
// @ts-ignore
const __VLS_93 = __VLS_asFunctionalComponent1(__VLS_92, new __VLS_92({}));
const __VLS_94 = __VLS_93({}, ...__VLS_functionalComponentArgsRest(__VLS_93));
const { default: __VLS_97 } = __VLS_95.slots;
let __VLS_98;
/** @ts-ignore @type {typeof __VLS_components.vCardTitle | typeof __VLS_components.VCardTitle | typeof __VLS_components.vCardTitle | typeof __VLS_components.VCardTitle} */
vCardTitle;
// @ts-ignore
const __VLS_99 = __VLS_asFunctionalComponent1(__VLS_98, new __VLS_98({
    ...{ class: "px-0" },
}));
const __VLS_100 = __VLS_99({
    ...{ class: "px-0" },
}, ...__VLS_functionalComponentArgsRest(__VLS_99));
/** @type {__VLS_StyleScopedClasses['px-0']} */ ;
const { default: __VLS_103 } = __VLS_101.slots;
// @ts-ignore
[];
var __VLS_101;
let __VLS_104;
/** @ts-ignore @type {typeof __VLS_components.vCardSubtitle | typeof __VLS_components.VCardSubtitle | typeof __VLS_components.vCardSubtitle | typeof __VLS_components.VCardSubtitle} */
vCardSubtitle;
// @ts-ignore
const __VLS_105 = __VLS_asFunctionalComponent1(__VLS_104, new __VLS_104({
    ...{ class: "px-0" },
}));
const __VLS_106 = __VLS_105({
    ...{ class: "px-0" },
}, ...__VLS_functionalComponentArgsRest(__VLS_105));
/** @type {__VLS_StyleScopedClasses['px-0']} */ ;
const { default: __VLS_109 } = __VLS_107.slots;
(__VLS_ctx.selectedTemplate?.name ?? '尚未选择模板');
// @ts-ignore
[selectedTemplate,];
var __VLS_107;
// @ts-ignore
[];
var __VLS_95;
let __VLS_110;
/** @ts-ignore @type {typeof __VLS_components.vCardText | typeof __VLS_components.VCardText | typeof __VLS_components.vCardText | typeof __VLS_components.VCardText} */
vCardText;
// @ts-ignore
const __VLS_111 = __VLS_asFunctionalComponent1(__VLS_110, new __VLS_110({}));
const __VLS_112 = __VLS_111({}, ...__VLS_functionalComponentArgsRest(__VLS_111));
const { default: __VLS_115 } = __VLS_113.slots;
let __VLS_116;
/** @ts-ignore @type {typeof __VLS_components.vSheet | typeof __VLS_components.VSheet | typeof __VLS_components.vSheet | typeof __VLS_components.VSheet} */
vSheet;
// @ts-ignore
const __VLS_117 = __VLS_asFunctionalComponent1(__VLS_116, new __VLS_116({
    ...{ class: "preview-panel" },
    color: "surface-variant",
    rounded: "xl",
}));
const __VLS_118 = __VLS_117({
    ...{ class: "preview-panel" },
    color: "surface-variant",
    rounded: "xl",
}, ...__VLS_functionalComponentArgsRest(__VLS_117));
/** @type {__VLS_StyleScopedClasses['preview-panel']} */ ;
const { default: __VLS_121 } = __VLS_119.slots;
__VLS_asFunctionalElement1(__VLS_intrinsics.pre, __VLS_intrinsics.pre)({});
(__VLS_ctx.selectedTemplate?.content ?? '从左侧列表选择一个模板，即可在这里查看完整 YAML。');
// @ts-ignore
[selectedTemplate,];
var __VLS_119;
// @ts-ignore
[];
var __VLS_113;
// @ts-ignore
[];
var __VLS_89;
// @ts-ignore
[];
var __VLS_83;
// @ts-ignore
[];
var __VLS_3;
let __VLS_122;
/** @ts-ignore @type {typeof __VLS_components.vDialog | typeof __VLS_components.VDialog | typeof __VLS_components.vDialog | typeof __VLS_components.VDialog} */
vDialog;
// @ts-ignore
const __VLS_123 = __VLS_asFunctionalComponent1(__VLS_122, new __VLS_122({
    modelValue: (__VLS_ctx.dialog),
}));
const __VLS_124 = __VLS_123({
    modelValue: (__VLS_ctx.dialog),
}, ...__VLS_functionalComponentArgsRest(__VLS_123));
const { default: __VLS_127 } = __VLS_125.slots;
let __VLS_128;
/** @ts-ignore @type {typeof __VLS_components.vCard | typeof __VLS_components.VCard | typeof __VLS_components.vCard | typeof __VLS_components.VCard} */
vCard;
// @ts-ignore
const __VLS_129 = __VLS_asFunctionalComponent1(__VLS_128, new __VLS_128({}));
const __VLS_130 = __VLS_129({}, ...__VLS_functionalComponentArgsRest(__VLS_129));
const { default: __VLS_133 } = __VLS_131.slots;
let __VLS_134;
/** @ts-ignore @type {typeof __VLS_components.vCardItem | typeof __VLS_components.VCardItem | typeof __VLS_components.vCardItem | typeof __VLS_components.VCardItem} */
vCardItem;
// @ts-ignore
const __VLS_135 = __VLS_asFunctionalComponent1(__VLS_134, new __VLS_134({}));
const __VLS_136 = __VLS_135({}, ...__VLS_functionalComponentArgsRest(__VLS_135));
const { default: __VLS_139 } = __VLS_137.slots;
let __VLS_140;
/** @ts-ignore @type {typeof __VLS_components.vCardTitle | typeof __VLS_components.VCardTitle | typeof __VLS_components.vCardTitle | typeof __VLS_components.VCardTitle} */
vCardTitle;
// @ts-ignore
const __VLS_141 = __VLS_asFunctionalComponent1(__VLS_140, new __VLS_140({}));
const __VLS_142 = __VLS_141({}, ...__VLS_functionalComponentArgsRest(__VLS_141));
const { default: __VLS_145 } = __VLS_143.slots;
(__VLS_ctx.dialogTitle);
// @ts-ignore
[dialog, dialogTitle,];
var __VLS_143;
let __VLS_146;
/** @ts-ignore @type {typeof __VLS_components.vCardSubtitle | typeof __VLS_components.VCardSubtitle | typeof __VLS_components.vCardSubtitle | typeof __VLS_components.VCardSubtitle} */
vCardSubtitle;
// @ts-ignore
const __VLS_147 = __VLS_asFunctionalComponent1(__VLS_146, new __VLS_146({}));
const __VLS_148 = __VLS_147({}, ...__VLS_functionalComponentArgsRest(__VLS_147));
const { default: __VLS_151 } = __VLS_149.slots;
// @ts-ignore
[];
var __VLS_149;
// @ts-ignore
[];
var __VLS_137;
let __VLS_152;
/** @ts-ignore @type {typeof __VLS_components.vCardText | typeof __VLS_components.VCardText | typeof __VLS_components.vCardText | typeof __VLS_components.VCardText} */
vCardText;
// @ts-ignore
const __VLS_153 = __VLS_asFunctionalComponent1(__VLS_152, new __VLS_152({}));
const __VLS_154 = __VLS_153({}, ...__VLS_functionalComponentArgsRest(__VLS_153));
const { default: __VLS_157 } = __VLS_155.slots;
let __VLS_158;
/** @ts-ignore @type {typeof __VLS_components.vRow | typeof __VLS_components.VRow | typeof __VLS_components.vRow | typeof __VLS_components.VRow} */
vRow;
// @ts-ignore
const __VLS_159 = __VLS_asFunctionalComponent1(__VLS_158, new __VLS_158({}));
const __VLS_160 = __VLS_159({}, ...__VLS_functionalComponentArgsRest(__VLS_159));
const { default: __VLS_163 } = __VLS_161.slots;
let __VLS_164;
/** @ts-ignore @type {typeof __VLS_components.vCol | typeof __VLS_components.VCol | typeof __VLS_components.vCol | typeof __VLS_components.VCol} */
vCol;
// @ts-ignore
const __VLS_165 = __VLS_asFunctionalComponent1(__VLS_164, new __VLS_164({
    cols: "12",
    md: "8",
}));
const __VLS_166 = __VLS_165({
    cols: "12",
    md: "8",
}, ...__VLS_functionalComponentArgsRest(__VLS_165));
const { default: __VLS_169 } = __VLS_167.slots;
let __VLS_170;
/** @ts-ignore @type {typeof __VLS_components.vTextField | typeof __VLS_components.VTextField} */
vTextField;
// @ts-ignore
const __VLS_171 = __VLS_asFunctionalComponent1(__VLS_170, new __VLS_170({
    modelValue: (__VLS_ctx.form.name),
    label: "模板名称",
    maxlength: "255",
}));
const __VLS_172 = __VLS_171({
    modelValue: (__VLS_ctx.form.name),
    label: "模板名称",
    maxlength: "255",
}, ...__VLS_functionalComponentArgsRest(__VLS_171));
// @ts-ignore
[form,];
var __VLS_167;
let __VLS_175;
/** @ts-ignore @type {typeof __VLS_components.vCol | typeof __VLS_components.VCol | typeof __VLS_components.vCol | typeof __VLS_components.VCol} */
vCol;
// @ts-ignore
const __VLS_176 = __VLS_asFunctionalComponent1(__VLS_175, new __VLS_175({
    cols: "12",
    md: "4",
}));
const __VLS_177 = __VLS_176({
    cols: "12",
    md: "4",
}, ...__VLS_functionalComponentArgsRest(__VLS_176));
const { default: __VLS_180 } = __VLS_178.slots;
let __VLS_181;
/** @ts-ignore @type {typeof __VLS_components.vSwitch | typeof __VLS_components.VSwitch} */
vSwitch;
// @ts-ignore
const __VLS_182 = __VLS_asFunctionalComponent1(__VLS_181, new __VLS_181({
    modelValue: (__VLS_ctx.form.isDefault),
    label: "设为默认",
    hideDetails: true,
}));
const __VLS_183 = __VLS_182({
    modelValue: (__VLS_ctx.form.isDefault),
    label: "设为默认",
    hideDetails: true,
}, ...__VLS_functionalComponentArgsRest(__VLS_182));
// @ts-ignore
[form,];
var __VLS_178;
let __VLS_186;
/** @ts-ignore @type {typeof __VLS_components.vCol | typeof __VLS_components.VCol | typeof __VLS_components.vCol | typeof __VLS_components.VCol} */
vCol;
// @ts-ignore
const __VLS_187 = __VLS_asFunctionalComponent1(__VLS_186, new __VLS_186({
    cols: "12",
}));
const __VLS_188 = __VLS_187({
    cols: "12",
}, ...__VLS_functionalComponentArgsRest(__VLS_187));
const { default: __VLS_191 } = __VLS_189.slots;
let __VLS_192;
/** @ts-ignore @type {typeof __VLS_components.vTextarea | typeof __VLS_components.VTextarea} */
vTextarea;
// @ts-ignore
const __VLS_193 = __VLS_asFunctionalComponent1(__VLS_192, new __VLS_192({
    modelValue: (__VLS_ctx.form.content),
    label: "YAML 内容",
    rows: "18",
}));
const __VLS_194 = __VLS_193({
    modelValue: (__VLS_ctx.form.content),
    label: "YAML 内容",
    rows: "18",
}, ...__VLS_functionalComponentArgsRest(__VLS_193));
// @ts-ignore
[form,];
var __VLS_189;
// @ts-ignore
[];
var __VLS_161;
// @ts-ignore
[];
var __VLS_155;
let __VLS_197;
/** @ts-ignore @type {typeof __VLS_components.vCardActions | typeof __VLS_components.VCardActions | typeof __VLS_components.vCardActions | typeof __VLS_components.VCardActions} */
vCardActions;
// @ts-ignore
const __VLS_198 = __VLS_asFunctionalComponent1(__VLS_197, new __VLS_197({}));
const __VLS_199 = __VLS_198({}, ...__VLS_functionalComponentArgsRest(__VLS_198));
const { default: __VLS_202 } = __VLS_200.slots;
let __VLS_203;
/** @ts-ignore @type {typeof __VLS_components.vSpacer | typeof __VLS_components.VSpacer} */
vSpacer;
// @ts-ignore
const __VLS_204 = __VLS_asFunctionalComponent1(__VLS_203, new __VLS_203({}));
const __VLS_205 = __VLS_204({}, ...__VLS_functionalComponentArgsRest(__VLS_204));
let __VLS_208;
/** @ts-ignore @type {typeof __VLS_components.vBtn | typeof __VLS_components.VBtn | typeof __VLS_components.vBtn | typeof __VLS_components.VBtn} */
vBtn;
// @ts-ignore
const __VLS_209 = __VLS_asFunctionalComponent1(__VLS_208, new __VLS_208({
    ...{ 'onClick': {} },
    variant: "text",
}));
const __VLS_210 = __VLS_209({
    ...{ 'onClick': {} },
    variant: "text",
}, ...__VLS_functionalComponentArgsRest(__VLS_209));
let __VLS_213;
const __VLS_214 = ({ click: {} },
    { onClick: (...[$event]) => {
            __VLS_ctx.dialog = false;
            // @ts-ignore
            [dialog,];
        } });
const { default: __VLS_215 } = __VLS_211.slots;
// @ts-ignore
[];
var __VLS_211;
var __VLS_212;
let __VLS_216;
/** @ts-ignore @type {typeof __VLS_components.vBtn | typeof __VLS_components.VBtn | typeof __VLS_components.vBtn | typeof __VLS_components.VBtn} */
vBtn;
// @ts-ignore
const __VLS_217 = __VLS_asFunctionalComponent1(__VLS_216, new __VLS_216({
    ...{ 'onClick': {} },
    color: "primary",
    disabled: (__VLS_ctx.busy || !__VLS_ctx.canSubmit),
}));
const __VLS_218 = __VLS_217({
    ...{ 'onClick': {} },
    color: "primary",
    disabled: (__VLS_ctx.busy || !__VLS_ctx.canSubmit),
}, ...__VLS_functionalComponentArgsRest(__VLS_217));
let __VLS_221;
const __VLS_222 = ({ click: {} },
    { onClick: (__VLS_ctx.saveTemplate) });
const { default: __VLS_223 } = __VLS_219.slots;
// @ts-ignore
[busy, canSubmit, saveTemplate,];
var __VLS_219;
var __VLS_220;
// @ts-ignore
[];
var __VLS_200;
// @ts-ignore
[];
var __VLS_131;
// @ts-ignore
[];
var __VLS_125;
// @ts-ignore
[];
const __VLS_export = (await import('vue')).defineComponent({});
export default {};
