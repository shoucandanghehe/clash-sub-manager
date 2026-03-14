/// <reference types="../node_modules/@vue/language-core/types/template-helpers.d.ts" />
/// <reference types="../node_modules/@vue/language-core/types/props-fallback.d.ts" />
import { storeToRefs } from 'pinia';
import { computed, onMounted, ref, watch } from 'vue';
import { useDisplay, useTheme } from 'vuetify';
import MergeProfilesView from './views/MergeProfilesView.vue';
import PreviewView from './views/PreviewView.vue';
import RulesView from './views/RulesView.vue';
import SubscriptionsView from './views/SubscriptionsView.vue';
import TemplatesView from './views/TemplatesView.vue';
import { useManagerStore } from './stores/manager';
const THEME_STORAGE_KEY = 'clash-sub-manager-theme';
const store = useManagerStore();
const { busy, error, notice } = storeToRefs(store);
const display = useDisplay();
const theme = useTheme();
const drawer = ref(false);
const activeView = ref('subscriptions');
const noticeOpen = ref(false);
const errorOpen = ref(false);
const navigationItems = [
    { key: 'subscriptions', title: '订阅', subtitle: '管理远程订阅与内联配置', icon: 'mdi-rss' },
    { key: 'rules', title: '规则', subtitle: '维护规则源与合并规则', icon: 'mdi-format-list-bulleted' },
    { key: 'templates', title: '模板', subtitle: '编辑 Clash 模板 YAML', icon: 'mdi-file-document-edit-outline' },
    { key: 'mergeProfiles', title: '合并配置', subtitle: '定义要合并的订阅与模板', icon: 'mdi-source-merge' },
    { key: 'preview', title: '预览', subtitle: '查看转换与生成结果', icon: 'mdi-eye-outline' },
];
const componentMap = {
    subscriptions: SubscriptionsView,
    rules: RulesView,
    templates: TemplatesView,
    mergeProfiles: MergeProfilesView,
    preview: PreviewView,
};
const activeItem = computed(() => {
    return navigationItems.find((item) => item.key === activeView.value) ?? navigationItems[0];
});
const activeComponent = computed(() => componentMap[activeView.value]);
const isDark = computed(() => theme.global.current.value.dark);
watch(() => display.mdAndUp.value, (mdAndUp) => {
    drawer.value = mdAndUp;
}, { immediate: true });
watch(notice, (value) => {
    noticeOpen.value = value.length > 0;
}, { immediate: true });
watch(error, (value) => {
    errorOpen.value = value.length > 0;
}, { immediate: true });
watch(() => theme.global.name.value, (value) => {
    window.localStorage.setItem(THEME_STORAGE_KEY, String(value));
});
function selectView(view) {
    activeView.value = view;
    if (!display.mdAndUp.value) {
        drawer.value = false;
    }
}
function toggleTheme() {
    theme.global.name.value = isDark.value ? 'lightTheme' : 'darkTheme';
}
onMounted(async () => {
    const savedTheme = window.localStorage.getItem(THEME_STORAGE_KEY);
    if (savedTheme === 'lightTheme' || savedTheme === 'darkTheme') {
        theme.global.name.value = savedTheme;
    }
    await store.refreshAll();
});
const __VLS_ctx = {
    ...{},
    ...{},
};
let __VLS_components;
let __VLS_intrinsics;
let __VLS_directives;
let __VLS_0;
/** @ts-ignore @type {typeof __VLS_components.vApp | typeof __VLS_components.VApp | typeof __VLS_components.vApp | typeof __VLS_components.VApp} */
vApp;
// @ts-ignore
const __VLS_1 = __VLS_asFunctionalComponent1(__VLS_0, new __VLS_0({}));
const __VLS_2 = __VLS_1({}, ...__VLS_functionalComponentArgsRest(__VLS_1));
var __VLS_5 = {};
const { default: __VLS_6 } = __VLS_3.slots;
let __VLS_7;
/** @ts-ignore @type {typeof __VLS_components.vNavigationDrawer | typeof __VLS_components.VNavigationDrawer | typeof __VLS_components.vNavigationDrawer | typeof __VLS_components.VNavigationDrawer} */
vNavigationDrawer;
// @ts-ignore
const __VLS_8 = __VLS_asFunctionalComponent1(__VLS_7, new __VLS_7({
    modelValue: (__VLS_ctx.drawer),
    permanent: (__VLS_ctx.display.mdAndUp.value),
    temporary: (!__VLS_ctx.display.mdAndUp.value),
    rail: (__VLS_ctx.display.mdAndUp.value),
    border: "sm",
}));
const __VLS_9 = __VLS_8({
    modelValue: (__VLS_ctx.drawer),
    permanent: (__VLS_ctx.display.mdAndUp.value),
    temporary: (!__VLS_ctx.display.mdAndUp.value),
    rail: (__VLS_ctx.display.mdAndUp.value),
    border: "sm",
}, ...__VLS_functionalComponentArgsRest(__VLS_8));
const { default: __VLS_12 } = __VLS_10.slots;
let __VLS_13;
/** @ts-ignore @type {typeof __VLS_components.vList | typeof __VLS_components.VList | typeof __VLS_components.vList | typeof __VLS_components.VList} */
vList;
// @ts-ignore
const __VLS_14 = __VLS_asFunctionalComponent1(__VLS_13, new __VLS_13({
    nav: true,
    ...{ class: "py-4" },
}));
const __VLS_15 = __VLS_14({
    nav: true,
    ...{ class: "py-4" },
}, ...__VLS_functionalComponentArgsRest(__VLS_14));
/** @type {__VLS_StyleScopedClasses['py-4']} */ ;
const { default: __VLS_18 } = __VLS_16.slots;
if (!__VLS_ctx.display.mdAndUp.value) {
    let __VLS_19;
    /** @ts-ignore @type {typeof __VLS_components.vListSubheader | typeof __VLS_components.VListSubheader | typeof __VLS_components.vListSubheader | typeof __VLS_components.VListSubheader} */
    vListSubheader;
    // @ts-ignore
    const __VLS_20 = __VLS_asFunctionalComponent1(__VLS_19, new __VLS_19({}));
    const __VLS_21 = __VLS_20({}, ...__VLS_functionalComponentArgsRest(__VLS_20));
    const { default: __VLS_24 } = __VLS_22.slots;
    // @ts-ignore
    [drawer, display, display, display, display,];
    var __VLS_22;
}
for (const [item] of __VLS_vFor((__VLS_ctx.navigationItems))) {
    let __VLS_25;
    /** @ts-ignore @type {typeof __VLS_components.vListItem | typeof __VLS_components.VListItem} */
    vListItem;
    // @ts-ignore
    const __VLS_26 = __VLS_asFunctionalComponent1(__VLS_25, new __VLS_25({
        ...{ 'onClick': {} },
        key: (item.key),
        active: (__VLS_ctx.activeView === item.key),
        prependIcon: (item.icon),
        title: (item.title),
        subtitle: (__VLS_ctx.display.mdAndUp.value ? undefined : item.subtitle),
        rounded: "xl",
    }));
    const __VLS_27 = __VLS_26({
        ...{ 'onClick': {} },
        key: (item.key),
        active: (__VLS_ctx.activeView === item.key),
        prependIcon: (item.icon),
        title: (item.title),
        subtitle: (__VLS_ctx.display.mdAndUp.value ? undefined : item.subtitle),
        rounded: "xl",
    }, ...__VLS_functionalComponentArgsRest(__VLS_26));
    let __VLS_30;
    const __VLS_31 = ({ click: {} },
        { onClick: (...[$event]) => {
                __VLS_ctx.selectView(item.key);
                // @ts-ignore
                [display, navigationItems, activeView, selectView,];
            } });
    var __VLS_28;
    var __VLS_29;
    // @ts-ignore
    [];
}
// @ts-ignore
[];
var __VLS_16;
// @ts-ignore
[];
var __VLS_10;
let __VLS_32;
/** @ts-ignore @type {typeof __VLS_components.vAppBar | typeof __VLS_components.VAppBar | typeof __VLS_components.vAppBar | typeof __VLS_components.VAppBar} */
vAppBar;
// @ts-ignore
const __VLS_33 = __VLS_asFunctionalComponent1(__VLS_32, new __VLS_32({
    flat: true,
}));
const __VLS_34 = __VLS_33({
    flat: true,
}, ...__VLS_functionalComponentArgsRest(__VLS_33));
const { default: __VLS_37 } = __VLS_35.slots;
if (!__VLS_ctx.display.mdAndUp.value) {
    {
        const { prepend: __VLS_38 } = __VLS_35.slots;
        let __VLS_39;
        /** @ts-ignore @type {typeof __VLS_components.vAppBarNavIcon | typeof __VLS_components.VAppBarNavIcon} */
        vAppBarNavIcon;
        // @ts-ignore
        const __VLS_40 = __VLS_asFunctionalComponent1(__VLS_39, new __VLS_39({
            ...{ 'onClick': {} },
        }));
        const __VLS_41 = __VLS_40({
            ...{ 'onClick': {} },
        }, ...__VLS_functionalComponentArgsRest(__VLS_40));
        let __VLS_44;
        const __VLS_45 = ({ click: {} },
            { onClick: (...[$event]) => {
                    if (!(!__VLS_ctx.display.mdAndUp.value))
                        return;
                    __VLS_ctx.drawer = !__VLS_ctx.drawer;
                    // @ts-ignore
                    [drawer, drawer, display,];
                } });
        var __VLS_42;
        var __VLS_43;
        // @ts-ignore
        [];
    }
}
let __VLS_46;
/** @ts-ignore @type {typeof __VLS_components.vAppBarTitle | typeof __VLS_components.VAppBarTitle | typeof __VLS_components.vAppBarTitle | typeof __VLS_components.VAppBarTitle} */
vAppBarTitle;
// @ts-ignore
const __VLS_47 = __VLS_asFunctionalComponent1(__VLS_46, new __VLS_46({}));
const __VLS_48 = __VLS_47({}, ...__VLS_functionalComponentArgsRest(__VLS_47));
const { default: __VLS_51 } = __VLS_49.slots;
__VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "app-title" },
});
/** @type {__VLS_StyleScopedClasses['app-title']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({
    ...{ class: "text-h6 font-weight-medium" },
});
/** @type {__VLS_StyleScopedClasses['text-h6']} */ ;
/** @type {__VLS_StyleScopedClasses['font-weight-medium']} */ ;
__VLS_asFunctionalElement1(__VLS_intrinsics.span, __VLS_intrinsics.span)({
    ...{ class: "text-body-2 text-medium-emphasis" },
});
/** @type {__VLS_StyleScopedClasses['text-body-2']} */ ;
/** @type {__VLS_StyleScopedClasses['text-medium-emphasis']} */ ;
(__VLS_ctx.activeItem.subtitle);
// @ts-ignore
[activeItem,];
var __VLS_49;
{
    const { append: __VLS_52 } = __VLS_35.slots;
    let __VLS_53;
    /** @ts-ignore @type {typeof __VLS_components.vBtn | typeof __VLS_components.VBtn} */
    vBtn;
    // @ts-ignore
    const __VLS_54 = __VLS_asFunctionalComponent1(__VLS_53, new __VLS_53({
        ...{ 'onClick': {} },
        disabled: (__VLS_ctx.busy),
        icon: "mdi-refresh",
        variant: "text",
    }));
    const __VLS_55 = __VLS_54({
        ...{ 'onClick': {} },
        disabled: (__VLS_ctx.busy),
        icon: "mdi-refresh",
        variant: "text",
    }, ...__VLS_functionalComponentArgsRest(__VLS_54));
    let __VLS_58;
    const __VLS_59 = ({ click: {} },
        { onClick: (__VLS_ctx.store.refreshAll) });
    var __VLS_56;
    var __VLS_57;
    let __VLS_60;
    /** @ts-ignore @type {typeof __VLS_components.vBtn | typeof __VLS_components.VBtn} */
    vBtn;
    // @ts-ignore
    const __VLS_61 = __VLS_asFunctionalComponent1(__VLS_60, new __VLS_60({
        ...{ 'onClick': {} },
        icon: (__VLS_ctx.isDark ? 'mdi-weather-sunny' : 'mdi-weather-night'),
        variant: "text",
    }));
    const __VLS_62 = __VLS_61({
        ...{ 'onClick': {} },
        icon: (__VLS_ctx.isDark ? 'mdi-weather-sunny' : 'mdi-weather-night'),
        variant: "text",
    }, ...__VLS_functionalComponentArgsRest(__VLS_61));
    let __VLS_65;
    const __VLS_66 = ({ click: {} },
        { onClick: (__VLS_ctx.toggleTheme) });
    var __VLS_63;
    var __VLS_64;
    // @ts-ignore
    [busy, store, isDark, toggleTheme,];
}
// @ts-ignore
[];
var __VLS_35;
if (__VLS_ctx.busy) {
    let __VLS_67;
    /** @ts-ignore @type {typeof __VLS_components.vProgressLinear | typeof __VLS_components.VProgressLinear} */
    vProgressLinear;
    // @ts-ignore
    const __VLS_68 = __VLS_asFunctionalComponent1(__VLS_67, new __VLS_67({
        indeterminate: true,
        color: "primary",
    }));
    const __VLS_69 = __VLS_68({
        indeterminate: true,
        color: "primary",
    }, ...__VLS_functionalComponentArgsRest(__VLS_68));
}
let __VLS_72;
/** @ts-ignore @type {typeof __VLS_components.vMain | typeof __VLS_components.VMain | typeof __VLS_components.vMain | typeof __VLS_components.VMain} */
vMain;
// @ts-ignore
const __VLS_73 = __VLS_asFunctionalComponent1(__VLS_72, new __VLS_72({}));
const __VLS_74 = __VLS_73({}, ...__VLS_functionalComponentArgsRest(__VLS_73));
const { default: __VLS_77 } = __VLS_75.slots;
let __VLS_78;
/** @ts-ignore @type {typeof __VLS_components.vContainer | typeof __VLS_components.VContainer | typeof __VLS_components.vContainer | typeof __VLS_components.VContainer} */
vContainer;
// @ts-ignore
const __VLS_79 = __VLS_asFunctionalComponent1(__VLS_78, new __VLS_78({
    fluid: true,
    ...{ class: "pa-4 pa-sm-6" },
}));
const __VLS_80 = __VLS_79({
    fluid: true,
    ...{ class: "pa-4 pa-sm-6" },
}, ...__VLS_functionalComponentArgsRest(__VLS_79));
/** @type {__VLS_StyleScopedClasses['pa-4']} */ ;
/** @type {__VLS_StyleScopedClasses['pa-sm-6']} */ ;
const { default: __VLS_83 } = __VLS_81.slots;
let __VLS_84;
/** @ts-ignore @type {typeof __VLS_components.vRow | typeof __VLS_components.VRow | typeof __VLS_components.vRow | typeof __VLS_components.VRow} */
vRow;
// @ts-ignore
const __VLS_85 = __VLS_asFunctionalComponent1(__VLS_84, new __VLS_84({
    ...{ class: "mb-4" },
    align: "center",
    justify: "space-between",
}));
const __VLS_86 = __VLS_85({
    ...{ class: "mb-4" },
    align: "center",
    justify: "space-between",
}, ...__VLS_functionalComponentArgsRest(__VLS_85));
/** @type {__VLS_StyleScopedClasses['mb-4']} */ ;
const { default: __VLS_89 } = __VLS_87.slots;
let __VLS_90;
/** @ts-ignore @type {typeof __VLS_components.vCol | typeof __VLS_components.VCol | typeof __VLS_components.vCol | typeof __VLS_components.VCol} */
vCol;
// @ts-ignore
const __VLS_91 = __VLS_asFunctionalComponent1(__VLS_90, new __VLS_90({
    cols: "12",
    md: "8",
}));
const __VLS_92 = __VLS_91({
    cols: "12",
    md: "8",
}, ...__VLS_functionalComponentArgsRest(__VLS_91));
const { default: __VLS_95 } = __VLS_93.slots;
__VLS_asFunctionalElement1(__VLS_intrinsics.div, __VLS_intrinsics.div)({
    ...{ class: "text-overline text-primary" },
});
/** @type {__VLS_StyleScopedClasses['text-overline']} */ ;
/** @type {__VLS_StyleScopedClasses['text-primary']} */ ;
(__VLS_ctx.activeItem.title);
__VLS_asFunctionalElement1(__VLS_intrinsics.h1, __VLS_intrinsics.h1)({
    ...{ class: "text-h4 font-weight-bold mb-2" },
});
/** @type {__VLS_StyleScopedClasses['text-h4']} */ ;
/** @type {__VLS_StyleScopedClasses['font-weight-bold']} */ ;
/** @type {__VLS_StyleScopedClasses['mb-2']} */ ;
(__VLS_ctx.activeItem.title);
__VLS_asFunctionalElement1(__VLS_intrinsics.p, __VLS_intrinsics.p)({
    ...{ class: "text-body-1 text-medium-emphasis mb-0" },
});
/** @type {__VLS_StyleScopedClasses['text-body-1']} */ ;
/** @type {__VLS_StyleScopedClasses['text-medium-emphasis']} */ ;
/** @type {__VLS_StyleScopedClasses['mb-0']} */ ;
(__VLS_ctx.activeItem.subtitle);
// @ts-ignore
[activeItem, activeItem, activeItem, busy,];
var __VLS_93;
// @ts-ignore
[];
var __VLS_87;
const __VLS_96 = (__VLS_ctx.activeComponent);
// @ts-ignore
const __VLS_97 = __VLS_asFunctionalComponent1(__VLS_96, new __VLS_96({
    ...{ 'onNavigatePreview': {} },
}));
const __VLS_98 = __VLS_97({
    ...{ 'onNavigatePreview': {} },
}, ...__VLS_functionalComponentArgsRest(__VLS_97));
let __VLS_101;
const __VLS_102 = ({ navigatePreview: {} },
    { onNavigatePreview: (...[$event]) => {
            __VLS_ctx.selectView('preview');
            // @ts-ignore
            [selectView, activeComponent,];
        } });
