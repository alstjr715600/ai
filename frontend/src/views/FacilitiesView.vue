<script setup>
import { onMounted, ref, watch } from 'vue'
import api from '../services/api'

const facilityTypes = [
  { value: 'CHILDCARE', label: '어린이집' }, { value: 'PARK', label: '놀이터' },
  { value: 'HOSPITAL', label: '병원' }, { value: 'SCHOOL', label: '초등학교' },
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

onMounted(async () => {
  const { data } = await api.get('/districts')
  districts.value = data
  await search()
})
watch([selectedType, selectedDistrict], () => { page.value = 1; search() })

async function search() {
  loading.value = true
  try {
    const { data } = await api.get('/facilities', { params: { type: selectedType.value, district: selectedDistrict.value, keyword: keyword.value || undefined, page: page.value, size } })
    facilities.value = data.items
    total.value = data.total
  } finally { loading.value = false }
}
function previousPage(){ if(page.value>1){page.value--;search()} }
function nextPage(){ if(page.value*size<total.value){page.value++;search()} }
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
              <td>{{ facility.name }}</td>
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
  </section>
</template>

<style scoped>
.status-message { padding: 40px; text-align: center; color: var(--color-ink-soft); }
.pagination { margin-top: 16px; display: flex; justify-content: center; align-items: center; gap: 12px; }
</style>
