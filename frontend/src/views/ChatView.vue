<script setup>
import { nextTick, ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '../services/api'
import { saveProfile } from '../utils/profile'

const router = useRouter()
const input = ref('')
const loading = ref(false)
const messageList = ref(null)
const profile = ref({ child_age: null, selected_categories: [], top_priority: null })
const messages = ref([{ role: 'assistant', content: '안녕하세요. 아이와 살기 좋은 서울 자치구를 찾아드릴게요. 아이의 나이를 알려주세요.' }])

const quickReplies = ['3살 아이 키우고 있어요', '어린이집이 가까웠으면 좋겠어요', '공원이 많은 동네가 좋아요']

async function sendMessage(presetText) {
  const text = (presetText ?? input.value).trim()
  if (!text || loading.value) return
  const history = messages.value.map(item => ({ role: item.role, content: item.content }))
  messages.value.push({ role: 'user', content: text })
  input.value = ''
  loading.value = true
  await scrollBottom()
  try {
    const { data } = await api.post('/chat/message', { message: text, history })
    messages.value.push({ role: 'assistant', content: data.reply })
    if (data.extracted_profile) profile.value = { ...profile.value, ...data.extracted_profile }
  } catch (error) {
    messages.value.push({ role: 'assistant', content: error.response?.data?.detail ?? '챗봇 응답을 불러오지 못했습니다.' })
  } finally {
    loading.value = false
    await scrollBottom()
  }
}

function saveRecommendationProfile() {
  const categories = profile.value.selected_categories ?? []
  saveProfile({
    child_age: profile.value.child_age ?? 3,
    priorities: categories.map(category => ({ category, weight: category === profile.value.top_priority ? 5 : 3 })),
    recommendation_count: 3
  })
}

function openRecommendations() {
  saveRecommendationProfile()
  router.push('/map')
}

async function scrollBottom() {
  await nextTick()
  if (messageList.value) messageList.value.scrollTop = messageList.value.scrollHeight
}
</script>

<template>
  <div class="chat-page">
    <section class="chat-panel">
      <header><h1>LocalHub</h1><p class="subtext">영유아와 살기 좋은 서울 자치구 찾기</p></header>
      <div ref="messageList" class="message-list">
        <div v-for="(message, index) in messages" :key="index" class="message" :class="message.role">{{ message.content }}</div>
        <div v-if="loading" class="message assistant">답변을 작성하고 있어요...</div>
      </div>
      <div v-if="messages.length <= 1" class="quick-chip-row">
        <button
          v-for="reply in quickReplies"
          :key="reply"
          type="button"
          class="quick-chip"
          :disabled="loading"
          @click="sendMessage(reply)"
        >
          {{ reply }}
        </button>
      </div>
      <form class="chat-input-row" @submit.prevent="sendMessage()">
        <input v-model="input" maxlength="500" placeholder="메시지를 입력해주세요." :disabled="loading" />
        <button type="submit" :disabled="loading || !input.trim()">전송</button>
      </form>
      <button v-if="profile.child_age !== null && profile.selected_categories.length >= 2 && profile.top_priority" class="recommend-button" @click="openRecommendations">추천 결과 확인하기</button>
    </section>
  </div>
</template>
