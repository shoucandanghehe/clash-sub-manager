<script setup lang="ts">
import { storeToRefs } from 'pinia'
import { computed, reactive, ref } from 'vue'

import type { SubscriptionPayload, SubscriptionRecord } from '../api'
import { useManagerStore } from '../stores/manager'

type SourceMode = 'content' | 'url'

interface HeaderRow {
  id: number
  name: string
  value: string
}

interface SubscriptionForm {
  name: string
  source: string
  proxy: string
  followRedirects: boolean
  enabled: boolean
  headers: HeaderRow[]
}

const store = useManagerStore()
const { busy, subscriptions } = storeToRefs(store)

const dialog = ref(false)
const editingId = ref<number | null>(null)
const sourceMode = ref<SourceMode>('content')
const nextHeaderRowId = ref(0)

const form = reactive<SubscriptionForm>({
  name: '',
  source: '',
  proxy: '',
  followRedirects: true,
  enabled: true,
  headers: [],
})

const headers = [
  { title: '名称', key: 'name' },
  { title: '来源', key: 'source' },
  { title: '状态', key: 'status', sortable: false },
  { title: '操作', key: 'actions', sortable: false, align: 'end' },
] as const

const sourceLabel = computed(() => {
  return sourceMode.value === 'content' ? '内联内容或分享链接' : '订阅 URL'
})

const dialogTitle = computed(() => {
  return editingId.value === null ? '新建订阅' : '编辑订阅'
})

const normalizedHeaders = computed(() => {
  const values: Record<string, string> = {}
  const seenNames = new Set<string>()

  for (const row of form.headers) {
    const name = row.name.trim()
    const value = row.value.trim()

    if (!name && !value) {
      continue
    }
    if (!name || !value) {
      return {
        valid: false,
        message: '每个自定义 Header 都必须同时填写名称和值。',
        values: {} as Record<string, string>,
      }
    }

    const normalizedName = name.toLowerCase()
    if (seenNames.has(normalizedName)) {
      return {
        valid: false,
        message: 'Header 名称不能重复。',
        values: {} as Record<string, string>,
      }
    }

    seenNames.add(normalizedName)
    values[name] = value
  }

  return {
    valid: true,
    message: '',
    values,
  }
})

const canSubmit = computed(() => {
  return form.name.trim().length > 0 && form.source.trim().length > 0 && normalizedHeaders.value.valid
})

function createHeaderRow(name = '', value = ''): HeaderRow {
  nextHeaderRowId.value += 1
  return {
    id: nextHeaderRowId.value,
    name,
    value,
  }
}

function resetForm(): void {
  editingId.value = null
  sourceMode.value = 'content'
  form.name = ''
  form.source = ''
  form.proxy = ''
  form.followRedirects = true
  form.enabled = true
  form.headers = []
}

function addHeaderRow(): void {
  form.headers = [...form.headers, createHeaderRow()]
}

function removeHeaderRow(id: number): void {
  form.headers = form.headers.filter((row) => row.id !== id)
}

function openCreateDialog(): void {
  resetForm()
  dialog.value = true
}

function openEditDialog(subscription: SubscriptionRecord): void {
  editingId.value = subscription.id
  sourceMode.value = subscription.url ? 'url' : 'content'
  form.name = subscription.name
  form.source = subscription.url ?? subscription.content ?? ''
  form.proxy = subscription.proxy ?? ''
  form.followRedirects = subscription.follow_redirects
  form.enabled = subscription.enabled
  form.headers = Object.entries(subscription.headers).map(([name, value]) => createHeaderRow(name, value))
  dialog.value = true
}

async function saveSubscription(): Promise<void> {
  const payload: SubscriptionPayload = {
    name: form.name.trim(),
    proxy: form.proxy.trim() ? form.proxy.trim() : null,
    headers: normalizedHeaders.value.values,
    follow_redirects: form.followRedirects,
    enabled: form.enabled,
  }

  if (sourceMode.value === 'content') {
    payload.content = form.source.trim()
  } else {
    payload.url = form.source.trim()
  }

  const succeeded = editingId.value === null
    ? await store.createSubscription(payload)
    : await store.updateSubscription(editingId.value, payload)

  if (succeeded) {
    dialog.value = false
    resetForm()
  }
}
</script>

