<template>
  <MainLayout>
    <div class="container">
      <h2 class="page-title">定制服务</h2>

      <div class="filter-bar">
        <el-radio-group v-model="filterStatus" @change="loadOrders">
          <el-radio-button value="">全部</el-radio-button>
          <el-radio-button value="pending">待处理</el-radio-button>
          <el-radio-button value="quoted">已报价</el-radio-button>
          <el-radio-button value="paid">已支付</el-radio-button>
          <el-radio-button value="rejected">已拒绝</el-radio-button>
        </el-radio-group>
      </div>

      <div class="card" v-loading="loading">
        <el-empty v-if="!orders.length" description="暂无定制订单" />
        <div v-else class="order-list">
          <div v-for="order in orders" :key="order.id" class="order-card">
            <div class="order-header">
              <div class="order-meta">
                <el-tag :type="statusType(order.status)" size="small">{{ statusText(order.status) }}</el-tag>
                <el-tag v-if="order.pay_status === 'paid'" type="success" size="small">已付款</el-tag>
                <span class="order-time">{{ order.created_at?.slice(0, 10) }}</span>
              </div>
              <div class="order-budget" v-if="order.budget_min || order.budget_max">
                预算 ¥{{ order.budget_min || '?' }} - ¥{{ order.budget_max || '?' }}
              </div>
            </div>
            <p class="order-desc">{{ order.description }}</p>

            <div class="ref-images" v-if="order.reference_images?.length">
              <el-image
                v-for="(img, i) in order.reference_images"
                :key="i"
                :src="img"
                fit="cover"
                style="width:72px;height:72px;border-radius:6px;margin-right:8px"
                :preview-src-list="order.reference_images"
                :initial-index="i"
              />
            </div>

            <!-- 商家报价信息 -->
            <div class="quote-info" v-if="order.quote_amount">
              <div>报价 <strong>¥{{ order.quote_amount }}</strong></div>
              <div v-if="order.quote_deadline">预计工期 <strong>{{ order.quote_deadline }} 天</strong></div>
              <div v-if="order.quote_deadline && order.updated_at" class="est-delivery">
                预计交付：{{ estDelivery(order) }}
              </div>
            </div>

            <!-- 用户期望交付时间 -->
            <div class="deadline-info" v-if="order.deadline">
              <el-icon><Clock /></el-icon> 期望交付：{{ order.deadline }}
            </div>

            <!-- 拒绝理由 -->
            <div class="reject-info" v-if="order.status === 'rejected' && order.reject_reason">
              <div class="reject-reason">
                <strong>拒绝理由：</strong>{{ order.reject_reason }}
              </div>
              <div v-if="order.rejected_by === 'user'" class="reject-hint">
                商家可能会重新报价，请留意
              </div>
            </div>

            <div class="order-actions">
              <!-- 已报价：用户确认接受/拒绝 -->
              <template v-if="order.status === 'quoted'">
                <el-button type="success" size="small" @click="handleAccept(order)">接受报价</el-button>
                <el-button type="danger" size="small" plain @click="handleReject(order)">拒绝</el-button>
              </template>
              <!-- 已接受：未超时显示付款+倒计时，已超时显示重新支付+取消订单 -->
              <template v-else-if="order.status === 'accepted' && order.pay_status !== 'paid'">
                <template v-if="!isPaymentExpired(order)">
                  <el-button type="danger" size="small" @click="handlePay(order)">付款</el-button>
                  <PaymentCountdown
                    v-if="order.payment_started_at"
                    :payment-started-at="order.payment_started_at"
                    style="margin-left:4px"
                  />
                </template>
                <template v-else>
                  <el-button type="danger" size="small" @click="handlePay(order)">重新支付</el-button>
                  <el-button type="info" size="small" plain @click="handleCancel(order)">取消订单</el-button>
                </template>
              </template>
              <!-- 已发货：确认收货 -->
              <template v-else-if="order.status === 'shipped'">
                <el-button type="success" size="small" @click="handleConfirm(order)">确认收货</el-button>
              </template>
              <!-- 已支付/制作中/已完成 -->
              <template v-else-if="order.pay_status === 'paid' || order.status === 'in_progress' || order.status === 'completed'">
                <el-tag type="success" size="small">{{ order.status === 'completed' ? '已完成' : '已付款' }}</el-tag>
              </template>
            <!-- 已拒绝/已取消 -->
            <template v-else-if="order.status === 'rejected' || order.status === 'cancelled'">
              <span style="color:#c0c4cc;font-size:13px">已关闭</span>
            </template>
            </div>
          </div>
        </div>
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
import { ElMessage, ElMessageBox } from 'element-plus'
import { Clock } from '@element-plus/icons-vue'

const router = useRouter()
const orders = ref([])
const loading = ref(false)
const filterStatus = ref('')

const statusText = (s) => ({
  pending: '待处理', quoted: '已报价', accepted: '待付款', in_progress: '制作中',
  shipped: '待收货', completed: '已完成', rejected: '已拒绝', cancelled: '已取消',
}[s] || s)

