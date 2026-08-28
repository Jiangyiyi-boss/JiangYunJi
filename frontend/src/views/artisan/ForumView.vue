<template>
  <div class="artisan-forum-wrapper">
    <div class="artisan-top-bar">
      <el-button text @click="$router.push('/artisan/dashboard')">
        <el-icon><ArrowLeft /></el-icon> 返回商家中心
      </el-button>
      <span class="bar-title">匠人雅集</span>
    </div>
    <ForumPage />
  </div>
</template>

<script setup>
import { ArrowLeft } from '@element-plus/icons-vue'
import ForumPage from '@/views/ForumView.vue'
</script>

<style scoped>
.artisan-forum-wrapper {
  min-height: 100vh;
}
.artisan-top-bar {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 8px 20px;
  background: #fff;
  border-bottom: 1px solid #eee;
  position: sticky;
  top: 0;
  z-index: 100;
}
.bar-title {
  font-size: 15px;
  font-weight: 600;
  color: #333;
}
</style>