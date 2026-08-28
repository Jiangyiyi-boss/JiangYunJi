<template>
  <MainLayout>
    <div class="container">
      <h2 class="page-title">定制需求</h2>

      <div class="filter-bar">
        <el-radio-group v-model="filterStatus" @change="loadOrders">
          <el-radio-button value="">全部</el-radio-button>
          <el-radio-button value="pending">待处理</el-radio-button>
          <el-radio-button value="quoted|accepted">已报价</el-radio-button>
          <el-radio-button value="in_progress">制作中</el-radio-button>
          <el-radio-button value="completed">已完成</el-radio-button>
          <el-radio-button value="rejected">已拒绝</el-radio-button>
          <el-radio-button value="cancelled">已取消</el-radio-button>
        </el-radio-group>
      </div>

      <div class="card" v-loading="loading">
        <el-empty v-if="!orders.length" description="暂无定制需求" />
        <div v-else class="order-list">
          <div v-for="order in orders" :key="order.id" class="order-card">
            <div class="order-header">
              <div class="order-meta">
                <el-tag :type="statusType(order.status)" size="small">{{ statusLabel(order.status) }}</el-tag>
                <el-tag v-if="order.pay_status === 'paid'" type="success" size="small">已付款</el-tag>
                <el-tag v-else-if="order.status === 'accepted' || order.status === 'quoted'" type="warning" size="small">待付款</el-tag>
                <span class="order-time">{{ order.created_at?.slice(0, 10) }}</span>
              </div>
              <div class="order-budget" v-if="order.budget_min || order.budget_max">
                预算 ¥{{ order.budget_min || '?' }} - ¥{{ order.budget_max || '?' }}
              </div>
            </div>
            <p class="order-desc">{{ order.description }}</p>

            <!-- 用户期望交付时间 -->
            <div class="deadline-info" v-if="order.deadline">
              <el-icon><Clock /></el-icon> 用户期望交付：{{ order.deadline }}
            </div>

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

            <div class="quote-info" v-if="order.quote_amount">
              <span>报价 <strong>¥{{ order.quote_amount }}</strong></span>
              <span v-if="order.quote_deadline"> · 工期 {{ order.quote_deadline }} 天</span>
            </div>

            <!-- 拒绝信息 -->
            <div class="reject-info" v-if="order.status === 'rejected'">
              <div class="reject-reason" v-if="order.reject_reason">
                <strong>{{ order.rejected_by === 'user' ? '用户拒绝理由' : '拒绝理由' }}：</strong>{{ order.reject_reason }}
              </div>
              <div v-if="order.rejected_by === 'user'" class="reject-hint">
                用户拒绝了您的报价，您可以修改报价重新发送
              </div>
            </div>

            <div class="order-actions">
              <template v-if="order.status === 'pending'">
                <el-button type="primary" size="small" @click="openQuote(order)">报价</el-button>
                <el-button type="danger" size="small" plain @click="rejectOrder(order)">拒绝</el-button>
              </template>
              <template v-else-if="order.status === 'quoted' || order.status === 'accepted'">
                <span v-if="order.pay_status !== 'paid'" style="color:#e6a23c;font-size:13px">
                  等待用户付款
                  <PaymentCountdown
                    v-if="order.payment_started_at"
                    :payment-started-at="order.payment_started_at"
                  />
                </span>
                <el-button v-else type="primary" size="small" @click="shipOrder(order)">发货</el-button>
              </template>
              <template v-else-if="order.status === 'in_progress' && order.pay_status === 'paid'">
                <el-button type="primary" size="small" @click="shipOrder(order)">发货</el-button>
              </template>
              <template v-else-if="order.status === 'shipped'">
                <span style="color:#409eff;font-size:13px">等待用户收货</span>
              </template>
              <template v-else-if="order.status === 'completed'">
                <span style="color:#67c23a;font-size:13px">已完成</span>
              </template>
              <!-- 用户拒绝报价后：匠人可重新报价 -->
              <template v-else-if="order.status === 'rejected' && order.rejected_by === 'user'">
                <el-button type="primary" size="small" @click="openQuote(order)">重新报价</el-button>
              </template>
            </div>
          </div>
        </div>
      </div>
    </div>

    <el-dialog v-model="quoteVisible" title="报价" width="400px">
      <el-form :model="quoteForm" label-width="80px">
        <el-form-item label="报价金额">
          <el-input-number v-model="quoteForm.amount" :min="0" :precision="2" style="width:100%" controls-position="right" />
        </el-form-item>
        <el-form-item label="预计工期">
          <el-input-number v-model="quoteForm.deadline" :min="1" style="width:100%" controls-position="right" />
          <span style="margin-left:8px;color:#999">天</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="quoteVisible = false">取消</el-button>
        <el-button type="primary" @click="handleQuote" :loading="quoting">确认报价</el-button>
      </template>
    </el-dialog>
  </MainLayout>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import MainLayout from '@/components/MainLayout.vue'
