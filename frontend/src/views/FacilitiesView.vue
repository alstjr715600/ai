<script setup>
import { nextTick, onMounted, ref, watch } from 'vue'
import api from '../services/api'

const facilityTypes = [
  { value: 'CHILDCARE', label: '어린이집' },
  { value: 'PARK', label: '놀이터' },
  { value: 'HOSPITAL', label: '병원' },
  { value: 'SCHOOL', label: '초등학교' },
  { value: 'CULTURE', label: '문화센터' }
]

const districts = ref([])
const selectedType = ref('CHILDCARE')
const selectedDistrict = ref('전체')
const keyword = ref('')
const facilities = ref([])
const loading = ref(false)
const page = ref(1)
const size = 20
const total = ref(0)

/* 지도 관련 */
const selectedFacility = ref(null)
const showMapModal = ref(false)
const mapContainer = ref(null)
const mapErrorMessage = ref('')
const mapLoading = ref(false)

let map = null
let marker = null
let infoWindow = null

onMounted(async () => {
  const { data } = await api.get('/districts')
  districts.value = data

  await search()
})

watch([selectedType, selectedDistrict], () => {
  page.value = 1
  search()
})

async function search() {
  loading.value = true

  try {
    const { data } = await api.get('/facilities', {
      params: {
        type: selectedType.value,
        district: selectedDistrict.value,
        keyword: keyword.value || undefined,
        page: page.value,
        size
      }
    })

    facilities.value = data.items
    total.value = data.total
  } finally {
    loading.value = false
  }
}

function previousPage() {
  if (page.value > 1) {
    page.value--
    search()
  }
}

function nextPage() {
  if (page.value * size < total.value) {
    page.value++
    search()
  }
}

/* 카카오맵 SDK 불러오기 */
function loadKakaoMapSdk() {
  return new Promise((resolve, reject) => {
    if (window.kakao?.maps?.services) {
      resolve()
      return
    }

    const existingScript = document.querySelector(
      'script[data-kakao-map-sdk="true"]'
    )

    if (existingScript) {
      existingScript.addEventListener('load', () => {
        window.kakao.maps.load(resolve)
      })

      existingScript.addEventListener('error', () => {
        reject(new Error('카카오 지도 SDK 요청 실패'))
      })

      return
    }

    const appKey = import.meta.env.VITE_KAKAO_MAP_KEY

    if (!appKey) {
      reject(new Error('VITE_KAKAO_MAP_KEY가 설정되지 않았습니다.'))
      return
    }

    const script = document.createElement('script')

    script.dataset.kakaoMapSdk = 'true'
    script.src =
      `https://dapi.kakao.com/v2/maps/sdk.js` +
      `?appkey=${appKey}` +
      `&autoload=false` +
      `&libraries=services`

    script.onload = () => {
      window.kakao.maps.load(resolve)
    }

    script.onerror = () => {
      reject(new Error('카카오 지도 SDK 요청 실패'))
    }

    document.head.appendChild(script)
  })
}

/* 시설 클릭 */
async function openMapModal(facility) {
  selectedFacility.value = facility
  showMapModal.value = true
  mapErrorMessage.value = ''
  mapLoading.value = true

  await nextTick()

  try {
    await loadKakaoMapSdk()
    await nextTick()

    displayFacilityMap(facility)
  } catch (error) {
    console.error(error)
    mapErrorMessage.value =
      error.message || '카카오 지도를 불러오지 못했습니다.'
  } finally {
    mapLoading.value = false
  }
}

