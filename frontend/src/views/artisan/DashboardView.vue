<template>
  <MainLayout>
    <div class="dashboard">
      <h2 class="page-title">匠人中心</h2>

      <!-- 核心数据卡片 -->
      <div class="stat-cards">
        <div class="stat-card">
          <div class="stat-icon" style="background: #ecf5ff; color: #4f6ef7;">
            <el-icon :size="22"><Goods /></el-icon>
          </div>
          <div class="stat-body">
            <div class="stat-label">在售商品</div>
            <div class="stat-value">{{ stats.products }}</div>
          </div>
        </div>

        <el-tooltip placement="bottom" effect="light" :show-after="300">
          <template #content>
            <div class="tooltip-table">
              <div class="tooltip-row"><span>商品订单</span><span>{{ stats.today_orders_product }} 单</span></div>
              <div class="tooltip-row"><span>课程订单</span><span>{{ stats.today_orders_course }} 单</span></div>
              <div class="tooltip-row"><span>定制订单</span><span>{{ stats.today_orders_custom || 0 }} 单</span></div>
            </div>
          </template>
          <div class="stat-card clickable">
            <div class="stat-icon" style="background: #fef0f0; color: #f56c6c;">
              <el-icon :size="22"><Document /></el-icon>
            </div>
            <div class="stat-body">
              <div class="stat-label">今日订单</div>
              <div class="stat-value">{{ stats.today_orders }}</div>
            </div>
          </div>
        </el-tooltip>

        <el-tooltip placement="bottom" effect="light" :show-after="300">
          <template #content>
            <div class="tooltip-table">
              <div class="tooltip-row"><span>商品营收</span><span>¥{{ fmt(stats.today_revenue_product) }}</span></div>
              <div class="tooltip-row"><span>课程营收</span><span>¥{{ fmt(stats.today_revenue_course) }}</span></div>
              <div class="tooltip-row"><span>定制营收</span><span>¥{{ fmt(stats.today_revenue_custom) }}</span></div>
            </div>
          </template>
          <div class="stat-card clickable">
            <div class="stat-icon" style="background: #fdf6ec; color: #e6a23c;">
              <el-icon :size="22"><Money /></el-icon>
            </div>
            <div class="stat-body">
              <div class="stat-label">今日营收</div>
              <div class="stat-value">¥{{ fmt(stats.today_revenue) }}</div>
            </div>
          </div>
        </el-tooltip>

        <div class="stat-card">
          <div class="stat-icon" style="background: #fef0f0; color: #f56c6c;">
            <el-icon :size="22"><Clock /></el-icon>
          </div>
          <div class="stat-body">
            <div class="stat-label">待处理订单</div>
            <div class="stat-value">{{ stats.pending_orders }}</div>
          </div>
        </div>

        <el-tooltip placement="bottom" effect="light" :show-after="300">
          <template #content>
            <div class="tooltip-table">
              <div class="tooltip-row"><span>商品营收</span><span>¥{{ fmt(stats.total_revenue_product) }}</span></div>
              <div class="tooltip-row"><span>课程营收</span><span>¥{{ fmt(stats.total_revenue_course) }}</span></div>
              <div class="tooltip-row"><span>定制营收</span><span>¥{{ fmt(stats.total_revenue_custom) }}</span></div>
            </div>
          </template>
          <div class="stat-card clickable">
            <div class="stat-icon" style="background: #f0f9eb; color: #67c23a;">
              <el-icon :size="22"><TrendCharts /></el-icon>
            </div>
            <div class="stat-body">
              <div class="stat-label">累计总营收</div>
              <div class="stat-value">¥{{ fmt(stats.total_revenue) }}</div>
            </div>
          </div>
        </el-tooltip>
      </div>

      <!-- 快捷操作 -->
      <div class="card section">
        <h3 class="section-title">快捷操作</h3>
        <div class="quick-actions">
          <el-button @click="$router.push('/artisan/products')">管理商品</el-button>
          <el-button @click="$router.push('/artisan/orders')">订单管理</el-button>
          <el-button @click="$router.push('/artisan/custom')">定制需求</el-button>
          <el-button @click="$router.push('/artisan/settings')">店铺设置</el-button>
        </div>
      </div>

      <!-- 图表区域 -->
      <div class="charts-row">
        <!-- 营收趋势 -->
        <div class="card chart-card">
          <div class="chart-header">
            <h3 class="section-title">营收趋势</h3>
            <el-radio-group v-model="period" size="small" @change="loadDashboard">
              <el-radio-button value="today">今日</el-radio-button>
              <el-radio-button value="7d">近7日</el-radio-button>
              <el-radio-button value="30d">近30日</el-radio-button>
            </el-radio-group>
          </div>
          <div v-if="hasRevenueData" ref="revenueChartRef" class="chart-box"></div>
          <el-empty v-else description="暂无营收数据" :image-size="80" />
          <div class="chart-legend">
            <span class="legend-item"><i class="dot" style="background:#4f6ef7"></i>商品</span>
            <span class="legend-item"><i class="dot" style="background:#67c23a"></i>课程</span>
            <span class="legend-item"><i class="dot" style="background:#e6a23c"></i>定制</span>
          </div>
        </div>

        <!-- 订单趋势 -->
        <div class="card chart-card">
          <div class="chart-header">
            <h3 class="section-title">订单趋势</h3>
            <el-radio-group v-model="period" size="small" @change="loadDashboard">
              <el-radio-button value="today">今日</el-radio-button>
              <el-radio-button value="7d">近7日</el-radio-button>
              <el-radio-button value="30d">近30日</el-radio-button>
            </el-radio-group>
          </div>
          <div v-if="hasOrderData" ref="orderChartRef" class="chart-box"></div>
          <el-empty v-else description="暂无订单数据" :image-size="80" />
          <div class="chart-legend">
            <span class="legend-item"><i class="dot" style="background:#4f6ef7"></i>商品</span>
            <span class="legend-item"><i class="dot" style="background:#67c23a"></i>课程</span>
            <span class="legend-item"><i class="dot" style="background:#e6a23c"></i>定制</span>
          </div>
        </div>
      </div>
    </div>
  </MainLayout>
