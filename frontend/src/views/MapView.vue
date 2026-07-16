<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import SeoulDistrictMap from '../components/SeoulDistrictMap.vue'
import MapFacilityChat from '../components/MapFacilityChat.vue'
import api from '../services/api'
import { getProfile } from '../utils/profile'

const districts = ref([])
const selectedDistrict = ref(null)
const loading = ref(true)
const errorMessage = ref('')
const popupOpen = ref(false)

const categoryLabels = {
  CHILDCARE: '어린이집',
  PARK: '공원·놀이터',
  MEDICAL: '병원·소아과',
  SAFETY: '안전',
  AIR: '대기환경',
  SCHOOL: '초등학교',
  CULTURE: '문화센터'
}
const sequentialPalette = ['#EAF4EC', '#BFE0C6', '#7EC28E', '#3D9463', '#1F5B43']

const scoreThresholds = computed(() => {
  const scores = districts.value.map((d) => d.total_score).sort((a, b) => a - b)
  const n = scores.length
  if (n === 0) return [0, 0, 0, 0]
  return [1, 2, 3, 4].map((i) => scores[Math.min(n - 1, Math.floor((n * i) / 5))])
})

function getScoreColor(score) {
  const [q1, q2, q3, q4] = scoreThresholds.value
  if (score >= q4) return sequentialPalette[4]
  if (score >= q3) return sequentialPalette[3]
  if (score >= q2) return sequentialPalette[2]
  if (score >= q1) return sequentialPalette[1]
  return sequentialPalette[0]
}

const scoreLegend = computed(() => {
  const [q1, q2, q3, q4] = scoreThresholds.value
  return [
    { label: `상위 20% (${q4}점 이상)`, color: sequentialPalette[4] },
    { label: `중상위 20% (${q3}~${q4}점)`, color: sequentialPalette[3] },
    { label: `중위 20% (${q2}~${q3}점)`, color: sequentialPalette[2] },
    { label: `중하위 20% (${q1}~${q2}점)`, color: sequentialPalette[1] },
    { label: `하위 20% (${q1}점 미만)`, color: sequentialPalette[0] }
  ]
})

const districtsWithColor = computed(() =>
  districts.value.map((d) => ({
    ...d,
    color: getScoreColor(d.total_score)
  }))
)

const averageScore = computed(() => {
  if (!districts.value.length) return '-'
  const sum = districts.value.reduce((acc, d) => acc + d.total_score, 0)
  return (sum / districts.value.length).toFixed(1)
})

const topDistrict = computed(() => {
  if (!districts.value.length) return null
  return [...districts.value].sort((a, b) => b.total_score - a.total_score)[0]
})

const selectedReasons = computed(() => selectedDistrict.value?.reasons ?? [])
const selectedCategoryScores = computed(() => {
  const scores = selectedDistrict.value?.category_scores ?? {}
  return Object.entries(scores).map(([category, score]) => ({
    category,
    label: categoryLabels[category] ?? category,
    score
  }))
})

onMounted(() => {
  loadScores()
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
  document.body.style.overflow = ''
})

async function loadScores() {
  loading.value = true
  errorMessage.value = ''
  try {
    const profile = getProfile()
    const { data } = await api.post('/districts/scores', profile)
    districts.value = data
  } catch (error) {
    console.error(error)
    errorMessage.value = '점수 데이터를 불러오지 못했습니다. FastAPI 서버를 확인해주세요.'
  } finally {
    loading.value = false
  }
}

function openDistrictPopup(district) {
  selectedDistrict.value = district
  popupOpen.value = true
  document.body.style.overflow = 'hidden'
}

function closePopup() {
  popupOpen.value = false
  document.body.style.overflow = ''
}

function handleBackdropClick(event) {
  if (event.target === event.currentTarget) closePopup()
}

function handleKeydown(event) {
  if (event.key === 'Escape' && popupOpen.value) closePopup()
}

function handleSelectFacility(item) {
  console.log('선택된 시설:', item)
}
</script>

