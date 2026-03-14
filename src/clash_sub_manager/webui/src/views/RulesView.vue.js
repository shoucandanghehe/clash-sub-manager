import { storeToRefs } from 'pinia';
import { computed, reactive, ref } from 'vue';
import { useManagerStore } from '../stores/manager';
const store = useManagerStore();
const { busy, ruleSources, rules } = storeToRefs(store);
const dialog = ref(false);
const editingId = ref(null);
const form = reactive({
    name: '',
    url: '',
    autoUpdate: true,
});
const headers = [
    { title: '名称', key: 'name' },
    { title: '链接', key: 'url' },
    { title: '更新策略', key: 'auto_update' },
    { title: '缓存状态', key: 'cache' },
    { title: '操作', key: 'actions', sortable: false, align: 'end' },
];
const dialogTitle = computed(() => {
    return editingId.value === null ? '新建规则源' : '编辑规则源';
});
const canSubmit = computed(() => {
    return form.name.trim().length > 0 && form.url.trim().length > 0;
});
const rulesText = computed(() => {
    return rules.value.join('\n') || '当前还没有缓存规则。';
});
function resetForm() {
    editingId.value = null;
    form.name = '';
    form.url = '';
    form.autoUpdate = true;
}
function openCreateDialog() {
    resetForm();
    dialog.value = true;
}
function openEditDialog(ruleSource) {
    editingId.value = ruleSource.id;
    form.name = ruleSource.name;
    form.url = ruleSource.url;
    form.autoUpdate = ruleSource.auto_update;
    dialog.value = true;
}
async function saveRuleSource() {
    const payload = {
        name: form.name.trim(),
        url: form.url.trim(),
        auto_update: form.autoUpdate,
    };
    const succeeded = editingId.value === null
        ? await store.createRuleSource(payload)
        : await store.updateRuleSource(editingId.value, payload);
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
    lg: "8",
}));
const __VLS_8 = __VLS_7({
    cols: "12",
    lg: "8",
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
    items: (__VLS_ctx.ruleSources),
    itemValue: "id",
}));
const __VLS_46 = __VLS_45({
    headers: (__VLS_ctx.headers),
    items: (__VLS_ctx.ruleSources),
    itemValue: "id",
}, ...__VLS_functionalComponentArgsRest(__VLS_45));
const { default: __VLS_49 } = __VLS_47.slots;
{
    const { 'item.url': __VLS_50 } = __VLS_47.slots;
    const [{ item }] = __VLS_vSlot(__VLS_50);
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "py-2 text-break" },
    });
    /** @type {__VLS_StyleScopedClasses['py-2']} */ ;
    /** @type {__VLS_StyleScopedClasses['text-break']} */ ;
    (item.url);
    // @ts-ignore
    [headers, ruleSources,];
}
{
    const { 'item.auto_update': __VLS_51 } = __VLS_47.slots;
    const [{ item }] = __VLS_vSlot(__VLS_51);
    let __VLS_52;
    /** @ts-ignore @type {typeof __VLS_components.vChip | typeof __VLS_components.VChip | typeof __VLS_components.vChip | typeof __VLS_components.VChip} */
    vChip;
    // @ts-ignore
    const __VLS_53 = __VLS_asFunctionalComponent1(__VLS_52, new __VLS_52({
        color: (item.auto_update ? 'primary' : 'default'),
        size: "small",
        variant: "tonal",
    }));
    const __VLS_54 = __VLS_53({
        color: (item.auto_update ? 'primary' : 'default'),
        size: "small",
        variant: "tonal",
    }, ...__VLS_functionalComponentArgsRest(__VLS_53));
    const { default: __VLS_57 } = __VLS_55.slots;
    (item.auto_update ? '自动更新' : '仅手动');
    // @ts-ignore
    [];
    var __VLS_55;
    // @ts-ignore
    [];
}
{
    const { 'item.cache': __VLS_58 } = __VLS_47.slots;
    const [{ item }] = __VLS_vSlot(__VLS_58);
    let __VLS_59;
    /** @ts-ignore @type {typeof __VLS_components.vChip | typeof __VLS_components.VChip | typeof __VLS_components.vChip | typeof __VLS_components.VChip} */
    vChip;
    // @ts-ignore
    const __VLS_60 = __VLS_asFunctionalComponent1(__VLS_59, new __VLS_59({
        color: (item.content ? 'secondary' : 'default'),
        size: "small",
        variant: "tonal",
    }));
    const __VLS_61 = __VLS_60({
        color: (item.content ? 'secondary' : 'default'),
        size: "small",
        variant: "tonal",
    }, ...__VLS_functionalComponentArgsRest(__VLS_60));
    const { default: __VLS_64 } = __VLS_62.slots;
    (item.content ? '已缓存' : '未缓存');
    // @ts-ignore
    [];
    var __VLS_62;
    // @ts-ignore
    [];
}
{
    const { 'item.actions': __VLS_65 } = __VLS_47.slots;
    const [{ item }] = __VLS_vSlot(__VLS_65);
    __VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
        ...{ class: "d-flex justify-end ga-2 py-2" },
    });
    /** @type {__VLS_StyleScopedClasses['d-flex']} */ ;
    /** @type {__VLS_StyleScopedClasses['justify-end']} */ ;
    /** @type {__VLS_StyleScopedClasses['ga-2']} */ ;
    /** @type {__VLS_StyleScopedClasses['py-2']} */ ;
    let __VLS_66;
    /** @ts-ignore @type {typeof __VLS_components.vBtn | typeof __VLS_components.VBtn} */
    vBtn;
    // @ts-ignore
    const __VLS_67 = __VLS_asFunctionalComponent1(__VLS_66, new __VLS_66({
        ...{ 'onClick': {} },
        icon: "mdi-refresh",
        size: "small",
        variant: "text",
    }));
    const __VLS_68 = __VLS_67({
        ...{ 'onClick': {} },
        icon: "mdi-refresh",
        size: "small",
        variant: "text",
    }, ...__VLS_functionalComponentArgsRest(__VLS_67));
    let __VLS_71;
    const __VLS_72 = ({ click: {} },
        { onClick: (...[$event]) => {
                __VLS_ctx.store.refreshRuleSource(item.id);
                // @ts-ignore
                [store,];
            } });
    var __VLS_69;
    var __VLS_70;
    let __VLS_73;
    /** @ts-ignore @type {typeof __VLS_components.vBtn | typeof __VLS_components.VBtn} */
    vBtn;
    // @ts-ignore
    const __VLS_74 = __VLS_asFunctionalComponent1(__VLS_73, new __VLS_73({
        ...{ 'onClick': {} },
        icon: "mdi-pencil",
        size: "small",
        variant: "text",
    }));
    const __VLS_75 = __VLS_74({
        ...{ 'onClick': {} },
        icon: "mdi-pencil",
        size: "small",
        variant: "text",
    }, ...__VLS_functionalComponentArgsRest(__VLS_74));
    let __VLS_78;
    const __VLS_79 = ({ click: {} },
        { onClick: (...[$event]) => {
                __VLS_ctx.openEditDialog(item);
                // @ts-ignore
                [openEditDialog,];
            } });
    var __VLS_76;
    var __VLS_77;
    let __VLS_80;
    /** @ts-ignore @type {typeof __VLS_components.vBtn | typeof __VLS_components.VBtn} */
    vBtn;
    // @ts-ignore
    const __VLS_81 = __VLS_asFunctionalComponent1(__VLS_80, new __VLS_80({
        ...{ 'onClick': {} },
        icon: "mdi-delete-outline",
        size: "small",
        variant: "text",
        color: "error",
    }));
    const __VLS_82 = __VLS_81({
        ...{ 'onClick': {} },
        icon: "mdi-delete-outline",
        size: "small",
        variant: "text",
        color: "error",
    }, ...__VLS_functionalComponentArgsRest(__VLS_81));
    let __VLS_85;
    const __VLS_86 = ({ click: {} },
        { onClick: (...[$event]) => {
                __VLS_ctx.store.deleteRuleSource(item.id);
                // @ts-ignore
                [store,];
            } });
    var __VLS_83;
    var __VLS_84;
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
let __VLS_87;
/** @ts-ignore @type {typeof __VLS_components.vCol | typeof __VLS_components.VCol | typeof __VLS_components.vCol | typeof __VLS_components.VCol} */
vCol;
// @ts-ignore
const __VLS_88 = __VLS_asFunctionalComponent1(__VLS_87, new __VLS_87({
    cols: "12",
    lg: "4",
}));
const __VLS_89 = __VLS_88({
    cols: "12",
    lg: "4",
}, ...__VLS_functionalComponentArgsRest(__VLS_88));
const { default: __VLS_92 } = __VLS_90.slots;
let __VLS_93;
/** @ts-ignore @type {typeof __VLS_components.vCard | typeof __VLS_components.VCard | typeof __VLS_components.vCard | typeof __VLS_components.VCard} */
vCard;
// @ts-ignore
const __VLS_94 = __VLS_asFunctionalComponent1(__VLS_93, new __VLS_93({
    ...{ class: "fill-height" },
}));
const __VLS_95 = __VLS_94({
    ...{ class: "fill-height" },
}, ...__VLS_functionalComponentArgsRest(__VLS_94));
/** @type {__VLS_StyleScopedClasses['fill-height']} */ ;
const { default: __VLS_98 } = __VLS_96.slots;
let __VLS_99;
/** @ts-ignore @type {typeof __VLS_components.vCardItem | typeof __VLS_components.VCardItem | typeof __VLS_components.vCardItem | typeof __VLS_components.VCardItem} */
vCardItem;
// @ts-ignore
const __VLS_100 = __VLS_asFunctionalComponent1(__VLS_99, new __VLS_99({}));
const __VLS_101 = __VLS_100({}, ...__VLS_functionalComponentArgsRest(__VLS_100));
const { default: __VLS_104 } = __VLS_102.slots;
let __VLS_105;
/** @ts-ignore @type {typeof __VLS_components.vCardTitle | typeof __VLS_components.VCardTitle | typeof __VLS_components.vCardTitle | typeof __VLS_components.VCardTitle} */
vCardTitle;
// @ts-ignore
const __VLS_106 = __VLS_asFunctionalComponent1(__VLS_105, new __VLS_105({
    ...{ class: "px-0" },
}));
const __VLS_107 = __VLS_106({
    ...{ class: "px-0" },
}, ...__VLS_functionalComponentArgsRest(__VLS_106));
/** @type {__VLS_StyleScopedClasses['px-0']} */ ;
const { default: __VLS_110 } = __VLS_108.slots;
// @ts-ignore
[];
var __VLS_108;
let __VLS_111;
/** @ts-ignore @type {typeof __VLS_components.vCardSubtitle | typeof __VLS_components.VCardSubtitle | typeof __VLS_components.vCardSubtitle | typeof __VLS_components.VCardSubtitle} */
vCardSubtitle;
// @ts-ignore
const __VLS_112 = __VLS_asFunctionalComponent1(__VLS_111, new __VLS_111({
    ...{ class: "px-0" },
}));
const __VLS_113 = __VLS_112({
    ...{ class: "px-0" },
}, ...__VLS_functionalComponentArgsRest(__VLS_112));
/** @type {__VLS_StyleScopedClasses['px-0']} */ ;
const { default: __VLS_116 } = __VLS_114.slots;
// @ts-ignore
[];
var __VLS_114;
// @ts-ignore
[];
var __VLS_102;
let __VLS_117;
/** @ts-ignore @type {typeof __VLS_components.vCardText | typeof __VLS_components.VCardText | typeof __VLS_components.vCardText | typeof __VLS_components.VCardText} */
vCardText;
// @ts-ignore
const __VLS_118 = __VLS_asFunctionalComponent1(__VLS_117, new __VLS_117({}));
const __VLS_119 = __VLS_118({}, ...__VLS_functionalComponentArgsRest(__VLS_118));
const { default: __VLS_122 } = __VLS_120.slots;
let __VLS_123;
/** @ts-ignore @type {typeof __VLS_components.vSheet | typeof __VLS_components.VSheet | typeof __VLS_components.vSheet | typeof __VLS_components.VSheet} */
vSheet;
// @ts-ignore
const __VLS_124 = __VLS_asFunctionalComponent1(__VLS_123, new __VLS_123({
    ...{ class: "preview-panel" },
    color: "surface-variant",
    rounded: "xl",
}));
const __VLS_125 = __VLS_124({
    ...{ class: "preview-panel" },
    color: "surface-variant",
    rounded: "xl",
}, ...__VLS_functionalComponentArgsRest(__VLS_124));
/** @type {__VLS_StyleScopedClasses['preview-panel']} */ ;
const { default: __VLS_128 } = __VLS_126.slots;
__VLS_asFunctionalElement1(__VLS_intrinsics.pre, __VLS_intrinsics.pre)({});
(__VLS_ctx.rulesText);
// @ts-ignore
[rulesText,];
var __VLS_126;
// @ts-ignore
[];
var __VLS_120;
// @ts-ignore
[];
var __VLS_96;
// @ts-ignore
[];
var __VLS_90;
// @ts-ignore
[];
var __VLS_3;
let __VLS_129;
/** @ts-ignore @type {typeof __VLS_components.vDialog | typeof __VLS_components.VDialog | typeof __VLS_components.vDialog | typeof __VLS_components.VDialog} */
vDialog;
// @ts-ignore
const __VLS_130 = __VLS_asFunctionalComponent1(__VLS_129, new __VLS_129({
    modelValue: (__VLS_ctx.dialog),
}));
const __VLS_131 = __VLS_130({
    modelValue: (__VLS_ctx.dialog),
}, ...__VLS_functionalComponentArgsRest(__VLS_130));
const { default: __VLS_134 } = __VLS_132.slots;
let __VLS_135;
/** @ts-ignore @type {typeof __VLS_components.vCard | typeof __VLS_components.VCard | typeof __VLS_components.vCard | typeof __VLS_components.VCard} */
vCard;
// @ts-ignore
const __VLS_136 = __VLS_asFunctionalComponent1(__VLS_135, new __VLS_135({}));
const __VLS_137 = __VLS_136({}, ...__VLS_functionalComponentArgsRest(__VLS_136));
const { default: __VLS_140 } = __VLS_138.slots;
let __VLS_141;
/** @ts-ignore @type {typeof __VLS_components.vCardItem | typeof __VLS_components.VCardItem | typeof __VLS_components.vCardItem | typeof __VLS_components.VCardItem} */
vCardItem;
// @ts-ignore
const __VLS_142 = __VLS_asFunctionalComponent1(__VLS_141, new __VLS_141({}));
const __VLS_143 = __VLS_142({}, ...__VLS_functionalComponentArgsRest(__VLS_142));
const { default: __VLS_146 } = __VLS_144.slots;
let __VLS_147;
/** @ts-ignore @type {typeof __VLS_components.vCardTitle | typeof __VLS_components.VCardTitle | typeof __VLS_components.vCardTitle | typeof __VLS_components.VCardTitle} */
vCardTitle;
// @ts-ignore
const __VLS_148 = __VLS_asFunctionalComponent1(__VLS_147, new __VLS_147({}));
const __VLS_149 = __VLS_148({}, ...__VLS_functionalComponentArgsRest(__VLS_148));
const { default: __VLS_152 } = __VLS_150.slots;
(__VLS_ctx.dialogTitle);
// @ts-ignore
[dialog, dialogTitle,];
var __VLS_150;
let __VLS_153;
/** @ts-ignore @type {typeof __VLS_components.vCardSubtitle | typeof __VLS_components.VCardSubtitle | typeof __VLS_components.vCardSubtitle | typeof __VLS_components.VCardSubtitle} */
vCardSubtitle;
// @ts-ignore
const __VLS_154 = __VLS_asFunctionalComponent1(__VLS_153, new __VLS_153({}));
const __VLS_155 = __VLS_154({}, ...__VLS_functionalComponentArgsRest(__VLS_154));
const { default: __VLS_158 } = __VLS_156.slots;
// @ts-ignore
[];
var __VLS_156;
// @ts-ignore
[];
var __VLS_144;
let __VLS_159;
/** @ts-ignore @type {typeof __VLS_components.vCardText | typeof __VLS_components.VCardText | typeof __VLS_components.vCardText | typeof __VLS_components.VCardText} */
vCardText;
// @ts-ignore
const __VLS_160 = __VLS_asFunctionalComponent1(__VLS_159, new __VLS_159({}));
const __VLS_161 = __VLS_160({}, ...__VLS_functionalComponentArgsRest(__VLS_160));
const { default: __VLS_164 } = __VLS_162.slots;
let __VLS_165;
/** @ts-ignore @type {typeof __VLS_components.vRow | typeof __VLS_components.VRow | typeof __VLS_components.vRow | typeof __VLS_components.VRow} */
vRow;
// @ts-ignore
const __VLS_166 = __VLS_asFunctionalComponent1(__VLS_165, new __VLS_165({}));
const __VLS_167 = __VLS_166({}, ...__VLS_functionalComponentArgsRest(__VLS_166));
const { default: __VLS_170 } = __VLS_168.slots;
let __VLS_171;
/** @ts-ignore @type {typeof __VLS_components.vCol | typeof __VLS_components.VCol | typeof __VLS_components.vCol | typeof __VLS_components.VCol} */
vCol;
// @ts-ignore
const __VLS_172 = __VLS_asFunctionalComponent1(__VLS_171, new __VLS_171({
    cols: "12",
    md: "6",
}));
const __VLS_173 = __VLS_172({
    cols: "12",
    md: "6",
}, ...__VLS_functionalComponentArgsRest(__VLS_172));
const { default: __VLS_176 } = __VLS_174.slots;
let __VLS_177;
/** @ts-ignore @type {typeof __VLS_components.vTextField | typeof __VLS_components.VTextField} */
vTextField;
// @ts-ignore
const __VLS_178 = __VLS_asFunctionalComponent1(__VLS_177, new __VLS_177({
    modelValue: (__VLS_ctx.form.name),
    label: "名称",
    maxlength: "255",
}));
const __VLS_179 = __VLS_178({
    modelValue: (__VLS_ctx.form.name),
    label: "名称",
    maxlength: "255",
}, ...__VLS_functionalComponentArgsRest(__VLS_178));
// @ts-ignore
[form,];
var __VLS_174;
let __VLS_182;
/** @ts-ignore @type {typeof __VLS_components.vCol | typeof __VLS_components.VCol | typeof __VLS_components.vCol | typeof __VLS_components.VCol} */
vCol;
// @ts-ignore
const __VLS_183 = __VLS_asFunctionalComponent1(__VLS_182, new __VLS_182({
    cols: "12",
    md: "6",
}));
const __VLS_184 = __VLS_183({
    cols: "12",
    md: "6",
}, ...__VLS_functionalComponentArgsRest(__VLS_183));
const { default: __VLS_187 } = __VLS_185.slots;
let __VLS_188;
/** @ts-ignore @type {typeof __VLS_components.vSwitch | typeof __VLS_components.VSwitch} */
vSwitch;
// @ts-ignore
const __VLS_189 = __VLS_asFunctionalComponent1(__VLS_188, new __VLS_188({
    modelValue: (__VLS_ctx.form.autoUpdate),
    label: "自动更新",
    hideDetails: true,
}));
const __VLS_190 = __VLS_189({
    modelValue: (__VLS_ctx.form.autoUpdate),
    label: "自动更新",
    hideDetails: true,
}, ...__VLS_functionalComponentArgsRest(__VLS_189));
// @ts-ignore
[form,];
var __VLS_185;
let __VLS_193;
/** @ts-ignore @type {typeof __VLS_components.vCol | typeof __VLS_components.VCol | typeof __VLS_components.vCol | typeof __VLS_components.VCol} */
vCol;
// @ts-ignore
const __VLS_194 = __VLS_asFunctionalComponent1(__VLS_193, new __VLS_193({
    cols: "12",
}));
const __VLS_195 = __VLS_194({
    cols: "12",
}, ...__VLS_functionalComponentArgsRest(__VLS_194));
const { default: __VLS_198 } = __VLS_196.slots;
let __VLS_199;
/** @ts-ignore @type {typeof __VLS_components.vTextField | typeof __VLS_components.VTextField} */
vTextField;
// @ts-ignore
const __VLS_200 = __VLS_asFunctionalComponent1(__VLS_199, new __VLS_199({
    modelValue: (__VLS_ctx.form.url),
    label: "规则链接",
    placeholder: "https://example.com/rules.txt",
}));
const __VLS_201 = __VLS_200({
    modelValue: (__VLS_ctx.form.url),
    label: "规则链接",
    placeholder: "https://example.com/rules.txt",
}, ...__VLS_functionalComponentArgsRest(__VLS_200));
// @ts-ignore
[form,];
var __VLS_196;
// @ts-ignore
[];
var __VLS_168;
// @ts-ignore
[];
var __VLS_162;
let __VLS_204;
/** @ts-ignore @type {typeof __VLS_components.vCardActions | typeof __VLS_components.VCardActions | typeof __VLS_components.vCardActions | typeof __VLS_components.VCardActions} */
vCardActions;
// @ts-ignore
const __VLS_205 = __VLS_asFunctionalComponent1(__VLS_204, new __VLS_204({}));
const __VLS_206 = __VLS_205({}, ...__VLS_functionalComponentArgsRest(__VLS_205));
const { default: __VLS_209 } = __VLS_207.slots;
let __VLS_210;
/** @ts-ignore @type {typeof __VLS_components.vSpacer | typeof __VLS_components.VSpacer} */
vSpacer;
// @ts-ignore
const __VLS_211 = __VLS_asFunctionalComponent1(__VLS_210, new __VLS_210({}));
const __VLS_212 = __VLS_211({}, ...__VLS_functionalComponentArgsRest(__VLS_211));
let __VLS_215;
/** @ts-ignore @type {typeof __VLS_components.vBtn | typeof __VLS_components.VBtn | typeof __VLS_components.vBtn | typeof __VLS_components.VBtn} */
vBtn;
// @ts-ignore
const __VLS_216 = __VLS_asFunctionalComponent1(__VLS_215, new __VLS_215({
    ...{ 'onClick': {} },
    variant: "text",
}));
const __VLS_217 = __VLS_216({
    ...{ 'onClick': {} },
    variant: "text",
}, ...__VLS_functionalComponentArgsRest(__VLS_216));
let __VLS_220;
const __VLS_221 = ({ click: {} },
    { onClick: (...[$event]) => {
            __VLS_ctx.dialog = false;
            // @ts-ignore
            [dialog,];
        } });
