<template>
  <MainLayout>
    <div class="container">
      <h2 class="page-title">我的</h2>

      <div
        v-for="item in allItems"
        :key="item.path"
        class="menu-row"
        @click="handleItemClick(item)"
      >
        <el-icon :size="24" :color="item.color"><component :is="item.icon" /></el-icon>
        <span class="menu-label">{{ item.label }}</span>
        <el-icon :size="16" color="#ccc"><ArrowRight /></el-icon>
      </div>
    </div>
  </MainLayout>
</template>

<script setup>
import MainLayout from '@/components/MainLayout.vue'
import { useUserStore } from '@/stores/user'
import { useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import {
  User, Tickets, Star, Location,
  Edit, School, Setting, Shop, Clock
} from '@element-plus/icons-vue'
import { ArrowRight } from '@element-plus/icons-vue'

const userStore = useUserStore()
const router = useRouter()

const allItems = [
  { label: '我的订单', path: '/orders', icon: 'Tickets', color: '#409eff' },
  { label: '我的收藏', path: '/favorites', icon: 'Star', color: '#e6a23c' },
  { label: '我的课程', path: '/my-courses', icon: 'School', color: '#67c23a' },
  { label: '浏览记录', path: '/browse-history', icon: 'Clock', color: '#e6a23c' },
  { label: '定制服务', path: '/custom', icon: 'Edit', color: '#909399', public: true },
  { label: '收货地址', path: '/addresses', icon: 'Location', color: '#409eff' },
  { label: '账号设置', path: '/profile', icon: 'User', color: '#67c23a' },
  ...(userStore.user?.role === 'admin' ? [{ label: '管理后台', path: '/admin', icon: 'Setting', color: '#f56c6c' }] : []),
  ...(userStore.user?.role !== 'artisan' ? [{ label: '商家入驻', path: '/artisan/apply', icon: 'Shop', color: '#e6a23c' }] : []),
]

const requireLogin = (item) => {
  ElMessageBox.confirm('请先登录，登录后方可操作', '提示', {
    confirmButtonText: '去登录',
    cancelButtonText: '取消',
    type: 'warning',
  }).then(() => {
    router.push({ path: '/login', query: { redirect: router.currentRoute.value.fullPath } })
  }).catch(() => {})
}

const handleItemClick = (item) => {
  if (!item.public && !userStore.token) {
    requireLogin(item)
    return
  }
  router.push(item.path)
}
</script>

<style scoped>
.page-title { margin: 20px 0; font-size: 22px; }

.menu-row {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px 20px;
  background: #fff;
  border-radius: 0;
  cursor: pointer;
  transition: background 0.15s;
  border-bottom: 1px solid #f5f5f5;
}
.menu-row:first-of-type {
  border-top: 1px solid #f5f5f5;
}
.menu-row:hover {
  background: #fafafa;
}

.menu-label {
  font-size: 15px;
  color: #333;
  font-weight: 500;
  flex: 1;
}
</style>