const statusType = (s) => ({
  pending: 'warning', quoted: '', accepted: 'danger', in_progress: 'primary',
  shipped: 'primary', completed: 'success', rejected: 'danger', cancelled: 'info',
}[s] || '')

const estDelivery = (order) => {
  if (!order.quote_deadline || !order.updated_at) return ''
  const d = new Date(new Date(order.updated_at).getTime() + order.quote_deadline * 86400000)
  return d.toLocaleDateString('zh-CN')
}

const isPaymentExpired = (order) => {
  if (!order.payment_started_at) return false
  const elapsed = (Date.now() - new Date(order.payment_started_at).getTime()) / 1000
  return elapsed > 600 // 10分钟超时
}

const loadOrders = async () => {
  loading.value = true
  try {
    const res = await artisanApi.getCustomOrders({ skip: 0, limit: 50 })
    let items = res.items || []
    if (filterStatus.value === 'paid') {
      items = items.filter(o => o.pay_status === 'paid' || o.status === 'in_progress' || o.status === 'shipped')
    } else if (filterStatus.value === 'rejected') {
      items = items.filter(o => o.status === 'rejected' || o.status === 'cancelled')
    } else if (filterStatus.value) {
      items = items.filter(o => o.status === filterStatus.value)
    }
    orders.value = items
  } catch (err) {
    console.error(err)
  } finally {
    loading.value = false
  }
}

const handleAccept = async (order) => {
  try {
    await ElMessageBox.confirm(
      `报价 ¥${order.quote_amount}，工期 ${order.quote_deadline} 天，确认接受？`,
      '接受报价',
      { confirmButtonText: '接受', cancelButtonText: '再想想', type: 'info' }
    )
    await artisanApi.acceptCustomOrder(order.id)
    ElMessage.success('已接受报价，请尽快付款')
    loadOrders()
  } catch (err) {
    if (err !== 'cancel') ElMessage.error('操作失败')
  }
}

const handleReject = async (order) => {
  try {
    const { value: reason } = await ElMessageBox.prompt(
      `报价 ¥${order.quote_amount}，请输入拒绝原因（如：超出预算）`,
      '拒绝报价',
      {
        confirmButtonText: '确定拒绝',
        cancelButtonText: '取消',
        inputType: 'textarea',
        inputPlaceholder: '请输入拒绝原因',
      }
    )
    await artisanApi.rejectCustomOrder(order.id, reason || '')
    ElMessage.success('已拒绝报价')
    loadOrders()
  } catch (err) {
    if (err !== 'cancel') ElMessage.error('操作失败')
  }
}

const handlePay = (row) => {
  router.push(`/custom-checkout/${row.id}`)
}

const handleCancel = async (order) => {
  try {
    await ElMessageBox.confirm('确定取消该定制订单？取消后可在匠人店铺重新发起定制', '取消订单', {
      confirmButtonText: '确定取消',
      cancelButtonText: '再想想',
      type: 'warning',
    })
    await artisanApi.cancelCustomOrder(order.id)
    ElMessage.success('订单已取消')
    loadOrders()
  } catch (err) {
    if (err !== 'cancel') ElMessage.error('取消失败')
  }
}

const handleConfirm = async (row) => {
  try {
    await artisanApi.completeCustomOrder(row.id)
    ElMessage.success('已确认收货')
    loadOrders()
  } catch (err) {
    ElMessage.error('操作失败')
  }
}

onMounted(loadOrders)
</script>

<style scoped>
.page-title { margin: 20px 0; }
.filter-bar { margin-bottom: 16px; }
.card {
  background: #fff;
  border-radius: 12px;
  padding: 24px;
}
.order-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.order-card {
  border: 1px solid #f0f0f0;
  border-radius: 10px;
  padding: 16px 20px;
}
.order-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}
.order-meta {
  display: flex;
  align-items: center;
  gap: 10px;
}
.order-time {
  font-size: 12px;
  color: #bbb;
}
.order-budget {
  font-size: 13px;
  color: #f56c6c;
}
.order-desc {
  font-size: 14px;
  color: #333;
  margin: 0 0 12px;
  line-height: 1.6;
}
.ref-images {
  margin-bottom: 12px;
}
.quote-info {
  font-size: 14px;
  color: #666;
  margin-bottom: 8px;
  padding: 10px 12px;
  background: #f0f9eb;
  border-radius: 6px;
  border: 1px solid #e1f3d8;
  line-height: 1.8;
}
.quote-info strong {
  color: #f56c6c;
}
.est-delivery {
  font-size: 12px;
  color: #999;
}
.deadline-info {
  font-size: 13px;
  color: #e6a23c;
  display: flex;
  align-items: center;
  gap: 4px;
  margin-bottom: 12px;
}
.reject-info {
  margin-bottom: 12px;
  padding: 10px 12px;
  background: #fef0f0;
  border-radius: 6px;
  border: 1px solid #fde2e2;
}
.reject-reason {
  font-size: 14px;
  color: #f56c6c;
  margin-bottom: 4px;
}
.reject-hint {
  font-size: 12px;
  color: #999;
}
.order-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}
</style>
