import { createRouter, createWebHistory } from 'vue-router'
import ChatView from '../views/ChatView.vue'
import MapView from '../views/MapView.vue'
import FacilitiesView from '../views/FacilitiesView.vue'
import CommunityView from '../views/CommunityView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'chat', component: ChatView },
    { path: '/map', name: 'map', component: MapView },
    { path: '/facilities', name: 'facilities', component: FacilitiesView },
    { path: '/community', name: 'community', component: CommunityView }
  ]
})

export default router
