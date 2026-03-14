/// <reference types="../../node_modules/@vue/language-core/types/template-helpers.d.ts" />
/// <reference types="../../node_modules/@vue/language-core/types/props-fallback.d.ts" />
import { storeToRefs } from 'pinia';
import { computed, ref, watch } from 'vue';
import { useManagerStore } from '../stores/manager';
const store = useManagerStore();
const { busy, convertPreview, mergePreview, mergeProfilePreview, mergeProfilePreviewName, subscriptions, templates, } = storeToRefs(store);
const convertMode = ref('content');
const convertValue = ref('trojan://secret@example.com:443#Demo');
const selectedTemplateId = ref(null);
const enabledSubscriptionCount = computed(() => {
    return subscriptions.value.filter((subscription) => subscription.enabled).length;
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
async function generateConvertPreview() {
    if (!convertValue.value.trim()) {
        return;
    }
    const payload = convertMode.value === 'content'
        ? { content: convertValue.value.trim() }
        : { url: convertValue.value.trim() };
    await store.runConvertPreview(payload);
}
async function generateMergePreview() {
    await store.runMergePreview(selectedTemplateId.value);
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
var __VLS_5 = {};
const { default: __VLS_6 } = __VLS_3.slots;
let __VLS_7;
/** @ts-ignore @type {typeof __VLS_components.vCol | typeof __VLS_components.VCol | typeof __VLS_components.vCol | typeof __VLS_components.VCol} */
vCol;
// @ts-ignore
const __VLS_8 = __VLS_asFunctionalComponent1(__VLS_7, new __VLS_7({
    cols: "12",
    xl: "4",
}));
const __VLS_9 = __VLS_8({
    cols: "12",
    xl: "4",
}, ...__VLS_functionalComponentArgsRest(__VLS_8));
const { default: __VLS_12 } = __VLS_10.slots;
let __VLS_13;
/** @ts-ignore @type {typeof __VLS_components.vCard | typeof __VLS_components.VCard | typeof __VLS_components.vCard | typeof __VLS_components.VCard} */
vCard;
// @ts-ignore
const __VLS_14 = __VLS_asFunctionalComponent1(__VLS_13, new __VLS_13({
    ...{ class: "fill-height" },
}));
const __VLS_15 = __VLS_14({
    ...{ class: "fill-height" },
}, ...__VLS_functionalComponentArgsRest(__VLS_14));
/** @type {__VLS_StyleScopedClasses['fill-height']} */ ;
const { default: __VLS_18 } = __VLS_16.slots;
let __VLS_19;
/** @ts-ignore @type {typeof __VLS_components.vCardItem | typeof __VLS_components.VCardItem | typeof __VLS_components.vCardItem | typeof __VLS_components.VCardItem} */
vCardItem;
// @ts-ignore
const __VLS_20 = __VLS_asFunctionalComponent1(__VLS_19, new __VLS_19({}));
const __VLS_21 = __VLS_20({}, ...__VLS_functionalComponentArgsRest(__VLS_20));
const { default: __VLS_24 } = __VLS_22.slots;
let __VLS_25;
/** @ts-ignore @type {typeof __VLS_components.vCardTitle | typeof __VLS_components.VCardTitle | typeof __VLS_components.vCardTitle | typeof __VLS_components.VCardTitle} */
vCardTitle;
// @ts-ignore
const __VLS_26 = __VLS_asFunctionalComponent1(__VLS_25, new __VLS_25({
    ...{ class: "px-0" },
}));
const __VLS_27 = __VLS_26({
    ...{ class: "px-0" },
}, ...__VLS_functionalComponentArgsRest(__VLS_26));
/** @type {__VLS_StyleScopedClasses['px-0']} */ ;
const { default: __VLS_30 } = __VLS_28.slots;
var __VLS_28;
let __VLS_31;
/** @ts-ignore @type {typeof __VLS_components.vCardSubtitle | typeof __VLS_components.VCardSubtitle | typeof __VLS_components.vCardSubtitle | typeof __VLS_components.VCardSubtitle} */
vCardSubtitle;
// @ts-ignore
const __VLS_32 = __VLS_asFunctionalComponent1(__VLS_31, new __VLS_31({
    ...{ class: "px-0" },
}));
const __VLS_33 = __VLS_32({
    ...{ class: "px-0" },
}, ...__VLS_functionalComponentArgsRest(__VLS_32));
/** @type {__VLS_StyleScopedClasses['px-0']} */ ;
const { default: __VLS_36 } = __VLS_34.slots;
var __VLS_34;
var __VLS_22;
let __VLS_37;
/** @ts-ignore @type {typeof __VLS_components.vCardText | typeof __VLS_components.VCardText | typeof __VLS_components.vCardText | typeof __VLS_components.VCardText} */
vCardText;
// @ts-ignore
const __VLS_38 = __VLS_asFunctionalComponent1(__VLS_37, new __VLS_37({}));
const __VLS_39 = __VLS_38({}, ...__VLS_functionalComponentArgsRest(__VLS_38));
const { default: __VLS_42 } = __VLS_40.slots;
__VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "d-flex flex-column ga-4" },
});
/** @type {__VLS_StyleScopedClasses['d-flex']} */ ;
/** @type {__VLS_StyleScopedClasses['flex-column']} */ ;
/** @type {__VLS_StyleScopedClasses['ga-4']} */ ;
let __VLS_43;
/** @ts-ignore @type {typeof __VLS_components.vBtnToggle | typeof __VLS_components.VBtnToggle | typeof __VLS_components.vBtnToggle | typeof __VLS_components.VBtnToggle} */
vBtnToggle;
// @ts-ignore
const __VLS_44 = __VLS_asFunctionalComponent1(__VLS_43, new __VLS_43({
    modelValue: (__VLS_ctx.convertMode),
    color: "primary",
    mandatory: true,
}));
const __VLS_45 = __VLS_44({
    modelValue: (__VLS_ctx.convertMode),
    color: "primary",
    mandatory: true,
}, ...__VLS_functionalComponentArgsRest(__VLS_44));
const { default: __VLS_48 } = __VLS_46.slots;
let __VLS_49;
/** @ts-ignore @type {typeof __VLS_components.vBtn | typeof __VLS_components.VBtn | typeof __VLS_components.vBtn | typeof __VLS_components.VBtn} */
vBtn;
// @ts-ignore
const __VLS_50 = __VLS_asFunctionalComponent1(__VLS_49, new __VLS_49({
    value: "content",
}));
const __VLS_51 = __VLS_50({
    value: "content",
}, ...__VLS_functionalComponentArgsRest(__VLS_50));
const { default: __VLS_54 } = __VLS_52.slots;
// @ts-ignore
[convertMode,];
var __VLS_52;
let __VLS_55;
/** @ts-ignore @type {typeof __VLS_components.vBtn | typeof __VLS_components.VBtn | typeof __VLS_components.vBtn | typeof __VLS_components.VBtn} */
vBtn;
// @ts-ignore
const __VLS_56 = __VLS_asFunctionalComponent1(__VLS_55, new __VLS_55({
    value: "url",
}));
const __VLS_57 = __VLS_56({
    value: "url",
}, ...__VLS_functionalComponentArgsRest(__VLS_56));
const { default: __VLS_60 } = __VLS_58.slots;
// @ts-ignore
[];
var __VLS_58;
// @ts-ignore
[];
var __VLS_46;
let __VLS_61;
/** @ts-ignore @type {typeof __VLS_components.vTextarea | typeof __VLS_components.VTextarea} */
vTextarea;
// @ts-ignore
const __VLS_62 = __VLS_asFunctionalComponent1(__VLS_61, new __VLS_61({
    modelValue: (__VLS_ctx.convertValue),
    label: (__VLS_ctx.convertMode === 'content' ? '分享链接或内联内容' : '订阅链接'),
    rows: "8",
}));
const __VLS_63 = __VLS_62({
    modelValue: (__VLS_ctx.convertValue),
    label: (__VLS_ctx.convertMode === 'content' ? '分享链接或内联内容' : '订阅链接'),
    rows: "8",
}, ...__VLS_functionalComponentArgsRest(__VLS_62));
let __VLS_66;
/** @ts-ignore @type {typeof __VLS_components.vBtn | typeof __VLS_components.VBtn | typeof __VLS_components.vBtn | typeof __VLS_components.VBtn} */
vBtn;
// @ts-ignore
const __VLS_67 = __VLS_asFunctionalComponent1(__VLS_66, new __VLS_66({
    ...{ 'onClick': {} },
    color: "primary",
    disabled: (__VLS_ctx.busy || !__VLS_ctx.convertValue.trim()),
}));
const __VLS_68 = __VLS_67({
    ...{ 'onClick': {} },
    color: "primary",
    disabled: (__VLS_ctx.busy || !__VLS_ctx.convertValue.trim()),
}, ...__VLS_functionalComponentArgsRest(__VLS_67));
let __VLS_71;
const __VLS_72 = ({ click: {} },
    { onClick: (__VLS_ctx.generateConvertPreview) });