</template>

<script setup>
import { ref, onMounted, nextTick, computed } from 'vue'
import * as echarts from 'echarts'
import MainLayout from '@/components/MainLayout.vue'
import { artisanApi } from '@/api/modules'
import { Goods, Document, Money, Clock, TrendCharts } from '@element-plus/icons-vue'

const stats = ref({
  products: 0,
  today_orders: 0,
  today_orders_product: 0,
  today_orders_course: 0,
  today_orders_custom: 0,
  today_revenue: 0,
  today_revenue_product: 0,
  today_revenue_course: 0,
  today_revenue_custom: 0,
  pending_orders: 0,
  total_revenue: 0,
  total_revenue_product: 0,
  total_revenue_course: 0,
  total_revenue_custom: 0,
  revenue_trend: [],
  order_trend: [],
})

const period = ref('7d')
const revenueChartRef = ref(null)
const orderChartRef = ref(null)
let revenueChart = null
let orderChart = null

const fmt = (v) => (Number(v) || 0).toFixed(2)

const hasRevenueData = computed(() =>
  stats.value.revenue_trend?.some(d => d.product > 0 || d.course > 0 || (d.custom || 0) > 0)
)
const hasOrderData = computed(() =>
  stats.value.order_trend?.some(d => d.product > 0 || d.course > 0 || (d.custom || 0) > 0)
)

const loadDashboard = async () => {
  try {
    const res = await artisanApi.getDashboard({ period: period.value })
    stats.value = res
    await nextTick()
    renderCharts()
  } catch (err) {
    console.error('加载仪表盘数据失败:', err)
  }
}

