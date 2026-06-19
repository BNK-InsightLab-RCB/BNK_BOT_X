import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/authStore.js'
import LoginPage from '../pages/authpages/LoginPage.vue'
import ChatPage from '../pages/chatpages/ChatPage.vue'
import AdminDashboardPage from '../pages/adminpages/AdminDashboardPage.vue'
import ManualListPage from '../pages/adminpages/ManualListPage.vue'
import ManualEditPage from '../pages/adminpages/ManualEditPage.vue'
import HandoffPage from '../pages/adminpages/HandoffPage.vue'

const MainRouter = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: LoginPage },
    { path: '/login', component: LoginPage },
    { path: '/chat', component: ChatPage, meta: { requiresAuth: true } },
    { path: '/admin', component: AdminDashboardPage, meta: { requiresAuth: true, requiresAdmin: true } },
    { path: '/admin/manuals', component: ManualListPage, meta: { requiresAuth: true, requiresAdmin: true } },
    { path: '/admin/manuals/:manualId', component: ManualEditPage, meta: { requiresAuth: true, requiresAdmin: true } },
    { path: '/admin/handoffs', component: HandoffPage, meta: { requiresAuth: true, requiresAdmin: true } }
  ]
})

MainRouter.beforeEach((to) => {
  const authStore = useAuthStore()
  if (to.meta.requiresAuth && !authStore.isLogin) {
    return '/login'
  }
  if (to.meta.requiresAdmin && !authStore.isAdmin) {
    return '/chat'
  }
  if ((to.path === '/' || to.path === '/login') && authStore.isLogin) {
    return authStore.isAdmin ? '/admin' : '/chat'
  }
  return true
})

export default MainRouter
