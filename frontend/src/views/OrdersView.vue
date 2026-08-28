<template>
  <MainLayout>
    <div class="container">
      <h2 class="page-title">我的订单</h2>

      <!-- 筛选栏 -->
      <div class="filter-bar">
        <div class="filter-type">
          <span class="filter-label">订单类型</span>
          <el-select v-model="filterGoodsType" @change="onGoodsTypeChange" style="width: 140px" placeholder="全部订单">
            <el-option :value="null" label="全部订单" />
            <el-option :value="1" label="商品订单" />
            <el-option :value="2" label="课程订单" />
            <el-option value="custom" label="定制订单" />
          </el-select>
        </div>
        <el-radio-group v-model="filterStatus" @change="loadOrders">
          <el-radio-button value="">全部</el-radio-button>

          <!-- 商品订单 / 全部订单 -->
          <template v-if="filterGoodsType === 1 || filterGoodsType === null">
            <el-radio-button value="pending">待付款</el-radio-button>
            <el-radio-button value="paid">待发货</el-radio-button>
            <el-radio-button value="shipped">待收货</el-radio-button>
            <el-radio-button value="completed">已完成</el-radio-button>
          </template>

          <!-- 课程订单 -->
          <template v-if="filterGoodsType === 2">
            <el-radio-button value="pending">待付款</el-radio-button>
            <el-radio-button value="completed">已完成</el-radio-button>
          </template>

          <!-- 定制订单 -->
          <template v-if="filterGoodsType === 'custom'">
            <el-radio-button value="pending">待付款</el-radio-button>
            <el-radio-button value="paid">待发货</el-radio-button>
            <el-radio-button value="shipped">待收货</el-radio-button>
            <el-radio-button value="completed">已完成</el-radio-button>
          </template>
        </el-radio-group>
      </div>

      <div class="card">
        <el-table :data="orders" style="width: 100%" v-loading="loading">
          <el-table-column prop="order_no" label="订单号" width="200" />

          <!-- 商品 / 课程名称 -->
          <el-table-column v-if="filterGoodsType !== 'custom'" label="商品 / 课程" min-width="220">
            <template #default="{ row }">
              <div v-for="item in row.items" :key="item.id" class="order-item">
                <span>{{ item.product_name }}</span>
                <span v-if="row.goods_type === 1" class="item-qty">×{{ item.qty }}</span>
                <span class="item-price">¥{{ item.subtotal?.toFixed(2) }}</span>
              </div>
            </template>
          </el-table-column>

          <!-- 定制订单：图片 -->
          <el-table-column v-if="filterGoodsType === 'custom'" label="定制图片" width="100">
            <template #default="{ row }">
              <el-image
                v-if="row.reference_images && row.reference_images.length"
                :src="row.reference_images[0]"
                :preview-src-list="row.reference_images"
                style="width: 60px; height: 60px; border-radius: 4px"
                fit="cover"
              />
              <span v-else style="color: #999">暂无</span>
            </template>
          </el-table-column>

          <el-table-column label="订单金额" width="110">
            <template #default="{ row }">
              ¥{{ (row.pay_amount || row.quote_amount || 0).toFixed ? (row.pay_amount || row.quote_amount || 0).toFixed(2) : (row.pay_amount || row.quote_amount || 0) }}
            </template>
          </el-table-column>
          <el-table-column label="状态" width="90">
            <template #default="{ row }">
              <el-tag :type="statusType(row)">
                {{ statusLabel(row) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="下单时间" width="170" />

          <!-- 操作 -->
          <el-table-column label="操作" width="180" fixed="right">
            <template #default="{ row }">
              <template v-if="filterGoodsType !== 'custom'">
                <!-- 待付款 (未超时): 付款 + 取消 -->
                <template v-if="row.status === 'pending' && !isPaymentExpired(row)">
                  <div class="action-row">
                    <el-button type="primary" size="small" @click="payOrder(row.id)" class="pay-btn">
                      付款
                      <PaymentCountdown
                        v-if="row.payment_started_at"
                        :payment-started-at="row.payment_started_at"
                        @expired="handleExpired(row)"
                      />
                    </el-button>
                    <el-button type="danger" size="small" plain @click="cancelOrder(row.id)">取消</el-button>
                  </div>
                </template>
                <!-- 待付款 (已超时): 自动取消，只显示已超时 -->
                <template v-if="row.status === 'pending' && isPaymentExpired(row)">
                  <span class="text-muted">已超时</span>
                </template>
                <!-- 待发货: 仅状态标签 -->
                <template v-if="row.status === 'paid'">
                  <span class="text-muted">待发货</span>
                </template>
                <!-- 待收货: 确认收货按钮 -->
                <template v-else-if="row.status === 'shipped'">
                  <el-button type="success" size="small" @click="completeOrder(row.id)">确认收货</el-button>
                </template>
                <!-- 已完成 -->
                <template v-else-if="row.status === 'completed'">
                  <span class="text-muted">已完成</span>
                </template>
                <!-- 已取消 -->
                <template v-else-if="row.status === 'cancelled'">
                  <span class="text-muted">已取消</span>
                </template>
              </template>
              <template v-else>
                <el-button
                  v-if="row.status === 'accepted' && row.pay_status !== 'paid'"
                  type="danger" size="small" @click="payCustomOrder(row)"
                >付款</el-button>
                <PaymentCountdown
                  v-if="row.status === 'accepted' && row.pay_status !== 'paid' && row.payment_started_at"
                  :payment-started-at="row.payment_started_at"
                  style="margin-left:4px"
                  @expired="handleExpired(row)"
                />
                <el-button
                  v-else-if="row.status === 'shipped'"
                  type="success" size="small" @click="confirmCustomOrder(row)"
                >确认收货</el-button>
                <el-tag v-else-if="row.pay_status === 'paid' && row.status !== 'shipped'" type="warning" size="small">待发货</el-tag>
                <el-tag v-else-if="row.status === 'completed'" type="success" size="small">已完成</el-tag>
                <span v-else class="text-muted">-</span>
              </template>
            </template>
          </el-table-column>
        </el-table>
        <el-empty v-if="!loading && !orders.length" description="暂无订单" />
      </div>
    </div>
  </MainLayout>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import MainLayout from '@/components/MainLayout.vue'
import PaymentCountdown from '@/components/PaymentCountdown.vue'
import { orderApi, artisanApi } from '@/api/modules'
import { ElMessage } from 'element-plus'

const router = useRouter()
const orders = ref([])
const loading = ref(false)
const filterStatus = ref('')
const filterGoodsType = ref(null)

const statusLabel = (row) => {
  const s = row.status
  // 课程订单
  if (row.goods_type === 2) {
    return { pending: '待付款', paid: '已完成', completed: '已完成', cancelled: '已取消' }[s] || s
  }
  // 商品订单
  if (row.goods_type === 1) {
    return { pending: '待付款', paid: '待发货', shipped: '待收货', completed: '已完成', cancelled: '已取消' }[s] || s
  }
  // 默认（含定制订单）
  return { pending: '待付款', paid: '待发货', shipped: '待收货', completed: '已完成', cancelled: '已取消',
    accepted: '待付款', quoted: '已报价', in_progress: '制作中', rejected: '已拒绝' }[s] || s
}

const statusType = (row) => {
  const s = row.status || row
  return { pending: 'danger', paid: 'warning', shipped: 'primary', completed: 'success', cancelled: 'info',
    accepted: 'danger', quoted: '', in_progress: 'primary', rejected: 'danger' }[s] || ''
}

const loadOrders = async () => {
  loading.value = true
  try {
    if (filterGoodsType.value === 'custom') {
      const res = await artisanApi.getCustomOrders({ skip: 0, limit: 50 })
      let items = res.items || []

      // 定制订单状态筛选
      if (filterStatus.value === 'pending') {
        items = items.filter(o => o.status === 'accepted' && o.pay_status !== 'paid' && !isPaymentExpired(o))
      } else if (filterStatus.value === 'paid') {
        items = items.filter(o => o.pay_status === 'paid' && o.status !== 'shipped' && o.status !== 'completed')
      } else if (filterStatus.value === 'shipped') {
        items = items.filter(o => o.status === 'shipped')
      } else if (filterStatus.value) {
        items = items.filter(o => o.status === filterStatus.value)
      }
      orders.value = items
    } else {
      const params = { skip: 0, limit: 50 }
      if (filterStatus.value) {
        // 课程订单的"已完成"包含 paid 和 completed（兼容旧数据）
        if (filterStatus.value === 'completed' && filterGoodsType.value === 2) {
          params.status = 'paid,completed'
        } else {
          params.status = filterStatus.value
        }
      }
      if (filterGoodsType.value !== null) params.goods_type = filterGoodsType.value
      const res = await orderApi.getOrders(params)
      let items = res.items || []
      // "待付款"筛选：排除已超时的订单
      if (filterStatus.value === 'pending') {
        items = items.filter(o => !isPaymentExpired(o))
      }
      orders.value = items
    }
  } catch (err) {
    ElMessage.error('加载订单失败')
  } finally {
    loading.value = false
  }
}

const onGoodsTypeChange = () => {
  filterStatus.value = ''
  loadOrders()
}

const isPaymentExpired = (row) => {
  if (!row.payment_started_at) return false
  const elapsed = (Date.now() - new Date(row.payment_started_at).getTime()) / 1000
  return elapsed > 600 // 10分钟超时
}

onMounted(loadOrders)

const payOrder = (id) => {
  router.push(`/pay/${id}`)
}

const payCustomOrder = (row) => {
  router.push(`/custom-checkout/${row.id}`)
}

const confirmCustomOrder = async (row) => {
  try {
    await artisanApi.completeCustomOrder(row.id)
    ElMessage.success('已确认收货')
    loadOrders()
  } catch (err) {
    ElMessage.error('操作失败')
  }
}

const cancelOrder = async (id) => {
  try {
    await orderApi.cancelOrder(id)
    ElMessage.success('已取消')
    loadOrders()
  } catch (err) {
    ElMessage.error(err.detail || '取消失败')
  }
}

const handleExpired = async (row) => {
  // 倒计时结束时自动取消订单
  if (row.status === 'pending' || row.status === 'accepted') {
    try {
      await orderApi.cancelOrder(row.id)
      ElMessage.warning('订单已超时，已自动取消')
      loadOrders()
    } catch (err) {
      // 可能已被后端取消，刷新即可
      loadOrders()
    }
  }
}

const completeOrder = async (id) => {
  try {
    await orderApi.completeOrder(id)
    ElMessage.success('已确认收货')
    loadOrders()
  } catch (err) {
    ElMessage.error(err.detail || '操作失败')
  }
}

</script>

<style scoped>
.page-title { margin: 20px 0; font-size: 22px; }

.filter-bar {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 16px;
}

.filter-type {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-label {
  font-size: 14px;
  color: #606266;
  font-weight: 500;
  white-space: nowrap;
}

.order-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 2px 0;
}
.item-qty { color: #999; font-size: 13px; }
.item-price { color: #f56c6c; margin-left: auto; font-weight: 500; }
.text-muted { color: #c0c4cc; font-size: 13px; }

.action-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: nowrap;
}

.pay-btn :deep(.countdown) {
  color: #fff;
  margin-left: 4px;
  font-size: 12px;
}
</style>
