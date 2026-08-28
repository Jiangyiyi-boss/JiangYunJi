<template>
  <div class="dashboard">
    <h2 class="page-title">数据概览</h2>

    <!-- 交易数据 + 平台收入 (同一卡片，左右两列) -->
    <div class="card section-card">
      <el-row :gutter="40">
        <el-col :span="12">
          <div class="section-header">
            <el-icon class="section-icon"><ShoppingCart /></el-icon>
            <span>交易数据</span>
          </div>
          <div class="stats-grid">
            <div class="stat-item">
              <span class="stat-label">今日销售额</span>
              <span class="stat-value">¥{{ formatNum(stats.today_sales) }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">总销售额</span>
              <span class="stat-value">¥{{ formatNum(stats.total_sales) }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">今日订单</span>
              <span class="stat-value">{{ stats.today_orders || 0 }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">总订单数</span>
              <span class="stat-value">{{ stats.total_orders || 0 }}</span>
            </div>
          </div>
        </el-col>
        <el-col :span="12">
          <div class="section-header">
            <el-icon class="section-icon"><Coin /></el-icon>
            <span>平台收入</span>
          </div>
          <div class="stats-grid">
            <div class="stat-item">
              <span class="stat-label">今日佣金收入</span>
              <span class="stat-value">¥{{ formatNum(stats.today_commission) }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">平台总收入</span>
              <span class="stat-value income-value">¥{{ formatNum(stats.total_income) }}</span>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 平台增长 -->
    <div class="card section-card">
      <div class="section-header">
        <el-icon class="section-icon"><TrendCharts /></el-icon>
        <span>平台增长</span>
      </div>
      <div class="stats-row">
        <div class="stat-inline">
          <span class="stat-label">今日新增用户</span>
          <span class="stat-value">{{ stats.today_new_users || 0 }}</span>
        </div>
        <span class="divider">|</span>
        <div class="stat-inline">
          <span class="stat-label">今日新增商家</span>
          <span class="stat-value">{{ stats.today_new_artisans || 0 }}</span>
        </div>
        <span class="divider">|</span>
        <div class="stat-inline">
          <span class="stat-label">总用户</span>
          <span class="stat-value">{{ stats.total_users || 0 }}</span>
        </div>
        <span class="divider">|</span>
        <div class="stat-inline">
          <span class="stat-label">总商家</span>
          <span class="stat-value">{{ stats.total_artisans || 0 }}</span>
        </div>
      </div>
    </div>

    <!-- 待处理任务 -->
    <div class="card section-card">
      <div class="section-header">
        <el-icon class="section-icon"><Clock /></el-icon>
        <span>待处理任务</span>
      </div>
      <div class="stats-row">
        <div class="stat-inline">
          <span class="stat-label">待审核商家</span>
          <span class="stat-value" :class="stats.pending_artisans > 0 ? 'warning-value' : ''">{{ stats.pending_artisans || 0 }}</span>
        </div>
        <span class="divider">|</span>
        <div class="stat-inline">
          <span class="stat-label">待审核商品</span>
          <span class="stat-value" :class="stats.pending_products > 0 ? 'warning-value' : ''">{{ stats.pending_products || 0 }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ShoppingCart, Coin, TrendCharts, Clock } from '@element-plus/icons-vue'
import { adminApi } from '@/api/modules'

const stats = ref({})

const formatNum = (val) => {
  if (!val && val !== 0) return '0.00'
  return Number(val).toFixed(2)
}

onMounted(async () => {
  try {
    stats.value = await adminApi.getStats()
  } catch (err) {
    console.error('加载统计数据失败', err)
  }
})
</script>

<style scoped>
.dashboard {
  max-width: 900px;
}
.page-title {
  margin: 0 0 20px;
  font-size: 20px;
}
.section-card {
  margin-bottom: 16px;
}
.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 16px;
  padding-bottom: 10px;
  border-bottom: 1px solid #ebeef5;
}
.section-icon {
  font-size: 18px;
  color: #409eff;
}
.stats-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}
.stat-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 10px 0;
}
.stat-label {
  font-size: 13px;
  color: #909399;
}
.stat-value {
  font-size: 20px;
  font-weight: 600;
  color: #303133;
}
.income-value {
  color: #67c23a;
}
.warning-value {
  color: #e6a23c;
}
.stats-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}
.stat-inline {
  display: flex;
  align-items: center;
  gap: 8px;
}
.divider {
  color: #dcdfe6;
  font-size: 14px;
}
</style>
