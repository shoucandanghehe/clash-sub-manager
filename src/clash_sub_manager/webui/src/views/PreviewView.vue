<script setup lang="ts">
import { storeToRefs } from 'pinia'
import { computed, ref, watch } from 'vue'

import { useManagerStore } from '../stores/manager'

type ConvertMode = 'content' | 'url'

const store = useManagerStore()
const {
  busy,
  convertPreview,
  mergePreview,
  mergeProfilePreview,
  mergeProfilePreviewName,
  subscriptions,
  templates,
} = storeToRefs(store)

const convertMode = ref<ConvertMode>('content')
const convertValue = ref('trojan://secret@example.com:443#Demo')
const selectedTemplateId = ref<number | null>(null)

const enabledSubscriptionCount = computed(() => {
  return subscriptions.value.filter((subscription) => subscription.enabled).length
})

watch(
  templates,
  (items) => {
    if (items.length === 0) {
      selectedTemplateId.value = null
      return
    }

    const stillExists = items.some((template) => template.id === selectedTemplateId.value)
    if (!stillExists) {
      selectedTemplateId.value = items.find((template) => template.is_default)?.id ?? items[0].id
    }
  },
  { immediate: true },
)

async function generateConvertPreview(): Promise<void> {
  if (!convertValue.value.trim()) {
    return
  }

  const payload = convertMode.value === 'content'
    ? { content: convertValue.value.trim() }
    : { url: convertValue.value.trim() }
  await store.runConvertPreview(payload)
}

async function generateMergePreview(): Promise<void> {
  await store.runMergePreview(selectedTemplateId.value)
}
</script>

<template>
  <v-row>
    <v-col cols="12" xl="4">
      <v-card class="fill-height">
        <v-card-item>
          <v-card-title class="px-0">转换预览</v-card-title>
          <v-card-subtitle class="px-0">快速检查单条订阅或分享链接的 Clash 输出。</v-card-subtitle>
        </v-card-item>
        <v-card-text>
          <div class="d-flex flex-column ga-4">
            <v-btn-toggle v-model="convertMode" color="primary" mandatory>
              <v-btn value="content">内容</v-btn>
              <v-btn value="url">链接</v-btn>
            </v-btn-toggle>
            <v-textarea
              v-model="convertValue"
              :label="convertMode === 'content' ? '分享链接或内联内容' : '订阅链接'"
              rows="8"
            />
            <v-btn color="primary" :disabled="busy || !convertValue.trim()" @click="generateConvertPreview">生成转换预览</v-btn>
            <v-sheet class="preview-panel" color="surface-variant" rounded="xl">
              <pre>{{ convertPreview || '尚未生成转换预览。' }}</pre>
            </v-sheet>
          </div>
        </v-card-text>
      </v-card>
    </v-col>

    <v-col cols="12" xl="4">
      <v-card class="fill-height">
        <v-card-item>
          <v-card-title class="px-0">合并预览</v-card-title>
          <v-card-subtitle class="px-0">按当前启用订阅和指定模板生成临时结果。</v-card-subtitle>
        </v-card-item>
        <v-card-text>
          <div class="d-flex flex-column ga-4">
            <v-select
              v-model="selectedTemplateId"
              :items="templates"
              item-title="name"
              item-value="id"
              label="预览模板"
              clearable
            />
            <v-alert color="primary" density="comfortable" variant="tonal">
              已启用订阅：{{ enabledSubscriptionCount }} 条
            </v-alert>
            <v-btn color="primary" :disabled="busy || enabledSubscriptionCount === 0" @click="generateMergePreview">生成合并预览</v-btn>
            <v-sheet class="preview-panel" color="surface-variant" rounded="xl">
              <pre>{{ mergePreview || '尚未生成合并预览。' }}</pre>
            </v-sheet>
          </div>
        </v-card-text>
      </v-card>
    </v-col>

    <v-col cols="12" xl="4">
      <v-card class="fill-height">
        <v-card-item>
          <v-card-title class="px-0">合并配置生成结果</v-card-title>
          <v-card-subtitle class="px-0">{{ mergeProfilePreviewName || '从“合并配置”页面点击生成后会显示在这里。' }}</v-card-subtitle>
        </v-card-item>
        <v-card-text>
          <v-sheet class="preview-panel" color="surface-variant" rounded="xl">
            <pre>{{ mergeProfilePreview || '尚未生成合并配置预览。' }}</pre>
          </v-sheet>
        </v-card-text>
      </v-card>
    </v-col>
  </v-row>
</template>
