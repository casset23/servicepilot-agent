import { createRouter, createWebHistory } from 'vue-router'
import AgentWorkspace from '../views/AgentWorkspace.vue'
import Login from '../views/Login.vue'
import CustomerPortal from '../views/CustomerPortal.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/preview', name: 'preview', component: CustomerPortal, props: { preview: true } },
    {
      path: '/',
      name: 'home',
      component: AgentWorkspace,
      meta: { requiresAuth: true }
    },
    {
      path: '/login',
      name: 'login',
      component: Login
    },
    {
      path: '/register',
      name: 'register',
      component: Login  // 使用同一个组件
    },
    {
      path: '/ecommerce',
      name: 'ecommerce',
      component: CustomerPortal
    }
  ]
})

// 路由守卫
router.beforeEach((to, _from, next) => {
  if (to.name === 'preview') { next(); return }
  const token = localStorage.getItem('token')
  
  // 如果已登录用户访问登录或注册页，跳转到首页
  if ((to.path === '/login' || to.path === '/register') && token) {
    next('/')
    return
  }
  
  // 如果未登录用户访问需要认证的页面，跳转到登录页
  if (!token && to.path !== '/login' && to.path !== '/register') {
    next('/login')
    return
  }
  
  next()
})

export default router 