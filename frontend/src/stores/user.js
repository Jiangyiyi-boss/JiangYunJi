import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useUserStore = defineStore('user', () => {
  // 兼容 localStorage 中残留 'undefined' 字符串或非法 JSON 的情况
  const rawUser = localStorage.getItem('user')
  let initUser = null
  if (rawUser && rawUser !== 'undefined' && rawUser !== 'null') {
    try { initUser = JSON.parse(rawUser) } catch { localStorage.removeItem('user') }
  }

  const user = ref(initUser)
  const token = ref(localStorage.getItem('token') || '')

  function setUser(userData) {
    user.value = userData
    localStorage.setItem('user', JSON.stringify(userData))
  }

  function setToken(newToken) {
    token.value = newToken
    localStorage.setItem('token', newToken)
  }

  function logout() {
    user.value = null
    token.value = ''
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }

  return { user, token, setUser, setToken, logout }
})
