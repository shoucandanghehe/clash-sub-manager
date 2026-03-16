<script setup lang="ts">
import { storeToRefs } from 'pinia'
import { computed, onMounted, ref, watch, type Component } from 'vue'
import { useDisplay, useTheme } from 'vuetify'

import MergeProfilesView from './views/MergeProfilesView.vue'
import PreviewView from './views/PreviewView.vue'
import RulesView from './views/RulesView.vue'
import SubscriptionsView from './views/SubscriptionsView.vue'
import TemplatesView from './views/TemplatesView.vue'
import { useManagerStore } from './stores/manager'

type ViewKey = 'subscriptions' | 'rules' | 'templates' | 'mergeProfiles' | 'preview'
type ThemeName = 'lightTheme' | 'darkTheme'

interface NavigationItem {
  key: ViewKey
  title: string
  subtitle: string
  icon: string
}

const THEME_STORAGE_KEY = 'clash-sub-manager-theme'

const store = useManagerStore()
const { busy, error, notice } = storeToRefs(store)
const display = useDisplay()
const theme = useTheme()

const drawer = ref(false)
const activeView = ref<ViewKey>('subscriptions')
const noticeOpen = ref(false)
const errorOpen = ref(false)

const navigationItems: NavigationItem[] = [
  { key: 'subscriptions', title: '订阅', subtitle: '管理远程订阅与内联配置', icon: 'mdi-rss' },
  { key: 'rules', title: '规则', subtitle: '维护规则源与查看缓存详情', icon: 'mdi-format-list-bulleted' },
  { key: 'templates', title: '模板', subtitle: '编辑 Clash 模板 YAML', icon: 'mdi-file-document-edit-outline' },
  { key: 'mergeProfiles', title: '合并配置', subtitle: '定义要合并的订阅与模板', icon: 'mdi-source-merge' },
  { key: 'preview', title: '预览', subtitle: '查看转换与生成结果', icon: 'mdi-eye-outline' },
]

const componentMap: Record<ViewKey, Component> = {
  subscriptions: SubscriptionsView,
  rules: RulesView,
  templates: TemplatesView,
  mergeProfiles: MergeProfilesView,
  preview: PreviewView,
}

const activeItem = computed<NavigationItem>(() => {
  return navigationItems.find((item) => item.key === activeView.value) ?? navigationItems[0]
})

const activeComponent = computed<Component>(() => componentMap[activeView.value])
const isDark = computed<boolean>(() => theme.global.current.value.dark)

watch(
  () => display.mdAndUp.value,
  (mdAndUp) => {
    drawer.value = mdAndUp
  },
  { immediate: true },
)

watch(
  notice,
  (value) => {
    noticeOpen.value = value.length > 0
  },
  { immediate: true },
)

watch(
  error,
  (value) => {
    errorOpen.value = value.length > 0
  },
  { immediate: true },
)

watch(
  () => theme.global.name.value,
  (value) => {
    window.localStorage.setItem(THEME_STORAGE_KEY, String(value))
  },
)

function selectView(view: ViewKey): void {
  activeView.value = view
  if (!display.mdAndUp.value) {
    drawer.value = false
  }
}

function toggleTheme(): void {
  theme.global.name.value = isDark.value ? 'lightTheme' : 'darkTheme'
}

onMounted(async () => {
  const savedTheme = window.localStorage.getItem(THEME_STORAGE_KEY)
  if (savedTheme === 'lightTheme' || savedTheme === 'darkTheme') {
    theme.global.name.value = savedTheme satisfies ThemeName
  }
  await store.refreshAll()
})
</script>

<template>
  <v-app>
    <v-navigation-drawer
      v-model="drawer"
      :permanent="display.mdAndUp.value"
      :temporary="!display.mdAndUp.value"
      :rail="display.mdAndUp.value"
      border="sm"
    >
      <v-list nav class="py-4">
        <v-list-subheader v-if="!display.mdAndUp.value">Clash 订阅管理器</v-list-subheader>
        <v-list-item
          v-for="item in navigationItems"
          :key="item.key"
          :active="activeView === item.key"
          :prepend-icon="item.icon"
          :title="item.title"
          :subtitle="display.mdAndUp.value ? undefined : item.subtitle"
          rounded="xl"
          @click="selectView(item.key)"
        />
      </v-list>
    </v-navigation-drawer>

    <v-app-bar flat>
      <template v-if="!display.mdAndUp.value" #prepend>
        <v-app-bar-nav-icon @click="drawer = !drawer" />
      </template>

      <v-app-bar-title>
        <div class="app-title">
          <span class="text-h6 font-weight-medium">Clash 订阅管理器</span>
          <span class="text-body-2 text-medium-emphasis">{{ activeItem.subtitle }}</span>
        </div>
      </v-app-bar-title>

      <template #append>
        <v-btn :disabled="busy" icon="mdi-refresh" variant="text" @click="store.refreshAll" />
        <v-btn :icon="isDark ? 'mdi-weather-sunny' : 'mdi-weather-night'" variant="text" @click="toggleTheme" />
      </template>
    </v-app-bar>

    <v-progress-linear v-if="busy" indeterminate color="primary" />

    <v-main>
      <v-container fluid class="pa-4 pa-sm-6">
        <v-row class="mb-4" align="center" justify="space-between">
          <v-col cols="12" md="8">
            <div class="text-overline text-primary">{{ activeItem.title }}</div>
            <h1 class="text-h4 font-weight-bold mb-2">{{ activeItem.title }}</h1>
            <p class="text-body-1 text-medium-emphasis mb-0">{{ activeItem.subtitle }}</p>
          </v-col>
        </v-row>

        <component :is="activeComponent" @navigate-preview="selectView('preview')" />
      </v-container>
    </v-main>

    <v-snackbar v-model="noticeOpen" color="primary" timeout="3200" location="top right" @update:model-value="!$event && store.clearNotice()">
      {{ notice }}
    </v-snackbar>

    <v-snackbar v-model="errorOpen" color="error" timeout="4800" location="top right" @update:model-value="!$event && store.clearError()">
      {{ error }}
    </v-snackbar>
  </v-app>
</template>
