import { createRouter, createWebHistory } from 'vue-router'
import Home from '@/views/Home.vue'
import Gallery from '@/views/Gallery.vue'
import Print from '@/views/Print.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home
  },
  {
    path: '/gallery',
    name: 'Gallery',
    component: Gallery
  },
  {
    path: '/print/:id',
    name: 'Print',
    component: Print,
    props: true
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