<template>
  <section class="page-container">
    <header class="hero-band">
      <div class="hero-top">
        <div>
          <span class="hero-eyebrow">챗봇 추천 결과</span>
          <h1>서울특별시 자치구 육아환경 점수</h1>
          <p>챗봇에서 선택한 조건에 맞춰 계산된 개인화 점수입니다. 자치구를 클릭하면 세부 근거를 볼 수 있어요.</p>
        </div>
      </div>

      <div class="stat-chip-row">
        <div class="stat-chip">
          <span class="stat-label">평균 점수</span>
          <span class="stat-value">{{ averageScore }}점</span>
        </div>
        <div class="stat-chip" v-if="topDistrict">
          <span class="stat-label">최고 점수 자치구</span>
          <span class="stat-value">{{ topDistrict.district_name }} · {{ topDistrict.total_score }}점</span>
        </div>
        <div class="stat-chip">
          <span class="stat-label">비교 대상</span>
          <span class="stat-value">서울 25개 자치구</span>
        </div>
      </div>
    </header>

    <div class="notice">현재 점수와 판단 근거는 화면 구현용 목업 데이터입니다.</div>

    <p v-if="loading" class="status-message">점수를 불러오는 중입니다.</p>
    <p v-else-if="errorMessage" class="error-message">{{ errorMessage }}</p>

    <div v-else class="map-content">
      <aside class="legend-panel">
        <h2>점수 구간</h2>
        <ul>
          <li v-for="legend in scoreLegend" :key="legend.label">
            <span class="legend-color" :style="{ backgroundColor: legend.color }"></span>
            <span>{{ legend.label }}</span>
          </li>
        </ul>
        <p class="legend-description">
          서울 25개 구 안에서의 상대적 순위입니다. "하위 20%"는 부족하다는 뜻이 아니라
          다른 구 대비 상대적으로 시설이 덜 밀집되어 있다는 의미입니다.
        </p>
      </aside>

      <div class="map-area">
        <SeoulDistrictMap
          :districts="districtsWithColor"
          :selected-code="popupOpen ? selectedDistrict?.district_code : ''"
          @select="openDistrictPopup"
        />
      </div>
    </div>

    <MapFacilityChat @select-facility="handleSelectFacility" />

    <div v-if="popupOpen && selectedDistrict" class="popup-backdrop" @click="handleBackdropClick">
      <article class="district-popup" role="dialog" aria-modal="true">
        <button type="button" class="popup-close-button" @click="closePopup">×</button>

        <header class="popup-header">
          <h2>{{ selectedDistrict.district_name }}</h2>
          <div class="total-score-badge" :style="{ backgroundColor: getScoreColor(selectedDistrict.total_score) }">
            {{ selectedDistrict.total_score }}점
            <span>/ {{ selectedDistrict.rank }}위</span>
          </div>
          <p>입력한 조건을 기준으로 계산한 개인화 점수입니다.</p>
        </header>

        <section class="popup-section">
          <h3>항목별 점수</h3>
          <ul class="category-score-list">
            <li v-for="item in selectedCategoryScores" :key="item.category">
              <div class="score-title">
                <span>{{ item.label }}</span>
                <strong>{{ item.score }}점</strong>
              </div>
              <div class="score-progress">
                <div class="score-progress-value" :style="{ width: `${item.score}%`, backgroundColor: getScoreColor(item.score) }"></div>
              </div>
            </li>
          </ul>
        </section>

        <section class="popup-section">
          <h3>판단 근거</h3>
          <ul class="reason-list">
            <li v-for="reason in selectedReasons" :key="reason.category">
              <span class="reason-check">✓</span>
              <div>
                <strong>{{ reason.title }}</strong>
                <p>{{ reason.description }}</p>
              </div>
            </li>
          </ul>
        </section>

        <RouterLink to="/facilities" class="facility-link-button" @click="closePopup">시설 정보 조회하기</RouterLink>
      </article>
    </div>
  </section>
</template>

<style scoped>
.status-message,
.error-message {
  padding: 40px;
  text-align: center;
}

.error-message {
  color: var(--color-support);
  font-weight: 600;
}

.notice {
  margin-bottom: 24px;
}

.map-content {
  position: relative;
  min-height: 680px;
}

.map-area {
  width: 100%;
  padding: 28px 56px;
  border-radius: var(--radius-xl);
  background: var(--color-surface);
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--color-border);
}

.legend-panel {
  position: absolute;
  top: 24px;
  left: 24px;
  z-index: 5;
  width: 200px;
  padding: 20px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(8px);
  box-shadow: var(--shadow-md);
}

.legend-panel h2 {
  margin: 0 0 14px;
  font-size: 15px;
  color: var(--color-ink);
}