const { default: __VLS_73 } = __VLS_69.slots;
// @ts-ignore
[convertMode, convertValue, convertValue, busy, generateConvertPreview,];
var __VLS_69;
var __VLS_70;
let __VLS_74;
/** @ts-ignore @type {typeof __VLS_components.vSheet | typeof __VLS_components.VSheet | typeof __VLS_components.vSheet | typeof __VLS_components.VSheet} */
vSheet;
// @ts-ignore
const __VLS_75 = __VLS_asFunctionalComponent1(__VLS_74, new __VLS_74({
    ...{ class: "preview-panel" },
    color: "surface-variant",
    rounded: "xl",
}));
const __VLS_76 = __VLS_75({
    ...{ class: "preview-panel" },
    color: "surface-variant",
    rounded: "xl",
}, ...__VLS_functionalComponentArgsRest(__VLS_75));
/** @type {__VLS_StyleScopedClasses['preview-panel']} */ ;
const { default: __VLS_79 } = __VLS_77.slots;
__VLS_asFunctionalElement1(__VLS_intrinsics.pre, __VLS_intrinsics.pre)({});
(__VLS_ctx.convertPreview || '尚未生成转换预览。');
// @ts-ignore
[convertPreview,];
var __VLS_77;
// @ts-ignore
[];
var __VLS_40;
// @ts-ignore
[];
var __VLS_16;
// @ts-ignore
[];
var __VLS_10;
let __VLS_80;
/** @ts-ignore @type {typeof __VLS_components.vCol | typeof __VLS_components.VCol | typeof __VLS_components.vCol | typeof __VLS_components.VCol} */
vCol;
// @ts-ignore
const __VLS_81 = __VLS_asFunctionalComponent1(__VLS_80, new __VLS_80({
    cols: "12",
    xl: "4",
}));
const __VLS_82 = __VLS_81({
    cols: "12",
    xl: "4",
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
// @ts-ignore
[];
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
__VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "d-flex flex-column ga-4" },
});
/** @type {__VLS_StyleScopedClasses['d-flex']} */ ;
/** @type {__VLS_StyleScopedClasses['flex-column']} */ ;
/** @type {__VLS_StyleScopedClasses['ga-4']} */ ;
let __VLS_116;
/** @ts-ignore @type {typeof __VLS_components.vSelect | typeof __VLS_components.VSelect} */
vSelect;
// @ts-ignore
const __VLS_117 = __VLS_asFunctionalComponent1(__VLS_116, new __VLS_116({
    modelValue: (__VLS_ctx.selectedTemplateId),
    items: (__VLS_ctx.templates),
    itemTitle: "name",
    itemValue: "id",
    label: "预览模板",
    clearable: true,
}));
const __VLS_118 = __VLS_117({
    modelValue: (__VLS_ctx.selectedTemplateId),
    items: (__VLS_ctx.templates),
    itemTitle: "name",
    itemValue: "id",
    label: "预览模板",
    clearable: true,
}, ...__VLS_functionalComponentArgsRest(__VLS_117));
let __VLS_121;
/** @ts-ignore @type {typeof __VLS_components.vAlert | typeof __VLS_components.VAlert | typeof __VLS_components.vAlert | typeof __VLS_components.VAlert} */
vAlert;
// @ts-ignore
const __VLS_122 = __VLS_asFunctionalComponent1(__VLS_121, new __VLS_121({
    color: "primary",
    density: "comfortable",
    variant: "tonal",
}));
const __VLS_123 = __VLS_122({
    color: "primary",
    density: "comfortable",
    variant: "tonal",
}, ...__VLS_functionalComponentArgsRest(__VLS_122));
const { default: __VLS_126 } = __VLS_124.slots;
(__VLS_ctx.enabledSubscriptionCount);
// @ts-ignore
[selectedTemplateId, templates, enabledSubscriptionCount,];
var __VLS_124;
let __VLS_127;
/** @ts-ignore @type {typeof __VLS_components.vBtn | typeof __VLS_components.VBtn | typeof __VLS_components.vBtn | typeof __VLS_components.VBtn} */
vBtn;
// @ts-ignore
const __VLS_128 = __VLS_asFunctionalComponent1(__VLS_127, new __VLS_127({
    ...{ 'onClick': {} },
    color: "primary",
    disabled: (__VLS_ctx.busy || __VLS_ctx.enabledSubscriptionCount === 0),
}));
const __VLS_129 = __VLS_128({
    ...{ 'onClick': {} },
    color: "primary",
    disabled: (__VLS_ctx.busy || __VLS_ctx.enabledSubscriptionCount === 0),
}, ...__VLS_functionalComponentArgsRest(__VLS_128));
let __VLS_132;
const __VLS_133 = ({ click: {} },
    { onClick: (__VLS_ctx.generateMergePreview) });
