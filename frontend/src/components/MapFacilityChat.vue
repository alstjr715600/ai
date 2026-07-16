<script setup>
import { nextTick, ref } from 'vue'
import api from '../services/api'

const emit = defineEmits([
  'select-facility'
])

const isOpen = ref(false)
const inputMessage = ref('')
const loading = ref(false)
const messageContainer = ref(null)

const messages = ref([
  {
    role: 'assistant',
    content:
      '장소를 기준으로 가까운 시설을 찾아드릴게요.\n' +
      '예: 강남역 근처 어린이집 추천해줘'
  }
])

function toggleChat() {
  isOpen.value = !isOpen.value

  if (isOpen.value) {
    scrollToBottom()
  }
}

function closeChat() {
  isOpen.value = false
}

async function scrollToBottom() {
  await nextTick()

  if (!messageContainer.value) return

  messageContainer.value.scrollTop =
    messageContainer.value.scrollHeight
}

async function sendMessage() {
  const text = inputMessage.value.trim()

  if (!text || loading.value) return

  messages.value.push({
    role: 'user',
    content: text
  })

  inputMessage.value = ''
  loading.value = true

  await scrollToBottom()

  try {
    const { data } = await api.post(
      '/chat/nearby',
      {
        message: text,
        limit: 3
      }
    )

    messages.value.push({
      role: 'assistant',
      content: data.reply,
      items: data.items ?? []
    })
  } catch (error) {
    console.error(error)

    messages.value.push({
      role: 'assistant',
      content:
        '시설 정보를 불러오지 못했어요. ' +
        '백엔드 서버와 카카오 REST API 키를 확인해주세요.'
    })
  } finally {
    loading.value = false
    await scrollToBottom()
  }
}

function handleEnter(event) {
  if (event.isComposing) return
  if (event.shiftKey) return

  event.preventDefault()
  sendMessage()
}

function selectFacility(item) {
  emit('select-facility', item)
}
</script>

<template>
  <div class="map-chat-wrapper">
    <button
      type="button"
      class="chat-floating-button"
      aria-label="주변 시설 챗봇 열기"
      @click="toggleChat"
    >
      <span v-if="!isOpen">💬</span>
      <span v-else>×</span>
    </button>

    <Transition name="chat-slide">
      <aside
        v-if="isOpen"
        class="chat-panel"
      >
        <header class="chat-header">
          <div>
            <strong>주변 시설 찾기</strong>
            <p>장소 기준 가까운 시설 추천</p>
          </div>

          <button
            type="button"
            class="chat-close-button"
            @click="closeChat"
          >
            ×
          </button>
        </header>

        <div
          ref="messageContainer"
          class="chat-messages"
        >
          <article
            v-for="(message, index) in messages"
            :key="index"
            :class="[
              'chat-message',
              message.role
            ]"
          >
            <div class="message-bubble">
              {{ message.content }}
            </div>

            <div
              v-if="message.items?.length"
              class="facility-result-list"
            >
              <button
                v-for="item in message.items"
                :key="item.id"
                type="button"
                class="facility-result-card"
                @click="selectFacility(item)"
              >
                <strong>{{ item.name }}</strong>

                <span class="meta">
                  {{ item.distance_km }}km · {{ item.district }}
                </span>

                <span class="address">{{ item.address }}</span>

                <span v-if="item.phone" class="phone">
                  📞 {{ item.phone }}
                </span>
              </button>
            </div>
          </article>

          <div
            v-if="loading"
            class="chat-loading"
          >
            <span class="loading-dots">가까운 시설을 찾는 중이에요...</span>
          </div>
        </div>

        <form
          class="chat-input-area"
          @submit.prevent="sendMessage"
        >
          <textarea
            v-model="inputMessage"
            rows="1"
            maxlength="500"
            placeholder="예: 서울역 근처 소아과 추천해줘"
            @keydown.enter="handleEnter"
          />

          <button
            type="submit"
            :disabled="
              loading || !inputMessage.trim()
            "
          >
            전송
          </button>
        </form>
      </aside>
    </Transition>
  </div>
</template>

<style scoped>
.map-chat-wrapper {
  position: fixed;
  right: 28px;
  bottom: 28px;
  z-index: 900;
}