.legend-panel ul {
  margin: 0;
  padding: 0;
  list-style: none;
}

.legend-panel li {
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
  color: var(--color-ink);
}

.legend-color {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
  border-radius: 4px;
}

.legend-description {
  margin: 16px 0 0;
  color: var(--color-ink-soft);
  font-size: 12px;
  line-height: 1.5;
  border-top: 1px solid var(--color-border);
  padding-top: 12px;
}

.popup-backdrop {
  position: fixed;
  inset: 0;
  z-index: 1000;
  padding: 24px;
  display: grid;
  place-items: center;
  background: rgba(31, 41, 55, 0.45);
  backdrop-filter: blur(4px);
}

.district-popup {
  position: relative;
  width: min(560px, 100%);
  max-height: calc(100vh - 48px);
  padding: 32px;
  overflow-y: auto;
  border-radius: var(--radius-xl);
  background: var(--color-surface);
  box-shadow: var(--shadow-lg);
  border: 1px solid var(--color-border);
}

.popup-close-button {
  position: absolute;
  top: 20px;
  right: 20px;
  width: 36px;
  height: 36px;
  padding: 0;
  border: 0;
  border-radius: var(--radius-pill);
  background: var(--color-bg);
  color: var(--color-ink-soft);
  font-size: 22px;
  line-height: 1;
  display: grid;
  place-items: center;
  transition: background 0.15s ease;
}

.popup-close-button:hover {
  background: var(--color-primary-soft);
  color: var(--color-primary-dark);
}

.popup-header {
  padding-right: 40px;
}

.popup-header h2 {
  margin: 0 0 12px;
  font-size: 26px;
  color: var(--color-ink);
}

.popup-header p {
  margin: 12px 0 0;
  color: var(--color-ink-soft);
  font-size: 14px;
}

.total-score-badge {
  width: fit-content;
  padding: 6px 16px;
  border-radius: var(--radius-pill);
  color: #fff;
  font-size: 17px;
  font-weight: 800;
}

.total-score-badge span {
  font-size: 13px;
  font-weight: 500;
  opacity: 0.9;
}

.popup-section {
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid var(--color-border);
}

.popup-section h3 {
  margin: 0 0 16px;
  font-size: 16px;
  color: var(--color-ink);
}

.category-score-list,
.reason-list {
  margin: 0;
  padding: 0;
  list-style: none;
}

.category-score-list li {
  margin-bottom: 14px;
}

.score-title {
  margin-bottom: 6px;
  display: flex;
  justify-content: space-between;
  font-size: 13.5px;
  color: var(--color-ink);
}

.score-progress {
  width: 100%;
  height: 8px;
  overflow: hidden;
  border-radius: var(--radius-pill);
  background: var(--color-primary-soft);
}

.score-progress-value {
  height: 100%;
  border-radius: inherit;
  transition: width 0.3s ease;
}

.reason-list li {
  margin-bottom: 14px;
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.reason-check {
  width: 22px;
  height: 22px;
  flex-shrink: 0;
  display: grid;
  place-items: center;
  border-radius: 50%;
  background: var(--color-primary);
  color: #fff;
  font-size: 12px;
  font-weight: 800;
}

.reason-list strong {
  display: block;
  margin-bottom: 4px;
  color: var(--color-ink);
  font-size: 14px;
}

.reason-list p {
  margin: 0;
  color: var(--color-ink-soft);
  font-size: 13.5px;
  line-height: 1.5;
}

.facility-link-button {
  margin-top: 28px;
  padding: 14px 16px;
  display: block;
  border-radius: var(--radius-pill);
  color: #fff;
  background: var(--color-primary);
  text-align: center;
  font-weight: 700;
  text-decoration: none;
  transition: background 0.15s ease;
}

.facility-link-button:hover {
  background: var(--color-primary-dark);
}

@media (max-width: 900px) {
  .map-content {
    display: flex;
    flex-direction: column;
  }

  .legend-panel {
    position: static;
    width: 100%;
    margin-bottom: 16px;
    box-shadow: none;
  }

  .legend-panel ul {
    display: flex;
    flex-wrap: wrap;
    gap: 10px 18px;
  }

  .legend-panel li {
    margin: 0;
  }

  .map-area {
    padding: 16px;
  }
}

@media (max-width: 600px) {
  .popup-backdrop {
    padding: 12px;
  }

  .district-popup {
    padding: 22px 18px;
  }
}
</style>