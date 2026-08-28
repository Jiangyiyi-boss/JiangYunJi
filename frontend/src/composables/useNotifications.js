import { ref, onMounted, onUnmounted } from 'vue'
import { courseApi } from '@/api/modules'
import { useUserStore } from '@/stores/user'

const unreadCount = ref(0)
let pollTimer = null
let activeListeners = 0

export function useCourseNotifications() {
  const userStore = useUserStore()

  const startPolling = () => {
    if (pollTimer) return
    fetchUnreadCount()
    pollTimer = setInterval(fetchUnreadCount, 30000)
  }

  const stopPolling = () => {
    if (pollTimer) {
      clearInterval(pollTimer)
      pollTimer = null
    }
  }

  const fetchUnreadCount = async () => {
    if (!userStore.user || !userStore.token) {
      unreadCount.value = 0
      return
    }
    try {
      const res = await courseApi.getUnreadCount()
      unreadCount.value = res.count || 0
    } catch (_) {
      // Silently ignore
    }
  }

  onMounted(() => {
    activeListeners++
    if (activeListeners === 1) startPolling()
  })

  onUnmounted(() => {
    activeListeners--
    if (activeListeners === 0) stopPolling()
  })

  return { unreadCount }
}