.chat-floating-button {
  position: absolute;
  right: 0;
  bottom: 0;
  width: 60px;
  height: 60px;
  padding: 0;
  border: 0;
  border-radius: var(--radius-pill);
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-dark) 100%);
  color: #fff;
  box-shadow: var(--shadow-md);
  font-size: 24px;
  cursor: pointer;
  display: grid;
  place-items: center;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.chat-floating-button:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
}

.chat-panel {
  position: absolute;
  right: 0;
  bottom: 76px;
  width: 400px;
  height: min(640px, calc(100vh - 130px));
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  background: var(--color-surface);
  box-shadow: var(--shadow-lg);
}

.chat-header {
  padding: 18px 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--color-border);
  background: var(--color-surface);
}

.chat-header strong {
  display: block;
  font-size: 16px;
  color: var(--color-ink);
  font-weight: 800;
}

.chat-header p {
  margin: 3px 0 0;
  color: var(--color-ink-soft);
  font-size: 12px;
}

.chat-close-button {
  width: 32px;
  height: 32px;
  padding: 0;
  border: 0;
  border-radius: var(--radius-pill);
  background: var(--color-bg);
  color: var(--color-ink-soft);
  font-size: 20px;
  line-height: 1;
  cursor: pointer;
  display: grid;
  place-items: center;
  transition: background 0.15s ease;
}

.chat-close-button:hover {
  background: var(--color-primary-soft);
  color: var(--color-primary-dark);
}

.chat-messages {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  background: var(--color-bg);
}

.chat-message {
  margin-bottom: 16px;
  display: flex;
  flex-direction: column;
}

.chat-message.user {
  align-items: flex-end;
}

.chat-message.assistant {
  align-items: flex-start;
}

.message-bubble {
  max-width: 85%;
  padding: 12px 16px;
  border-radius: var(--radius-md);
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 14px;
  line-height: 1.55;
  box-shadow: var(--shadow-sm);
}

.chat-message.user .message-bubble {
  border-bottom-right-radius: 4px;
  background: var(--color-primary);
  color: #fff;
  border: none;
}

.chat-message.assistant .message-bubble {
  border: 1px solid var(--color-border);
  border-bottom-left-radius: 4px;
  background: var(--color-surface);
  color: var(--color-ink);
}

.facility-result-list {
  width: 100%;
  margin-top: 10px;
  display: grid;
  gap: 10px;
}

.facility-result-card {
  width: 100%;
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  text-align: left;
  cursor: pointer;
  transition: border-color 0.15s ease, transform 0.15s ease, box-shadow 0.15s ease;
}

.facility-result-card:hover {
  border-color: var(--color-primary);
  transform: translateY(-2px);
  box-shadow: var(--shadow-sm);
}

.facility-result-card strong {
  font-size: 14px;
  color: var(--color-ink);
}

.facility-result-card .meta {
  color: var(--color-primary-dark);
  font-size: 12px;
  font-weight: 700;
}

.facility-result-card .address,
.facility-result-card .phone {
  color: var(--color-ink-soft);
  font-size: 12px;
  line-height: 1.4;
}

.chat-loading {
  color: var(--color-ink-soft);
  font-size: 13px;
  padding: 8px 12px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  width: fit-content;
}

.chat-input-area {
  padding: 14px;
  display: flex;
  align-items: flex-end;
  gap: 8px;
  border-top: 1px solid var(--color-border);
  background: var(--color-surface);
}

.chat-input-area textarea {
  flex: 1;
  min-height: 42px;
  max-height: 100px;
  padding: 10px 14px;
  resize: none;
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-md);
  font: inherit;
  font-size: 14px;
  line-height: 1.4;
}

.chat-input-area button {
  height: 42px;
  padding: 0 18px;
  border: 0;
  border-radius: var(--radius-pill);
  background: var(--color-primary);
  color: #fff;
  font-weight: 700;
  cursor: pointer;
  transition: background 0.15s ease;
}

.chat-input-area button:hover:not(:disabled) {
  background: var(--color-primary-dark);
}

.chat-input-area button:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.chat-slide-enter-active,
.chat-slide-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.chat-slide-enter-from,
.chat-slide-leave-to {
  opacity: 0;
  transform: translateY(15px);
}

@media (max-width: 600px) {
  .map-chat-wrapper {
    right: 16px;
    bottom: 16px;
  }

  .chat-panel {
    position: fixed;
    inset: 70px 16px 84px;
    width: auto;
    height: auto;
  }

  .chat-floating-button {
    width: 54px;
    height: 54px;
  }
}
</style>