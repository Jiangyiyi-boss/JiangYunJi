<template>
  <MainLayout>
    <div class="container">
      <h2 class="page-title">订单管理</h2>

      <!-- 筛选栏：订单类型在下拉框 + 订单状态 -->
      <div class="filter-bar">
        <div class="filter-type">
          <span class="filter-label">订单类型</span>
          <el-select v-model="filterGoodsType" @change="loadOrders" style="width: 140px" placeholder="全部订单">
            <el-option :value="null" label="全部订单" />
            <el-option :value="1" label="商品订单" />
            <el-option :value="2" label="课程订单" />
            <el-option value="custom" label="定制订单" />
          </el-select>
        </div>
        <!-- 商品订单 -->
        <el-radio-group v-model="filterStatus" @change="loadOrders" v-if="filterGoodsType === 1 || filterGoodsType === null">
          <el-radio-button value="">全部</el-radio-button>
          <el-radio-button value="pending">待付款</el-radio-button>
          <el-radio-button value="paid">待发货</el-radio-button>
          <el-radio-button value="shipped">待收货</el-radio-button>
          <el-radio-button value="completed">已完成</el-radio-button>
        </el-radio-group>
        <!-- 课程订单 -->
        <el-radio-group v-model="filterStatus" @change="loadOrders" v-if="filterGoodsType === 2">
          <el-radio-button value="">全部</el-radio-button>
          <el-radio-button value="pending">待付款</el-radio-button>
          <el-radio-button value="completed">已完成</el-radio-button>
        </el-radio-group>
      </div>

      <div class="card">
        <el-table :data="orders" style="width: 100%" v-loading="loading">
          <el-table-column prop="order_no" label="订单号" width="200">
            <template #default="{ row }">
              {{ row.order_no || `CUSTOM-${row.id}` }}
            </template>
          </el-table-column>

          <!-- 商品 / 课程名称（按行自适应） -->
          <el-table-column v-if="filterGoodsType !== 'custom'" label="商品 / 课程" min-width="220">
            <template #default="{ row }">
              <div v-for="item in row.items" :key="item.id" class="order-item">
                <span>{{ item.product_name }}</span>
                <span v-if="row.goods_type === 1" class="item-qty">×{{ item.qty }}</span>
                <span class="item-price">¥{{ item.subtotal?.toFixed(2) }}</span>
              </div>
            </template>
          </el-table-column>

          <!-- 定制订单：需求描述 -->
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
          <el-table-column v-if="filterGoodsType === 'custom'" label="需求描述" min-width="180">
            <template #default="{ row }">
              <span>{{ row.description }}</span>
            </template>
          </el-table-column>

          <el-table-column label="订单金额" width="100">
            <template #default="{ row }">
              ¥{{ parseFloat(row.pay_amount || row.quote_amount || 0).toFixed(2) }}
            </template>
          </el-table-column>
          <el-table-column v-if="filterGoodsType !== 'custom'" label="佣金" width="90">
            <template #default="{ row }">
              <span style="color: #e6a23c">-¥{{ row.commission_amount?.toFixed(2) }}</span>
            </template>
          </el-table-column>
          <el-table-column v-if="filterGoodsType !== 'custom'" label="实收金额" width="100">
            <template #default="{ row }">
              <span style="color: #67c23a; font-weight: bold">¥{{ getActualIncome(row).toFixed(2) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="90">
            <template #default="{ row }">
              <el-tag :type="statusType(row)">{{ statusText(row) }}</el-tag>
            </template>
          </el-table-column>

          <!-- 收货信息 — 仅实物订单可见 -->
          <el-table-column v-if="filterGoodsType !== 2 && filterGoodsType !== 'custom'" label="收货信息" min-width="200">
            <template #default="{ row }">
              <template v-if="row.goods_type !== 2">
                <div class="receiver-info">
                  <div><strong>{{ row.receiver_name }}</strong> {{ row.receiver_phone }}</div>
                  <div class="receiver-address">{{ row.receiver_address }}</div>
                </div>
              </template>
              <span v-else class="text-muted">-</span>
            </template>
          </el-table-column>

          <el-table-column v-if="filterGoodsType !== 'custom'" label="支付方式" width="90">
            <template #default="{ row }">{{ payMethodLabel(row.pay_method) }}</template>
          </el-table-column>
          <el-table-column prop="created_at" label="下单时间" width="170" />

          <!-- 操作 -->
          <el-table-column label="操作" width="120" fixed="right">
            <template #default="{ row }">
              <template v-if="filterGoodsType !== 'custom'">
                <el-button v-if="row.goods_type === 1 && row.status === 'paid'" type="primary" size="small" @click="handleShip(row.id)">
                  发货
                </el-button>
                <el-tag v-else-if="row.goods_type === 1 && row.status === 'shipped'" type="primary" size="small">已发货</el-tag>
                <el-tag v-else-if="row.goods_type === 1 && row.status === 'completed'" type="success" size="small">已完成</el-tag>
                <PaymentCountdown
                  v-if="row.status === 'pending' && row.payment_started_at"
                  :payment-started-at="row.payment_started_at"
                />
                <el-tag v-else-if="row.goods_type === 2 && row.status === 'completed'" type="success" size="small">已完成</el-tag>
                <span v-else-if="row.goods_type === 2" class="text-muted">-</span>
                <span v-if="!row.goods_type || (row.goods_type === 1 && !['paid','shipped','completed'].includes(row.status) && row.status !== 'pending')" class="text-muted">-</span>
              </template>
              <template v-else>
                <template v-if="row.status === 'accepted' && row.pay_status !== 'paid'">
                  <span style="color:#e6a23c;font-size:13px">待付款</span>
                  <PaymentCountdown
                    v-if="row.payment_started_at"
                    :payment-started-at="row.payment_started_at"
                    style="margin-left:4px"
                  />
                </template>
                <template v-else-if="row.pay_status === 'paid' && row.status !== 'shipped' && row.status !== 'completed'">
                  <span style="color:#e6a23c;font-size:13px">待发货</span>
                </template>
                <template v-else-if="row.status === 'shipped'">
                  <span style="color:#409eff;font-size:13px">待收货</span>
                </template>
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
import { artisanApi } from '@/api/modules'
import { ElMessage } from 'element-plus'

const router = useRouter()
const orders = ref([])
const loading = ref(false)
const filterStatus = ref('')
const filterGoodsType = ref(null)

const statusText = (row) => {
  const s = typeof row === 'string' ? row : row.status
  const gt = typeof row === 'string' ? null : row.goods_type
  if (gt === 2) {
    return { pending: '待付款', paid: '已完成', completed: '已完成', cancelled: '已取消' }[s] || s
  }
  return { pending: '待付款', paid: '待发货', shipped: '待收货', completed: '已完成',
    cancelled: '已取消',
    quoted: '已报价', accepted: '已接受', in_progress: '制作中', rejected: '已拒绝',
  }[s] || s
}

const statusType = (row) => {
  const s = typeof row === 'string' ? row : row.status
  const gt = typeof row === 'string' ? null : row.goods_type
  if (gt === 2) {
    return { pending: 'danger', completed: 'success', cancelled: 'info' }[s] || ''
  }
  return { pending: 'danger', paid: 'warning', shipped: 'primary', completed: 'success',
    cancelled: 'info',
    quoted: '', accepted: 'primary', in_progress: 'primary', rejected: 'danger',
  }[s] || ''
}

const payMethodLabel = (m) => m === 'alipay' ? '支付宝' : m || '-'

const getActualIncome = (row) => {
  const total = row.pay_amount || 0
  const commission = row.commission_amount || 0
  return total - commission
}

const loadOrders = async () => {
  loading.value = true
  try {
    if (filterGoodsType.value === 'custom') {
      const res = await artisanApi.getCustomOrders({ skip: 0, limit: 50 })
      // 只显示已报价的订单（不含待处理和已拒绝）
      orders.value = (res.items || []).filter(o => o.status !== 'pending' && o.status !== 'rejected')
    } else {
      const params = { skip: 0, limit: 50 }
      if (filterStatus.value) {
        if (filterStatus.value === 'completed' && filterGoodsType.value === 2) {
          params.status = 'paid,completed'
        } else {
          params.status = filterStatus.value
        }
      }
      if (filterGoodsType.value !== null) params.goods_type = filterGoodsType.value
      const res = await artisanApi.getOrders(params)
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

const handleShip = async (id) => {
  try {
    await artisanApi.shipOrder(id)
    ElMessage.success('已发货')
    await loadOrders()
  } catch (err) {
    ElMessage.error('发货失败')
  }
}

const isPaymentExpired = (row) => {
  if (!row.payment_started_at) return false
  const elapsed = (Date.now() - new Date(row.payment_started_at).getTime()) / 1000
  return elapsed > 600
}

onMounted(() => {
  loadOrders()
})
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
.text-muted { color: #c0c4cc; }
.receiver-info { font-size: 13px; }
.receiver-address { color: #999; font-size: 12px; margin-top: 2px; }
</style>