/* 주소를 좌표로 변환한 뒤 지도 표시 */
function displayFacilityMap(facility) {
  if (!mapContainer.value) {
    mapErrorMessage.value = '지도 영역을 찾지 못했습니다.'
    return
  }

  const defaultPosition = new window.kakao.maps.LatLng(
    37.5665,
    126.978
  )

  map = new window.kakao.maps.Map(mapContainer.value, {
    center: defaultPosition,
    level: 3
  })

  const geocoder = new window.kakao.maps.services.Geocoder()

  geocoder.addressSearch(facility.address, (result, status) => {
    if (status !== window.kakao.maps.services.Status.OK) {
      mapErrorMessage.value =
        '해당 주소의 지도 위치를 찾지 못했습니다.'
      return
    }

    const position = new window.kakao.maps.LatLng(
      Number(result[0].y),
      Number(result[0].x)
    )

    marker = new window.kakao.maps.Marker({
      map,
      position
    })

    infoWindow = new window.kakao.maps.InfoWindow({
      content: `
        <div style="
          min-width:180px;
          padding:10px;
          font-size:13px;
          line-height:1.5;
          text-align:center;
        ">
          <strong>${escapeHtml(facility.name)}</strong>
        </div>
      `
    })

    infoWindow.open(map, marker)

    map.setCenter(position)

    setTimeout(() => {
      map.relayout()
      map.setCenter(position)
    }, 100)
  })
}

function closeMapModal() {
  showMapModal.value = false
  selectedFacility.value = null
  mapErrorMessage.value = ''

  if (infoWindow) {
    infoWindow.close()
  }

  if (marker) {
    marker.setMap(null)
  }

  map = null
  marker = null
  infoWindow = null
}

function escapeHtml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;')
}
</script>

<template>
  <section>
    <header class="hero-band">
      <div class="hero-top">
        <div>
          <span class="hero-eyebrow">시설 데이터</span>
          <h1>육아 시설 조회</h1>
          <p>로컬 JSON 데이터에서 자치구별 어린이집·놀이터·병원·초등학교·문화센터를 조회할 수 있어요.</p>
        </div>
      </div>
      <div class="stat-chip-row">
        <div class="stat-chip">
          <span class="stat-label">조회된 시설</span>
          <span class="stat-value">{{ total }}건</span>
        </div>
      </div>
    </header>

    <div class="filter-card">
      <div class="filter-bar">
        <select v-model="selectedType"><option v-for="type in facilityTypes" :key="type.value" :value="type.value">{{ type.label }}</option></select>
        <select v-model="selectedDistrict"><option value="전체">전체 자치구</option><option v-for="district in districts" :key="district.district_code" :value="district.district_name">{{ district.district_name }}</option></select>
        <input v-model="keyword" placeholder="시설명·주소·분류 검색" @keyup.enter="page=1;search()" />
        <button @click="page=1;search()">조회</button>
      </div>
    </div>

    <p class="notice">외부 서울시 API를 실시간 호출하지 않습니다. 현재 포함된 데이터는 화면 구현용 예시 JSON이며, 나중에 실제 내려받은 JSON으로 교체할 수 있습니다.</p>

    <p v-if="loading" class="status-message">조회 중입니다...</p>

    <template v-else>
      <p class="result-count"><strong>{{ facilities.length }}</strong>건 표시 중 · 전체 <strong>{{ total }}</strong>건</p>

      <div class="table-wrap">
        <table>
          <thead>
            <tr><th>시설명</th><th>자치구</th><th>분류</th><th>주소</th><th>전화번호</th></tr>
          </thead>
          <tbody>
            <tr v-for="facility in facilities" :key="facility.id">
              <td>
  <button
    type="button"
    class="facility-name-button"
    @click="openMapModal(facility)"
  >
    {{ facility.name }}
  </button>
