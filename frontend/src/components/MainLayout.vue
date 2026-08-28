<template>
  <div class="layout">
    <!-- 顶部导航 -->
    <header class="header">
      <div class="header-content container">
        <router-link to="/home" class="logo">
          <span class="logo-icon">匠</span>
          <span class="logo-text">匠韵集</span>
        </router-link>
        <nav class="nav">
          <!-- 匠人导航（非用户浏览模式时显示） -->
          <template v-if="userStore.user?.role === 'artisan' && !browseAsUser">
            <router-link to="/artisan/dashboard" class="nav-item">匠人中心</router-link>
            <router-link to="/artisan/forum" class="nav-item">匠人雅集</router-link>
            <router-link to="/artisan/courses" class="nav-item">匠艺学堂管理</router-link>
            <a :href="shopPreviewUrl" target="_blank" class="nav-item nav-external">
              店铺预览 <el-icon><TopRight /></el-icon>
            </a>
          </template>
          <!-- 普通用户导航（或匠人处于用户浏览模式） -->
          <template v-else>
            <router-link to="/home" class="nav-item">商城首页</router-link>
            <router-link to="/forum" class="nav-item">匠人雅集</router-link>
            <router-link to="/courses" class="nav-item">匠艺学堂</router-link>
            <router-link to="/my" class="nav-item">我的</router-link>
            <span class="nav-item nav-ai" @click="toggleChat">
              <el-icon><ChatDotRound /></el-icon> AI问答
            </span>
          </template>
        </nav>
        <div class="header-right">
          <el-button
            v-if="browseAsUser"
            type="primary"
            size="small"
            @click="exitBrowseMode"
          >
            返回商家中心
          </el-button>
          <template v-if="userStore.user">
            <router-link v-if="userStore.user.role !== 'artisan'" to="/cart" class="nav-item cart-link">
              <el-icon><ShoppingCart /></el-icon>
              <span class="cart-text">购物车</span>
            </router-link>
            <el-dropdown trigger="click">
              <span class="user-info">
                <el-avatar :size="32" :src="userStore.user?.avatar">{{ userStore.user.nickname?.[0] || 'U' }}</el-avatar>
                <span class="username">{{ userStore.user.nickname }}</span>
              </span>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item v-if="userStore.user?.role !== 'user'" @click="$router.push('/profile')">账号管理</el-dropdown-item>
                  <el-dropdown-item @click="handleLogout">退出登录</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
          <template v-else>
            <router-link to="/login" class="btn-login">登录</router-link>
            <router-link to="/register" class="btn-register">注册</router-link>
          </template>
        </div>
      </div>
    </header>

    <!-- 主内容区 -->
    <main class="main">
      <slot />
    </main>

    <!-- AI 问答助手 -->
    <ChatAssistant ref="chatRef" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { artisanApi } from '@/api/modules'
import { ShoppingCart, TopRight, ChatDotRound } from '@element-plus/icons-vue'
import ChatAssistant from '@/components/ChatAssistant.vue'

const router = useRouter()
const userStore = useUserStore()
const artisanId = ref(null)
const chatRef = ref(null)

const toggleChat = () => {
  if (chatRef.value) {
    chatRef.value.visible = !chatRef.value.visible
  }
}

const shopPreviewUrl = computed(() => {
  if (artisanId.value) {
    return `${window.location.origin}/artisan/${artisanId.value}`
  }
  return `${window.location.origin}/home`
})

// 用户浏览模式：匠人从店铺预览跳转过来时，保持用户视角
const browseAsUser = ref(false)

const checkBrowseMode = () => {
  if (userStore.user?.role === 'artisan' && sessionStorage.getItem('browse_as_user') === '1') {
    browseAsUser.value = true
  }
}

const exitBrowseMode = () => {
  sessionStorage.removeItem('browse_as_user')
  browseAsUser.value = false
  router.push('/artisan/dashboard')
}