var __VLS_99;
var __VLS_100;
// @ts-ignore
[];
var __VLS_81;
// @ts-ignore
[];
var __VLS_75;
let __VLS_103;
/** @ts-ignore @type {typeof __VLS_components.vSnackbar | typeof __VLS_components.VSnackbar | typeof __VLS_components.vSnackbar | typeof __VLS_components.VSnackbar} */
vSnackbar;
// @ts-ignore
const __VLS_104 = __VLS_asFunctionalComponent1(__VLS_103, new __VLS_103({
    ...{ 'onUpdate:modelValue': {} },
    modelValue: (__VLS_ctx.noticeOpen),
    color: "primary",
    timeout: "3200",
    location: "top right",
}));
const __VLS_105 = __VLS_104({
    ...{ 'onUpdate:modelValue': {} },
    modelValue: (__VLS_ctx.noticeOpen),
    color: "primary",
    timeout: "3200",
    location: "top right",
}, ...__VLS_functionalComponentArgsRest(__VLS_104));
let __VLS_108;
const __VLS_109 = ({ 'update:modelValue': {} },
    { 'onUpdate:modelValue': (...[$event]) => {
            !$event && __VLS_ctx.store.clearNotice();
            // @ts-ignore
            [store, noticeOpen,];
        } });
const { default: __VLS_110 } = __VLS_106.slots;
(__VLS_ctx.notice);
// @ts-ignore
[notice,];
var __VLS_106;
var __VLS_107;
let __VLS_111;
/** @ts-ignore @type {typeof __VLS_components.vSnackbar | typeof __VLS_components.VSnackbar | typeof __VLS_components.vSnackbar | typeof __VLS_components.VSnackbar} */
vSnackbar;
// @ts-ignore
const __VLS_112 = __VLS_asFunctionalComponent1(__VLS_111, new __VLS_111({
    ...{ 'onUpdate:modelValue': {} },
    modelValue: (__VLS_ctx.errorOpen),
    color: "error",
    timeout: "4800",
    location: "top right",
}));
const __VLS_113 = __VLS_112({
    ...{ 'onUpdate:modelValue': {} },
    modelValue: (__VLS_ctx.errorOpen),
    color: "error",
    timeout: "4800",
    location: "top right",
}, ...__VLS_functionalComponentArgsRest(__VLS_112));
let __VLS_116;
const __VLS_117 = ({ 'update:modelValue': {} },
    { 'onUpdate:modelValue': (...[$event]) => {
            !$event && __VLS_ctx.store.clearError();
            // @ts-ignore
            [store, errorOpen,];
        } });
const { default: __VLS_118 } = __VLS_114.slots;
(__VLS_ctx.error);
// @ts-ignore
[error,];
var __VLS_114;
var __VLS_115;
// @ts-ignore
[];
var __VLS_3;
// @ts-ignore
[];
const __VLS_export = (await import('vue')).defineComponent({});
export default {};