const makeOption = (data, title) => ({
  tooltip: {
    trigger: 'axis',
    backgroundColor: '#fff',
    borderColor: '#eee',
    textStyle: { color: '#333', fontSize: 12 },
    formatter: (params) => {
      let html = `<b>${params[0].axisValue}</b><br/>`
      params.forEach(p => {
        html += `<span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:${p.color};margin-right:4px"></span>${p.seriesName}: ${p.value}<br/>`
      })
      return html
    },
  },
  legend: { show: false },
  grid: { top: 10, right: 16, bottom: 10, left: 40 },
  xAxis: {
    type: 'category',
    data: data.map(d => d.date),
    axisLine: { lineStyle: { color: '#e0e0e0' } },
    axisTick: { show: false },
    axisLabel: { color: '#999', fontSize: 11 },
  },
  yAxis: {
    type: 'value',
    splitLine: { lineStyle: { color: '#f0f0f0', type: 'dashed' } },
    axisLabel: { color: '#999', fontSize: 11 },
  },
  series: [
    {
      name: '商品',
      type: title === '营收' ? 'line' : 'bar',
      data: data.map(d => d.product),
      smooth: true,
      itemStyle: { color: '#4f6ef7', borderRadius: [4, 4, 0, 0] },
      lineStyle: { width: 2 },
      symbol: 'circle',
      symbolSize: 4,
    },
    {
      name: '课程',
      type: title === '营收' ? 'line' : 'bar',
      data: data.map(d => d.course),
      smooth: true,
      itemStyle: { color: '#67c23a', borderRadius: [4, 4, 0, 0] },
      lineStyle: { width: 2 },
      symbol: 'circle',
      symbolSize: 4,
    },
    {
      name: '定制',
      type: title === '营收' ? 'line' : 'bar',
      data: data.map(d => d.custom || 0),
      smooth: true,
      itemStyle: { color: '#e6a23c', borderRadius: [4, 4, 0, 0] },
      lineStyle: { width: 2 },
      symbol: 'circle',
      symbolSize: 4,
    },
  ],
})

const renderCharts = () => {
  if (revenueChartRef.value && hasRevenueData.value) {
    if (!revenueChart) revenueChart = echarts.init(revenueChartRef.value)
    revenueChart.setOption(makeOption(stats.value.revenue_trend, '营收'))
  }
  if (orderChartRef.value && hasOrderData.value) {
    if (!orderChart) orderChart = echarts.init(orderChartRef.value)
    orderChart.setOption(makeOption(stats.value.order_trend, '订单'))
  }
}

const handleResize = () => {
  revenueChart?.resize()
  orderChart?.resize()
}

onMounted(async () => {
  await loadDashboard()
  window.addEventListener('resize', handleResize)
})
</script>

<style scoped>
.dashboard {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.page-title {
  font-size: 22px;
  font-weight: 600;
  color: #333;
  margin: 0 0 20px;
}

/* 数据卡片 */
.stat-cards {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}

.stat-card {
  background: #fff;
  border-radius: 10px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 14px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  transition: transform 0.2s, box-shadow 0.2s;
}

.stat-card.clickable {
  cursor: pointer;
}

.stat-card.clickable:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0,0,0,0.08);
}

.stat-icon {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stat-body {
  flex: 1;
  min-width: 0;
}

.stat-label {
  font-size: 13px;
  color: #999;
  margin-bottom: 4px;
}

.stat-value {
  font-size: 22px;
  font-weight: 700;
  color: #333;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 通用区块 */
.card {
  background: #fff;
  border-radius: 10px;
  padding: 20px 24px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}

.section {
  margin-bottom: 20px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin: 0;
}

/* 快捷操作 */
.quick-actions {
  display: flex;
  gap: 12px;
  margin-top: 14px;
  flex-wrap: wrap;
}

/* 图表 */
.charts-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 20px;
}

.chart-card {
  padding: 20px 24px;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.chart-box {
  height: 280px;
}

.chart-legend {
  display: flex;
  justify-content: center;
  gap: 20px;
  margin-top: 8px;
}

.legend-item {
  font-size: 12px;
  color: #999;
  display: flex;
  align-items: center;
  gap: 6px;
}

.dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

/* Tooltip */
.tooltip-table {
  font-size: 12px;
}

.tooltip-row {
  display: flex;
  justify-content: space-between;
  gap: 24px;
  padding: 2px 0;
  color: #666;
}

.tooltip-row span:last-child {
  font-weight: 600;
  color: #333;
}

/* 响应式 */
@media (max-width: 1100px) {
  .stat-cards {
    grid-template-columns: repeat(3, 1fr);
  }
  .charts-row {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 700px) {
  .stat-cards {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 480px) {
  .stat-cards {
    grid-template-columns: 1fr;
  }
}
</style>