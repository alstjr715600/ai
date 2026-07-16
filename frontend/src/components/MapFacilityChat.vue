<script setup>
import { nextTick, onBeforeUnmount, ref } from 'vue'
import api from '../services/api'

const emit = defineEmits([
  'select-facility'
])

const isOpen = ref(false)
const inputMessage = ref('')
const loading = ref(false)
const messageContainer = ref(null)

const selectedFacility = ref(null)
const showDetailModal = ref(false)
const mapContainer = ref(null)
const mapError = ref('')

let detailMap = null
let detailMarker = null
let kakaoScriptPromise = null

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

function getLatitude(item) {
  const value =
    item.latitude ??
    item.lat ??
    item.y

  return Number(value)
}

function getLongitude(item) {
  const value =
    item.longitude ??
    item.lng ??
    item.lon ??
    item.x

  return Number(value)
}

async function selectFacility(item) {
  selectedFacility.value = item
  showDetailModal.value = true
  mapError.value = ''

  emit('select-facility', item)

  await nextTick()
  await showKakaoMap(item)
}

function closeDetailModal() {
  showDetailModal.value = false
  selectedFacility.value = null
  mapError.value = ''

  if (detailMarker) {
    detailMarker.setMap(null)
    detailMarker = null
  }

  detailMap = null
}

function loadKakaoMapScript() {
  if (window.kakao?.maps) {
    return Promise.resolve()
  }

  if (kakaoScriptPromise) {
    return kakaoScriptPromise
  }

  kakaoScriptPromise = new Promise((resolve, reject) => {
    const existingScript = document.querySelector(
      'script[data-kakao-map-sdk="true"]'
    )

    if (existingScript) {
      existingScript.addEventListener('load', () => {
        window.kakao.maps.load(resolve)
      })

      existingScript.addEventListener('error', reject)
      return
    }

    const kakaoKey = import.meta.env.VITE_KAKAO_MAP_KEY

    if (!kakaoKey) {
      reject(
        new Error(
          'VITE_KAKAO_MAP_KEY가 설정되어 있지 않습니다.'
        )
      )
      return
    }

    const script = document.createElement('script')

    script.dataset.kakaoMapSdk = 'true'
    script.async = true
    script.src =
      `https://dapi.kakao.com/v2/maps/sdk.js?appkey=${kakaoKey}&autoload=false`

    script.onload = () => {
      window.kakao.maps.load(resolve)
    }

    script.onerror = () => {
      reject(
        new Error(
          '카카오 지도 SDK를 불러오지 못했습니다.'
        )
      )
    }

    document.head.appendChild(script)
  })

  return kakaoScriptPromise
}

async function showKakaoMap(item) {
  const latitude = getLatitude(item)
  const longitude = getLongitude(item)

  if (
    !Number.isFinite(latitude) ||
    !Number.isFinite(longitude)
  ) {
    mapError.value =
      '이 시설의 위도와 경도 정보가 없습니다.'
    return
  }

  try {
    await loadKakaoMapScript()
    await nextTick()

    if (!mapContainer.value) return

    const position =
      new window.kakao.maps.LatLng(
        latitude,
        longitude
      )

    detailMap = new window.kakao.maps.Map(
      mapContainer.value,
      {
        center: position,
        level: 3
      }
    )

    detailMarker = new window.kakao.maps.Marker({
      position
    })

    detailMarker.setMap(detailMap)

    const infoWindow =
      new window.kakao.maps.InfoWindow({
        content: `
          <div style="
            min-width:150px;
            padding:8px 12px;
            font-size:13px;
            text-align:center;
            color:#222;
          ">
            ${escapeHtml(item.name)}
          </div>
        `
      })

    infoWindow.open(detailMap, detailMarker)

    setTimeout(() => {
      detailMap.relayout()
      detailMap.setCenter(position)
    }, 100)
  } catch (error) {
    console.error('카카오 지도 오류:', error)

    mapError.value =
      error.message ??
      '카카오 지도를 표시하지 못했습니다.'
  }
}

