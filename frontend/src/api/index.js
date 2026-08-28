import axios from 'axios'
import { useUserStore } from '@/stores/user'
import router from '@/router'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response?.status === 401) {
      const url = error.config?.url || ''
      const publicPaths = ['/auth/login', '/auth/register', '/auth/admin/login', '/payment/status-by-no', '/payment/query']
      if (!publicPaths.some(p => url.includes(p))) {
        // 只对需要登录的页面才自动跳转，公共页面的 401 由组件自行处理
        const currentRoute = router.currentRoute.value
        if (currentRoute.meta?.requiresAuth) {
          localStorage.removeItem('token')
          const userStore = useUserStore()
          userStore.logout()
          router.push('/login')
        }
      }
    }
    return Promise.reject(error.response?.data || error)
  }
)

export default api