</td>
              <td><span class="badge">{{ facility.district }}</span></td>
              <td>{{ facility.category }}</td>
              <td>{{ facility.address }}</td>
              <td>{{ facility.phone ?? '-' }}</td>
            </tr>
          </tbody>
        </table>

        <div v-if="!facilities.length" class="empty-state">
          <span class="empty-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
              <circle cx="11" cy="11" r="6.5" stroke="currentColor" stroke-width="1.6" />
              <path d="M20 20l-4.3-4.3" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" />
            </svg>
          </span>
          <strong>조회 결과가 없어요</strong>
          <span>검색어나 필터 조건을 바꿔서 다시 시도해보세요.</span>
        </div>
      </div>

      <div class="pagination">
        <button :disabled="page===1" @click="previousPage">이전</button>
        <span>{{ page }}페이지 · 총 {{ total }}건</span>
        <button :disabled="page*size>=total" @click="nextPage">다음</button>
      </div>
    </template>
    <Teleport to="body">
  <div
    v-if="showMapModal"
    class="map-modal-overlay"
    @click.self="closeMapModal"
  >
    <div class="map-modal">
      <div class="map-modal-header">
        <div>
          <span class="map-modal-label">시설 위치</span>

          <h2>
            {{ selectedFacility?.name }}
          </h2>

          <p>
            {{ selectedFacility?.address }}
          </p>
        </div>

        <button
          type="button"
          class="map-close-button"
          aria-label="지도 닫기"
          @click="closeMapModal"
        >
          ×
        </button>
      </div>

      <div class="map-modal-body">
        <p v-if="mapLoading" class="map-status">
          지도를 불러오는 중입니다...
        </p>

        <p v-if="mapErrorMessage" class="map-error">
          {{ mapErrorMessage }}
        </p>

        <div
          ref="mapContainer"
          class="kakao-map"
        ></div>
      </div>

      <div class="map-modal-footer">
        <div>
          <strong>{{ selectedFacility?.category }}</strong>
          <span>{{ selectedFacility?.phone ?? '전화번호 없음' }}</span>
        </div>

        <button
          type="button"
          @click="closeMapModal"
        >
          닫기
        </button>
      </div>
    </div>
  </div>
</Teleport>
  </section>
</template>

<style scoped>
.status-message { padding: 40px; text-align: center; color: var(--color-ink-soft); }
.pagination { margin-top: 16px; display: flex; justify-content: center; align-items: center; gap: 12px; }
.facility-link {
  color: #2563eb;
  cursor: pointer;
  font-weight: 600;
  text-decoration: underline;
}

.facility-link:hover {
  color: #1d4ed8;
}
.facility-name-button {
  padding: 0;
  border: 0;
  background: transparent;
  color: #000000;
  font: inherit;
  font-weight: 700;
  text-align: left;
  cursor: pointer;
}

.facility-name-button:hover {
  text-decoration: underline;
}

.map-modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: rgba(15, 23, 42, 0.55);
}

.map-modal {
  width: min(760px, 100%);
  overflow: hidden;
  border-radius: 20px;
  background: white;
  box-shadow: 0 24px 80px rgba(15, 23, 42, 0.3);
}

.map-modal-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
  padding: 22px 24px;
  border-bottom: 1px solid #e5e7eb;
}

.map-modal-label {
  display: block;
  margin-bottom: 5px;
  color: #2563eb;
  font-size: 12px;
  font-weight: 700;
}

.map-modal-header h2 {
  margin: 0;
  font-size: 21px;
}

.map-modal-header p {
  margin: 7px 0 0;
  color: #64748b;
  font-size: 14px;
}

.map-close-button {
  width: 36px;
  height: 36px;
  padding: 0;
  border: 0;
  border-radius: 50%;
  background: #f1f5f9;
  color: #334155;
  font-size: 25px;
  line-height: 1;
  cursor: pointer;
}

.map-modal-body {
  position: relative;
  min-height: 430px;
  background: #f1f5f9;
}

.kakao-map {
  width: 100%;
  height: 430px;
}

.map-status,
.map-error {
  position: absolute;
  top: 16px;
  left: 50%;
  z-index: 10;
  margin: 0;
  padding: 10px 16px;
  border-radius: 10px;
  background: white;
  box-shadow: 0 5px 20px rgba(15, 23, 42, 0.15);
  transform: translateX(-50%);
}

.map-error {
  color: #dc2626;
}

.map-modal-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  padding: 18px 24px;
  border-top: 1px solid #e5e7eb;
}

.map-modal-footer div {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.map-modal-footer span {
  color: #64748b;
  font-size: 13px;
}

.map-modal-footer button {
  padding: 9px 18px;
  border: 0;
  border-radius: 8px;
  background: #1e293b;
  color: white;
  cursor: pointer;
}

@media (max-width: 600px) {
  .map-modal-overlay {
    padding: 12px;
  }

  .map-modal-body {
    min-height: 360px;
  }

  .kakao-map {
    height: 360px;
  }
}
</style>
