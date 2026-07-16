<script setup>
import { computed, onMounted, ref } from 'vue'

const props = defineProps({
  districts: { type: Array, default: () => [] },
  selectedCode: { type: String, default: '' }
})

const emit = defineEmits(['select'])

const features = ref([])
const loading = ref(true)
const errorMessage = ref('')

const WIDTH = 760
const HEIGHT = 650
const PADDING = 28

const GEOJSON_URL =
  'https://raw.githubusercontent.com/southkorea/seoul-maps/master/kostat/2013/json/seoul_municipalities_geo_simple.json'

onMounted(loadGeoJson)

async function loadGeoJson() {
  loading.value = true
  errorMessage.value = ''

  try {
    const response = await fetch(GEOJSON_URL)

    if (!response.ok) {
      throw new Error('서울 지도 데이터를 불러오지 못했습니다.')
    }

    const geoJson = await response.json()
    features.value = geoJson.features ?? []
  } catch (error) {
    console.error(error)
    errorMessage.value =
      '실제 서울 자치구 지도를 불러오지 못했습니다. 인터넷 연결을 확인해주세요.'
  } finally {
    loading.value = false
  }
}

function featureName(feature) {
  const p = feature.properties ?? {}
  return p.name ?? p.NAME ?? p.SIG_KOR_NM ?? p.SGG_NM ?? p.adm_nm ?? ''
}

function districtFor(feature) {
  const name = featureName(feature)
  return props.districts.find(item => item.district_name === name)
}

function flattenCoordinates(geometry) {
  if (!geometry) return []
  if (geometry.type === 'Polygon') return geometry.coordinates.flat()
  if (geometry.type === 'MultiPolygon') return geometry.coordinates.flat(2)
  return []
}

const bounds = computed(() => {
  const all = features.value.flatMap(feature => flattenCoordinates(feature.geometry))

  if (!all.length) {
    return { minX: 0, maxX: 1, minY: 0, maxY: 1 }
  }

  const xs = all.map(([x]) => x)
  const ys = all.map(([, y]) => y)

  return {
    minX: Math.min(...xs),
    maxX: Math.max(...xs),
    minY: Math.min(...ys),
    maxY: Math.max(...ys)
  }
})

function project([longitude, latitude]) {
  const xRange = bounds.value.maxX - bounds.value.minX || 1
  const yRange = bounds.value.maxY - bounds.value.minY || 1

  const availableWidth = WIDTH - PADDING * 2
  const availableHeight = HEIGHT - PADDING * 2
  const scale = Math.min(availableWidth / xRange, availableHeight / yRange)

  const renderedWidth = xRange * scale
  const renderedHeight = yRange * scale
  const offsetX = (WIDTH - renderedWidth) / 2
  const offsetY = (HEIGHT - renderedHeight) / 2

  return [
    offsetX + (longitude - bounds.value.minX) * scale,
    offsetY + (bounds.value.maxY - latitude) * scale
  ]
}

function ringPath(ring) {
  return ring
    .map((point, index) => {
      const [x, y] = project(point)
      return `${index === 0 ? 'M' : 'L'} ${x.toFixed(2)} ${y.toFixed(2)}`
    })
    .join(' ') + ' Z'
}

function geometryPath(geometry) {
  if (!geometry) return ''

  if (geometry.type === 'Polygon') {
    return geometry.coordinates.map(ringPath).join(' ')
  }

  if (geometry.type === 'MultiPolygon') {
    return geometry.coordinates
      .flatMap(polygon => polygon.map(ringPath))
      .join(' ')
  }

  return ''
}

function center(feature) {
  const points = flattenCoordinates(feature.geometry)
  if (!points.length) return { x: 0, y: 0 }

  const projected = points.map(project)
  const x = projected.reduce((sum, point) => sum + point[0], 0) / projected.length
  const y = projected.reduce((sum, point) => sum + point[1], 0) / projected.length
  return { x, y }
}

function selectFeature(feature) {
  const district = districtFor(feature)
  if (district) emit('select', district)
}
</script>

<template>
  <div class="map-wrapper">
    <p v-if="loading">실제 서울 지도를 불러오는 중입니다.</p>
    <p v-else-if="errorMessage" class="error-message">{{ errorMessage }}</p>

    <svg
      v-else
      class="seoul-map"
      :viewBox="`0 0 ${WIDTH} ${HEIGHT}`"
      role="img"
      aria-label="서울 자치구별 육아 환경 점수 지도"
    >
      <g
        v-for="(feature, index) in features"
        :key="`${featureName(feature)}-${index}`"
        class="district-group"
        @click="selectFeature(feature)"
      >
        <path
          :d="geometryPath(feature.geometry)"
          :fill="districtFor(feature)?.color ?? '#e5e7eb'"
          fill-rule="evenodd"
          class="district-path"
          :class="{
            selected: districtFor(feature)?.district_code === selectedCode
          }"
        >
          <title>
            {{ featureName(feature) }}
            {{ districtFor(feature)?.total_score ?? '-' }}점
          </title>
        </path>

        <g
          v-if="districtFor(feature)"
          class="district-label"
          :transform="`translate(${center(feature).x}, ${center(feature).y})`"
        >
          <text text-anchor="middle" class="district-name">
            {{ featureName(feature) }}
          </text>
          <text y="17" text-anchor="middle" class="district-score">
            {{ districtFor(feature).total_score }}
          </text>
        </g>
      </g>
    </svg>
  </div>
</template>

<style scoped>
.map-wrapper {
  width: 100%;
  min-height: 650px;
  display: grid;
  place-items: center;
}

.seoul-map {
  width: min(820px, 100%);
  height: auto;
  overflow: visible;
  filter: drop-shadow(0 6px 18px rgb(31 41 55 / 8%));
}

.district-group {
  cursor: pointer;
}

.district-path {
  stroke: #a9b6a4;
  stroke-width: 1.6;
  vector-effect: non-scaling-stroke;
  transition: filter 0.15s ease, stroke 0.15s ease, stroke-width 0.15s ease;
}

.district-group:hover .district-path {
  filter: brightness(1.04) saturate(1.08);
  stroke: #1f5b43;
  stroke-width: 2.6;
}

.district-path.selected {
  stroke: #1f5b43;
  stroke-width: 4;
}

.district-label {
  pointer-events: none;
}

.district-name,
.district-score {
  fill: #1f2937;
  font-weight: 700;
  paint-order: stroke;
  stroke: rgb(255 255 255 / 88%);
  stroke-width: 3px;
  stroke-linejoin: round;
}

.district-name { font-size: 13px; }
.district-score { font-size: 12px; }
.error-message { color: #e8637a; }

@media (max-width: 650px) {
  .map-wrapper { min-height: 430px; }
  .district-name { font-size: 10px; }
  .district-score { font-size: 9px; }
}
</style>
