<script setup>
import { onMounted, ref } from 'vue'
import api from '../services/api'

const posts = ref([])
const selectedPost = ref(null)
const showForm = ref(false)
const editMode = ref(false)
const errorMessage = ref('')

const comments = ref([])

const commentForm = ref({
  content: '',
  password: ''
})

const form = ref({
  title: '',
  content: '',
  district_name: '전체',
  password: ''
})

const districts = [
  '전체', '종로구', '중구', '용산구', '성동구', '광진구',
  '동대문구', '중랑구', '성북구', '강북구', '도봉구',
  '노원구', '은평구', '서대문구', '마포구', '양천구',
  '강서구', '구로구', '금천구', '영등포구', '동작구',
  '관악구', '서초구', '강남구', '송파구', '강동구'
]

onMounted(loadPosts)

async function loadPosts() {
  const { data } = await api.get('/community/posts')
  posts.value = data
}

async function openPost(post) {
  const { data } = await api.get(`/community/posts/${post.id}`)

  selectedPost.value = data

  await loadComments(post.id)

  await loadPosts()
}

function openCreate() {
  editMode.value = false
  showForm.value = true
  form.value = {
    title: '',
    content: '',
    district_name: '전체',
    password: ''
  }
}

function openEdit() {
  if (!selectedPost.value) return

  editMode.value = true
  showForm.value = true
  form.value = {
    title: selectedPost.value.title,
    content: selectedPost.value.content,
    district_name: selectedPost.value.district_name,
    password: ''
  }
}

async function submitForm() {
  errorMessage.value = ''

  try {
    if (editMode.value) {
      const { data } = await api.put(
        `/community/posts/${selectedPost.value.id}`,
        form.value
      )
      selectedPost.value = data
    } else {
      await api.post('/community/posts', form.value)
    }

    showForm.value = false
    await loadPosts()
  } catch (error) {
    errorMessage.value =
      error.response?.data?.detail ?? '요청을 처리하지 못했습니다.'
  }
}

async function deletePost() {
  const password = window.prompt('게시글 비밀번호를 입력해주세요.')

  if (!password) return

  try {
    await api.delete(`/community/posts/${selectedPost.value.id}`, {
      data: { password }
    })
    selectedPost.value = null
    await loadPosts()
  } catch (error) {
    window.alert(
      error.response?.data?.detail ?? '삭제하지 못했습니다.'
    )
  }
}

async function loadComments(postId) {
  const { data } = await api.get(
    `/community/posts/${postId}/comments`
  )

  comments.value = data
}


async function submitComment() {
  try {
    await api.post(
      `/community/posts/${selectedPost.value.id}/comments`,
      commentForm.value
    )

    commentForm.value = {
      content: '',
      password: ''
    }

    await loadComments(selectedPost.value.id)

  } catch (error) {
    window.alert(
      error.response?.data?.detail ??
      '댓글 작성 실패'
    )
  }
}
</script>

<template>
  <section>
    <header class="hero-band">
      <div class="hero-top">
        <div>
          <span class="hero-eyebrow">익명 게시판</span>
          <h1>익명 커뮤니티</h1>
          <p>자치구별 육아 정보를 자유롭게 공유합니다. 회원가입 없이 비밀번호만으로 작성·수정할 수 있어요.</p>
        </div>
        <button type="button" class="primary-action" @click="openCreate">+ 글쓰기</button>
      </div>

      <div class="stat-chip-row">
        <div class="stat-chip">
          <span class="stat-label">전체 게시글</span>
          <span class="stat-value">{{ posts.length }}건</span>
        </div>
      </div>
    </header>

    <p v-if="errorMessage" class="notice error">{{ errorMessage }}</p>

    <div class="community-layout">
      <div class="post-list">
        <button
          v-for="post in posts"
          :key="post.id"
          type="button"
          class="post-row"
          @click="openPost(post)"
        >
          <strong>{{ post.title }}</strong>
          <span>
            <span class="badge">{{ post.district_name }}</span>
            · 조회 {{ post.view_count }}
          </span>
        </button>

        <div v-if="!posts.length" class="empty-state">
          <span class="empty-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
              <path d="M4 5h16v11H8l-4 4V5Z" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round" />
            </svg>
          </span>
          <strong>아직 등록된 게시글이 없어요</strong>
          <span>가장 먼저 우리 동네 육아 정보를 공유해보세요.</span>
        </div>
      </div>

      <article v-if="selectedPost" class="post-detail">
        <span class="badge">{{ selectedPost.district_name }}</span>
        <h2>{{ selectedPost.title }}</h2>
        <p class="post-meta">{{ selectedPost.author }}</p>
        <p class="post-content">{{ selectedPost.content }}</p>

        <section class="comment-section">
          <h3>댓글 {{ comments.length }}</h3>

          <div v-if="comments.length">
            <div
              v-for="comment in comments"
              :key="comment.id"
              class="comment-item"
            >
              <p>{{ comment.content }}</p>
              <small>{{ comment.author }}</small>
            </div>
          </div>

          <p v-else class="post-meta">아직 댓글이 없습니다.</p>

          <form @submit.prevent="submitComment">
            <textarea
              v-model="commentForm.content"
              placeholder="댓글 입력"
              required
            ></textarea>

            <input
              v-model="commentForm.password"
              type="password"
              placeholder="비밀번호"
              required
            />

            <button type="submit">댓글 작성</button>
          </form>
        </section>

        <div class="button-row">
          <button type="button" @click="openEdit">수정</button>
          <button type="button" @click="deletePost">삭제</button>
        </div>
      </article>

      <div v-else class="post-detail empty-state">
        <span class="empty-icon">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
            <path d="M9 5l7 7-7 7" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
        </span>
        <strong>게시글을 선택해주세요</strong>
        <span>왼쪽 목록에서 글을 클릭하면 내용과 댓글을 볼 수 있어요.</span>
      </div>
    </div>

    <div v-if="showForm" class="modal-backdrop">
      <form class="modal-panel" @submit.prevent="submitForm">
        <h2>{{ editMode ? '게시글 수정' : '게시글 작성' }}</h2>

        <label>
          자치구
          <select v-model="form.district_name">
            <option
              v-for="district in districts"
              :key="district"
              :value="district"
            >
              {{ district }}
            </option>
          </select>
        </label>

        <label>
          제목
          <input v-model="form.title" required maxlength="100" />
        </label>

        <label>
          내용
          <textarea v-model="form.content" required rows="8"></textarea>
        </label>

        <label>
          비밀번호
          <input
            v-model="form.password"
            required
            minlength="4"
            maxlength="20"
            type="password"
          />
        </label>

        <p v-if="errorMessage" class="error">{{ errorMessage }}</p>

        <div class="button-row">
          <button type="submit">저장</button>
          <button type="button" @click="showForm = false">취소</button>
        </div>
      </form>
    </div>
  </section>
</template>