import PaymentCountdown from '@/components/PaymentCountdown.vue'
import { artisanApi } from '@/api/modules'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Clock } from '@element-plus/icons-vue'

const orders = ref([])
const loading = ref(false)
const filterStatus = ref('')
const quoteVisible = ref(false)
const quoting = ref(false)
const quoteForm = ref({ amount: 0, deadline: 7 })
const currentOrder = ref(null)

const statusType = (s) => {
  const map = { pending: 'warning', quoted: '', accepted: '', in_progress: 'primary', shipped: 'primary', completed: 'success', rejected: 'danger', cancelled: 'info' }
  return map[s] || ''
}

const statusLabel = (s) => {
  const map = { pending: '待处理', quoted: '已报价', accepted: '已报价', in_progress: '制作中', shipped: '已发货', completed: '已完成', rejected: '已拒绝', cancelled: '已取消' }
  return map[s] || s
}

const loadOrders = async () => {
  loading.value = true
  try {
    const res = await artisanApi.getCustomOrders({ skip: 0, limit: 50 })
    let items = res.items || []
    if (filterStatus.value) {
      const filters = filterStatus.value.split('|')
      items = items.filter(o => filters.includes(o.status))
    }
    orders.value = items
  } catch (err) {
    console.error(err)
  } finally {
    loading.value = false
  }
}

const openQuote = (order) => {
  currentOrder.value = order
  // 如果是重新报价，预填上次的报价信息
  quoteForm.value = {
    amount: order.quote_amount ? parseFloat(order.quote_amount) : 0,
    deadline: order.quote_deadline || 7,
  }
  quoteVisible.value = true
}

const handleQuote = async () => {
  if (!quoteForm.value.amount || quoteForm.value.amount <= 0) {
    ElMessage.warning('请输入报价金额')
    return
  }
  quoting.value = true
  try {
    await artisanApi.quoteCustomOrder(currentOrder.value.id, {
      quote_amount: quoteForm.value.amount,
      quote_deadline: quoteForm.value.deadline,
    })
    ElMessage.success('报价已发送')
    quoteVisible.value = false
    loadOrders()
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '报价失败')
  } finally {
    quoting.value = false
  }
}

const rejectOrder = async (order) => {
  try {
    const { value: reason } = await ElMessageBox.prompt('请输入拒绝原因', '拒绝定制需求', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      inputType: 'textarea',
    })
    await artisanApi.rejectCustomOrder(order.id, reason || '')
    ElMessage.success('已拒绝')
    loadOrders()
  } catch (err) {
    if (err !== 'cancel') ElMessage.error('操作失败')
  }
}

const shipOrder = async (order) => {
  try {
    await artisanApi.shipCustomOrder(order.id)
    ElMessage.success('已发货')
    loadOrders()
  } catch (err) {
    ElMessage.error('操作失败')
  }
}

const completeOrder = async (order) => {
  try {
    await artisanApi.updateCustomProgress(order.id, 100)
    ElMessage.success('已标记完成')
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
  margin: 0 0 10px;
  line-height: 1.6;
}
.deadline-info {
  font-size: 13px;
  color: #e6a23c;
  display: flex;
  align-items: center;
  gap: 4px;
  margin-bottom: 10px;
}
.ref-images {
  margin-bottom: 12px;
}
.quote-info {
  font-size: 14px;
  color: #666;
  margin-bottom: 12px;
  padding: 8px 12px;
  background: #f5f7fa;
  border-radius: 6px;
}
.quote-info strong {
  color: #f56c6c;
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
}
</style>
