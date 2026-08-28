<template>
  <router-view />
</template>

<script setup>
import { onMounted } from 'vue'
import { useUserStore } from '@/stores/user'
import { userApi } from '@/api/modules'

const userStore = useUserStore()

onMounted(async () => {
  if (userStore.token) {
    try {
      const res = await userApi.getMe()
      userStore.setUser(res)
    } catch (err) {
      // Token may be invalid, clear session
      userStore.logout()
    }
  }
})
</script>

<style>
#app {
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #333;
  min-height: 100vh;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}
</style>