<template>
  <v-card>
    <v-card-item>
      <div class="d-flex flex-column flex-sm-row ga-4 align-sm-center justify-space-between">
        <div>
          <v-card-title class="px-0">订阅管理</v-card-title>
          <v-card-subtitle class="px-0">名称唯一，支持远程 URL 或内联内容。</v-card-subtitle>
        </div>
        <v-btn color="primary" prepend-icon="mdi-plus" @click="openCreateDialog">新建订阅</v-btn>
      </div>
    </v-card-item>

    <v-data-table :headers="headers" :items="subscriptions" item-value="id">
      <template #item.source="{ item }">
        <div class="d-flex flex-column py-2">
          <span class="font-weight-medium">{{ item.url ? '远程订阅' : '内联内容' }}</span>
          <span class="text-caption text-medium-emphasis text-break">{{ item.url ?? '已保存到数据库' }}</span>
        </div>
      </template>

      <template #item.status="{ item }">
        <div class="d-flex align-center ga-3 py-2">
          <v-switch
            :model-value="item.enabled"
            color="primary"
            hide-details
            inset
            @update:model-value="store.toggleSubscription(item.id, Boolean($event))"
          />
          <v-chip :color="item.enabled ? 'primary' : 'default'" size="small" variant="tonal">
            {{ item.enabled ? '启用' : '停用' }}
          </v-chip>
        </div>
      </template>

      <template #item.actions="{ item }">
        <div class="d-flex justify-end ga-2 py-2">
          <v-btn icon="mdi-pencil" size="small" variant="text" @click="openEditDialog(item)" />
          <v-btn icon="mdi-delete-outline" size="small" variant="text" color="error" @click="store.deleteSubscription(item.id)" />
        </div>
      </template>
    </v-data-table>
  </v-card>

  <v-dialog v-model="dialog">
    <v-card>
      <v-card-item>
        <v-card-title>{{ dialogTitle }}</v-card-title>
        <v-card-subtitle>订阅名称会作为唯一标识展示给其他功能使用。</v-card-subtitle>
      </v-card-item>

      <v-card-text>
        <v-row>
          <v-col cols="12">
            <v-text-field v-model="form.name" label="名称" maxlength="255" />
          </v-col>
          <v-col cols="12">
            <v-btn-toggle v-model="sourceMode" color="primary" mandatory>
              <v-btn value="content">内联内容</v-btn>
              <v-btn value="url">远程 URL</v-btn>
            </v-btn-toggle>
          </v-col>
          <v-col cols="12">
            <v-textarea v-model="form.source" :label="sourceLabel" rows="8" />
          </v-col>
          <v-col cols="12" md="6">
            <v-text-field v-model="form.proxy" label="代理 URL（可选）" placeholder="http://127.0.0.1:7890" />
          </v-col>
          <v-col cols="12" md="3">
            <v-switch v-model="form.followRedirects" label="跟随重定向" hide-details />
          </v-col>
          <v-col cols="12" md="3">
            <v-switch v-model="form.enabled" label="启用" hide-details />
          </v-col>
          <v-col cols="12">
            <div class="d-flex align-center justify-space-between mb-3">
              <div>
                <div class="text-subtitle-1 font-weight-medium">自定义 Header</div>
                <div class="text-body-2 text-medium-emphasis">用于远程订阅请求，例如 Authorization、User-Agent。</div>
              </div>
              <v-btn prepend-icon="mdi-plus" variant="text" @click="addHeaderRow">添加 Header</v-btn>
            </div>

            <v-alert
              v-if="normalizedHeaders.message"
              color="error"
              density="comfortable"
              variant="tonal"
              class="mb-3"
            >
              {{ normalizedHeaders.message }}
            </v-alert>

            <div v-if="form.headers.length === 0" class="text-body-2 text-medium-emphasis py-2">
              当前未设置自定义 Header。
            </div>

            <v-row v-for="row in form.headers" :key="row.id" class="align-center">
              <v-col cols="12" md="5">
                <v-text-field v-model="row.name" label="Header 名称" placeholder="Authorization" />
              </v-col>
              <v-col cols="12" md="6">
                <v-text-field v-model="row.value" label="Header 值" placeholder="Bearer ..." />
              </v-col>
              <v-col cols="12" md="1" class="d-flex justify-end">
                <v-btn icon="mdi-delete-outline" size="small" variant="text" color="error" @click="removeHeaderRow(row.id)" />
              </v-col>
            </v-row>
          </v-col>
        </v-row>
      </v-card-text>

      <v-card-actions>
        <v-spacer />
        <v-btn variant="text" @click="dialog = false">取消</v-btn>
        <v-btn color="primary" :disabled="busy || !canSubmit" @click="saveSubscription">保存</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>