const { default: __VLS_134 } = __VLS_130.slots;
// @ts-ignore
[busy, enabledSubscriptionCount, generateMergePreview,];
var __VLS_130;
var __VLS_131;
let __VLS_135;
/** @ts-ignore @type {typeof __VLS_components.vSheet | typeof __VLS_components.VSheet | typeof __VLS_components.vSheet | typeof __VLS_components.VSheet} */
vSheet;
// @ts-ignore
const __VLS_136 = __VLS_asFunctionalComponent1(__VLS_135, new __VLS_135({
    ...{ class: "preview-panel" },
    color: "surface-variant",
    rounded: "xl",
}));
const __VLS_137 = __VLS_136({
    ...{ class: "preview-panel" },
    color: "surface-variant",
    rounded: "xl",
}, ...__VLS_functionalComponentArgsRest(__VLS_136));
/** @type {__VLS_StyleScopedClasses['preview-panel']} */ ;
const { default: __VLS_140 } = __VLS_138.slots;
__VLS_asFunctionalElement1(__VLS_intrinsics.pre, __VLS_intrinsics.pre)({});
(__VLS_ctx.mergePreview || '尚未生成合并预览。');
// @ts-ignore
[mergePreview,];
var __VLS_138;
// @ts-ignore
[];
var __VLS_113;
// @ts-ignore
[];
var __VLS_89;
// @ts-ignore
[];
var __VLS_83;
let __VLS_141;
/** @ts-ignore @type {typeof __VLS_components.vCol | typeof __VLS_components.VCol | typeof __VLS_components.vCol | typeof __VLS_components.VCol} */
vCol;
// @ts-ignore
const __VLS_142 = __VLS_asFunctionalComponent1(__VLS_141, new __VLS_141({
    cols: "12",
    xl: "4",
}));
const __VLS_143 = __VLS_142({
    cols: "12",
    xl: "4",
}, ...__VLS_functionalComponentArgsRest(__VLS_142));
const { default: __VLS_146 } = __VLS_144.slots;
let __VLS_147;
/** @ts-ignore @type {typeof __VLS_components.vCard | typeof __VLS_components.VCard | typeof __VLS_components.vCard | typeof __VLS_components.VCard} */
vCard;
// @ts-ignore
const __VLS_148 = __VLS_asFunctionalComponent1(__VLS_147, new __VLS_147({
    ...{ class: "fill-height" },
}));
const __VLS_149 = __VLS_148({
    ...{ class: "fill-height" },
}, ...__VLS_functionalComponentArgsRest(__VLS_148));
/** @type {__VLS_StyleScopedClasses['fill-height']} */ ;
const { default: __VLS_152 } = __VLS_150.slots;
let __VLS_153;
/** @ts-ignore @type {typeof __VLS_components.vCardItem | typeof __VLS_components.VCardItem | typeof __VLS_components.vCardItem | typeof __VLS_components.VCardItem} */
vCardItem;
// @ts-ignore
const __VLS_154 = __VLS_asFunctionalComponent1(__VLS_153, new __VLS_153({}));
const __VLS_155 = __VLS_154({}, ...__VLS_functionalComponentArgsRest(__VLS_154));
const { default: __VLS_158 } = __VLS_156.slots;
let __VLS_159;
/** @ts-ignore @type {typeof __VLS_components.vCardTitle | typeof __VLS_components.VCardTitle | typeof __VLS_components.vCardTitle | typeof __VLS_components.VCardTitle} */
vCardTitle;
// @ts-ignore
const __VLS_160 = __VLS_asFunctionalComponent1(__VLS_159, new __VLS_159({
    ...{ class: "px-0" },
}));
const __VLS_161 = __VLS_160({
    ...{ class: "px-0" },
}, ...__VLS_functionalComponentArgsRest(__VLS_160));
/** @type {__VLS_StyleScopedClasses['px-0']} */ ;
const { default: __VLS_164 } = __VLS_162.slots;
// @ts-ignore
[];
var __VLS_162;
let __VLS_165;
/** @ts-ignore @type {typeof __VLS_components.vCardSubtitle | typeof __VLS_components.VCardSubtitle | typeof __VLS_components.vCardSubtitle | typeof __VLS_components.VCardSubtitle} */
vCardSubtitle;
// @ts-ignore
const __VLS_166 = __VLS_asFunctionalComponent1(__VLS_165, new __VLS_165({
    ...{ class: "px-0" },
}));
const __VLS_167 = __VLS_166({
    ...{ class: "px-0" },
}, ...__VLS_functionalComponentArgsRest(__VLS_166));
/** @type {__VLS_StyleScopedClasses['px-0']} */ ;
const { default: __VLS_170 } = __VLS_168.slots;
(__VLS_ctx.mergeProfilePreviewName || '从“合并配置”页面点击生成后会显示在这里。');
// @ts-ignore
[mergeProfilePreviewName,];
var __VLS_168;
// @ts-ignore
[];
var __VLS_156;
let __VLS_171;
/** @ts-ignore @type {typeof __VLS_components.vCardText | typeof __VLS_components.VCardText | typeof __VLS_components.vCardText | typeof __VLS_components.VCardText} */
vCardText;
// @ts-ignore
const __VLS_172 = __VLS_asFunctionalComponent1(__VLS_171, new __VLS_171({}));
const __VLS_173 = __VLS_172({}, ...__VLS_functionalComponentArgsRest(__VLS_172));
const { default: __VLS_176 } = __VLS_174.slots;
let __VLS_177;
/** @ts-ignore @type {typeof __VLS_components.vSheet | typeof __VLS_components.VSheet | typeof __VLS_components.vSheet | typeof __VLS_components.VSheet} */
vSheet;
// @ts-ignore
const __VLS_178 = __VLS_asFunctionalComponent1(__VLS_177, new __VLS_177({
    ...{ class: "preview-panel" },
    color: "surface-variant",
    rounded: "xl",
}));
const __VLS_179 = __VLS_178({
    ...{ class: "preview-panel" },
    color: "surface-variant",
    rounded: "xl",
}, ...__VLS_functionalComponentArgsRest(__VLS_178));
/** @type {__VLS_StyleScopedClasses['preview-panel']} */ ;
const { default: __VLS_182 } = __VLS_180.slots;
__VLS_asFunctionalElement1(__VLS_intrinsics.pre, __VLS_intrinsics.pre)({});
(__VLS_ctx.mergeProfilePreview || '尚未生成合并配置预览。');
// @ts-ignore
[mergeProfilePreview,];
var __VLS_180;
// @ts-ignore
[];
var __VLS_174;
// @ts-ignore
[];
var __VLS_150;
// @ts-ignore
[];
var __VLS_144;
// @ts-ignore
[];
var __VLS_3;
// @ts-ignore
[];
const __VLS_export = (await import('vue')).defineComponent({});
export default {};
