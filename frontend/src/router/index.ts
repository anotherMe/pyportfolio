
import { createRouter, createWebHistory } from 'vue-router'
import InstrumentsListView from '@/views/InstrumentsList.vue'
import HomeView from '@/views/Home.vue'

const routes = [
  { path: '/', name: 'home', component: HomeView },
  { path: '/instruments', name: 'instruments', component: InstrumentsListView },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