function escapeHtml(text) {
  return String(text ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;')
}

function openKakaoMap() {
  if (!selectedFacility.value) return

  const item = selectedFacility.value
  const latitude = getLatitude(item)
  const longitude = getLongitude(item)

  let url

  if (
    Number.isFinite(latitude) &&
    Number.isFinite(longitude)
  ) {
    url =
      `https://map.kakao.com/link/map/` +
      `${encodeURIComponent(item.name)},` +
      `${latitude},${longitude}`
  } else {
    url =
      `https://map.kakao.com/?q=` +
      encodeURIComponent(
        item.address || item.name
      )
  }

  window.open(url, '_blank', 'noopener,noreferrer')
}

function callFacility() {
  const phone = selectedFacility.value?.phone

  if (!phone) return

  window.location.href =
    `tel:${phone.replace(/[^0-9+]/g, '')}`
}

onBeforeUnmount(() => {
  if (detailMarker) {
    detailMarker.setMap(null)
  }

  detailMarker = null
  detailMap = null
})
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
                  {{ item.distance_km }}km ·
                  {{ item.district }}
                </span>

                <span class="address">
                  {{ item.address }}
                </span>

                <span
                  v-if="item.phone"
                  class="phone"
                >
                  📞 {{ item.phone }}
                </span>

                <span class="detail-guide">
                  눌러서 상세 위치 확인하기
                </span>
              </button>
            </div>
          </article>

          <div
            v-if="loading"
            class="chat-loading"
          >
            가까운 시설을 찾는 중이에요...
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

    <Teleport to="body">
      <Transition name="modal-fade">
        <div
          v-if="showDetailModal && selectedFacility"
          class="facility-modal-overlay"
          @click.self="closeDetailModal"
        >
          <section class="facility-modal">
            <header class="facility-modal-header">
              <div>
                <p class="facility-type">
                  {{ selectedFacility.facility_type || '시설 상세' }}
                </p>

                <h2>
                  {{ selectedFacility.name }}
                </h2>
              </div>

              <button
                type="button"
                class="facility-modal-close"
                aria-label="상세 창 닫기"
                @click="closeDetailModal"
              >
                ×
              </button>
            </header>

            <div class="facility-detail-info">
              <div class="detail-row">
                <span class="detail-label">주소</span>
                <span>
                  {{ selectedFacility.address || '정보 없음' }}
                </span>
              </div>

              <div class="detail-row">
                <span class="detail-label">자치구</span>
                <span>
                  {{ selectedFacility.district || '정보 없음' }}
                </span>
              </div>

              <div class="detail-row">
                <span class="detail-label">거리</span>
                <span>
                  {{
                    selectedFacility.distance_km != null
                      ? `${selectedFacility.distance_km}km`
                      : '정보 없음'
                  }}
                </span>
              </div>

              <div class="detail-row">
                <span class="detail-label">전화번호</span>
                <span>
                  {{ selectedFacility.phone || '정보 없음' }}
                </span>
              </div>
            </div>

            <div class="facility-map-area">
              <div
                v-show="!mapError"
                ref="mapContainer"
                class="facility-map"
              />

              <div
                v-if="mapError"
                class="map-error"
              >
                <p>{{ mapError }}</p>

                <button
                  type="button"
                  @click="openKakaoMap"
                >
                  카카오맵에서 검색하기
                </button>
              </div>
            </div>

            <div class="facility-modal-actions">
              <button
                v-if="selectedFacility.phone"
                type="button"
                class="call-button"
                @click="callFacility"
              >
                전화하기
              </button>

              <button
                type="button"
                class="kakao-map-button"
                @click="openKakaoMap"
              >
                카카오맵 크게 보기
              </button>
            </div>
          </section>
        </div>
      </Transition>
    </Teleport>
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
  background: linear-gradient(
    135deg,
    var(--color-primary) 0%,
    var(--color-primary-dark) 100%
  );
  color: #fff;
  box-shadow: var(--shadow-md);
  font-size: 24px;
  cursor: pointer;
  display: grid;
  place-items: center;
  transition:
    transform 0.2s ease,
    box-shadow 0.2s ease;
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
  transition:
    border-color 0.15s ease,
    transform 0.15s ease,
    box-shadow 0.15s ease;
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

.detail-guide {
  margin-top: 6px;
  color: var(--color-primary-dark);
  font-size: 11px;
  font-weight: 700;
}

.chat-loading {
  padding: 8px 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  color: var(--color-ink-soft);
  font-size: 13px;
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
}

.chat-input-area button:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.facility-modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 2000;
  padding: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.48);
}

.facility-modal {
  width: min(620px, 100%);
  max-height: calc(100vh - 40px);
  overflow-y: auto;
  border-radius: 20px;
  background: #fff;
  box-shadow: 0 24px 70px rgba(0, 0, 0, 0.25);
}

.facility-modal-header {
  padding: 22px 24px 16px;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  border-bottom: 1px solid #ececec;
}

.facility-type {
  margin: 0 0 5px;
  color: #777;
  font-size: 12px;
}

.facility-modal-header h2 {
  margin: 0;
  color: #222;
  font-size: 22px;
}

.facility-modal-close {
  width: 36px;
  height: 36px;
  padding: 0;
  border: 0;
  border-radius: 50%;
  background: #f3f3f3;
  color: #333;
  font-size: 24px;
  cursor: pointer;
}

.facility-detail-info {
  padding: 18px 24px;
  display: grid;
  gap: 12px;
}

.detail-row {
  display: grid;
  grid-template-columns: 80px 1fr;
  gap: 12px;
  color: #333;
  font-size: 14px;
}

.detail-label {
  color: #777;
  font-weight: 700;
}

.facility-map-area {
  padding: 0 24px;
}

.facility-map {
  width: 100%;
  height: 320px;
  border-radius: 14px;
  overflow: hidden;
  background: #eeeeee;
}

.map-error {
  min-height: 240px;
  padding: 30px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border-radius: 14px;
  background: #f5f5f5;
  color: #666;
  text-align: center;
}

.map-error button {
  margin-top: 12px;
  padding: 10px 16px;
  border: 0;
  border-radius: 10px;
  background: #fee500;
  color: #191919;
  font-weight: 700;
  cursor: pointer;
}

.facility-modal-actions {
  padding: 18px 24px 24px;
  display: flex;
  gap: 10px;
}

.facility-modal-actions button {
  flex: 1;
  height: 46px;
  border: 0;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 800;
  cursor: pointer;
}

.call-button {
  background: #f0f0f0;
  color: #333;
}

.kakao-map-button {
  background: #fee500;
  color: #191919;
}

.chat-slide-enter-active,
.chat-slide-leave-active,
.modal-fade-enter-active,
.modal-fade-leave-active {
  transition:
    opacity 0.2s ease,
    transform 0.2s ease;
}

.chat-slide-enter-from,
.chat-slide-leave-to {
  opacity: 0;
  transform: translateY(15px);
}

.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
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

  .facility-modal-overlay {
    padding: 12px;
  }

  .facility-modal-header {
    padding: 18px;
  }

  .facility-detail-info {
    padding: 16px 18px;
  }

  .facility-map-area {
    padding: 0 18px;
  }

  .facility-map {
    height: 260px;
  }

  .facility-modal-actions {
    padding: 16px 18px 20px;
    flex-direction: column;
  }
}
</style>