const loadArtisanId = async () => {
  if (userStore.user?.role !== 'artisan') return
  try {
    const artisan = await artisanApi.getMy()
    artisanId.value = artisan.id
  } catch (err) {
    // ignore
  }
}

onMounted(() => {
  checkBrowseMode()
  loadArtisanId()
})

const handleLogout = () => {
  artisanId.value = null
  userStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--color-bg);
}

/* --- Header --- */
.header {
  background: var(--color-surface);
  box-shadow: 0 1px 8px rgba(58, 58, 58, 0.06);
  position: sticky;
  top: 0;
  z-index: 100;
  border-bottom: 1px solid var(--color-border-light);
}

.header-content {
  display: flex;
  align-items: center;
  height: 68px;
  gap: 48px;
}

/* Logo */
.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  white-space: nowrap;
  transition: opacity var(--transition-fast);
}

.logo:hover {
  opacity: 0.85;
}

.logo-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  background: var(--color-primary);
  color: #fff;
  font-size: 18px;
  font-weight: 600;
  border-radius: var(--radius-sm);
  letter-spacing: 1px;
}

.logo-text {
  font-size: 20px;
  font-weight: 600;
  color: var(--color-primary);
  letter-spacing: 2px;
}

/* Navigation */
.nav {
  display: flex;
  gap: 32px;
  flex: 1;
}

.nav-item {
  color: var(--color-text-secondary);
  font-size: 14px;
  font-weight: 500;
  transition: color var(--transition-fast);
  position: relative;
  padding: 4px 0;
}

.nav-item::after {
  content: '';
  position: absolute;
  bottom: -2px;
  left: 0;
  width: 0;
  height: 2px;
  background: var(--color-accent);
  transition: width var(--transition-base);
}

.nav-item:hover,
.nav-item.router-link-active {
  color: var(--color-primary);
}

.nav-item:hover::after,
.nav-item.router-link-active::after {
  width: 100%;
}

.nav-external {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.nav-external::after {
  display: none;
}

.nav-external:hover {
  color: var(--color-primary);
}

.nav-external .el-icon {
  font-size: 12px;
}

.nav-ai {
  cursor: pointer;
  color: var(--color-primary) !important;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.nav-ai:hover {
  color: var(--color-primary-light, #5a7a9a) !important;
}

/* Header Right */
.header-right {
  display: flex;
  align-items: center;
  gap: 20px;
}

.cart-link {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--color-text-secondary);
  transition: color var(--transition-fast);
}

.cart-link:hover {
  color: var(--color-primary);
}

.cart-text {
  font-size: 14px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: var(--radius-sm);
  transition: background var(--transition-fast);
}

.user-info:hover {
  background: var(--color-bg-warm);
}

.username {
  font-size: 14px;
  color: var(--color-text);
  font-weight: 500;
}

.btn-login,
.btn-register {
  padding: 8px 20px;
  border-radius: var(--radius-sm);
  font-size: 14px;
  font-weight: 500;
  transition: all var(--transition-base);
}

.btn-login {
  color: var(--color-primary);
  background: transparent;
  border: 1px solid var(--color-border);
}

.btn-login:hover {
  background: var(--color-bg-warm);
  border-color: var(--color-primary);
}

.btn-register {
  background: var(--color-primary);
  color: #fff;
  border: 1px solid var(--color-primary);
}

.btn-register:hover {
  background: var(--color-primary-light);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(59, 79, 107, 0.2);
}

/* --- Main Content --- */
.main {
  flex: 1;
}

/* --- Responsive --- */
@media (max-width: 768px) {
  .header-content {
    gap: 16px;
    height: 56px;
  }

  .logo-text {
    font-size: 16px;
  }

  .logo-icon {
    width: 28px;
    height: 28px;
    font-size: 14px;
  }

  .nav {
    gap: 16px;
  }

  .nav-item {
    font-size: 13px;
  }

  .cart-text {
    display: none;
  }

  .username {
    display: none;
  }
}
</style>