const { default: __VLS_222 } = __VLS_218.slots;
// @ts-ignore
[];
var __VLS_218;
var __VLS_219;
let __VLS_223;
/** @ts-ignore @type {typeof __VLS_components.vBtn | typeof __VLS_components.VBtn | typeof __VLS_components.vBtn | typeof __VLS_components.VBtn} */
vBtn;
// @ts-ignore
const __VLS_224 = __VLS_asFunctionalComponent1(__VLS_223, new __VLS_223({
    ...{ 'onClick': {} },
    color: "primary",
    disabled: (__VLS_ctx.busy || !__VLS_ctx.canSubmit),
}));
const __VLS_225 = __VLS_224({
    ...{ 'onClick': {} },
    color: "primary",
    disabled: (__VLS_ctx.busy || !__VLS_ctx.canSubmit),
}, ...__VLS_functionalComponentArgsRest(__VLS_224));
let __VLS_228;
const __VLS_229 = ({ click: {} },
    { onClick: (__VLS_ctx.saveRuleSource) });
const { default: __VLS_230 } = __VLS_226.slots;
// @ts-ignore
[busy, canSubmit, saveRuleSource,];
var __VLS_226;
var __VLS_227;
// @ts-ignore
[];
var __VLS_207;
// @ts-ignore
[];
var __VLS_138;
// @ts-ignore
[];
var __VLS_132;
// @ts-ignore
[];
const __VLS_export = (await import('vue')).defineComponent({});
export default {};
