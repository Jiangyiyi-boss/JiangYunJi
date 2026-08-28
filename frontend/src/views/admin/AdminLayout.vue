<template>
  <div class="admin-layout">
    <el-container>
      <el-aside width="220px" class="admin-aside">
        <div class="admin-logo">匠韵集 · 管理后台</div>
        <el-menu :default-active="activeMenu" router background-color="#304156" text-color="#bfcbd9" active-text-color="#409EFF">
          <el-menu-item index="/admin">
            <el-icon><DataBoard /></el-icon>
            <span>数据概览</span>
          </el-menu-item>
          <el-menu-item index="/admin/users">
            <el-icon><User /></el-icon>
            <span>用户管理</span>
          </el-menu-item>

          <el-sub-menu index="merchant">
            <template #title>
              <el-icon><Medal /></el-icon>
              <span>商家管理</span>
            </template>
            <el-menu-item index="/admin/merchant/applications">入驻审核</el-menu-item>
            <el-menu-item index="/admin/merchant/list">商家列表</el-menu-item>
          </el-sub-menu>

          <el-menu-item index="/admin/products">
            <el-icon><Goods /></el-icon>
            <span>商品审核</span>
          </el-menu-item>
          <el-menu-item index="/admin/orders">
            <el-icon><List /></el-icon>
            <span>订单管理</span>
          </el-menu-item>
          <el-menu-item index="/admin/commissions">
            <el-icon><Coin /></el-icon>
            <span>佣金管理</span>
          </el-menu-item>
          <el-menu-item index="/admin/banners">
            <el-icon><Picture /></el-icon>
            <span>轮播图管理</span>
          </el-menu-item>
          <el-menu-item index="/admin/categories">
            <el-icon><Menu /></el-icon>
            <span>分类管理</span>
          </el-menu-item>
          <el-menu-item index="/admin/courses">
            <el-icon><Reading /></el-icon>
            <span>课程审核</span>
          </el-menu-item>
          <el-menu-item index="/admin/forum">
            <el-icon><ChatLineSquare /></el-icon>
            <span>论坛管理</span>
          </el-menu-item>
        </el-menu>
        <div class="admin-logout">
          <el-button type="danger" text @click="handleLogout">
            <el-icon><SwitchButton /></el-icon>
            退出登录
          </el-button>
        </div>
      </el-aside>
      <el-main class="admin-main">
        <router-view />
      </el-main>
    </el-container>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const activeMenu = computed(() => route.path)

const handleLogout = () => {
  userStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.admin-layout {
  min-height: 100vh;
  background: #f0f2f5;
}

.admin-aside {
  background: #304156;
  min-height: 100vh;
}

.admin-logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 18px;
  font-weight: bold;
  background: #263445;
}

.admin-main {
  padding: 20px;
}

.admin-logout {
  position: absolute;
  bottom: 20px;
  left: 0;
  right: 0;
  text-align: center;
}

.admin-logout .el-button {
  color: #bfcbd9;
  font-size: 14px;
}

.admin-logout .el-button:hover {
  color: #f56c6c;
}
</style>
