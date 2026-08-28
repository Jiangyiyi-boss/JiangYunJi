<template>
  <div class="pay-callback-container">
    <div class="callback-card">
      <!-- 加载中 -->
      <div v-if="checking" class="callback-content">
        <el-icon class="loading-icon" :size="64"><Loading /></el-icon>
        <h2>正在确认支付结果...</h2>
        <p>请稍候，正在向服务器查询订单状态</p>
        <p class="order-no">订单编号：{{ orderNo }}</p>
      </div>

      <!-- 支付成功 -->
      <div v-else-if="success" class="callback-content">
        <div class="result-icon success-icon">
          <el-icon :size="64"><CircleCheckFilled /></el-icon>
        </div>
        <h2>支付成功！</h2>
        <p class="order-no">订单编号：{{ orderNo }}</p>
        <p class="amount">支付金额：<span>¥{{ amount }}</span></p>
        <div class="callback-actions">
          <el-button type="primary" size="large" @click="goToOrders">
            {{ isCourseOrder ? '去学习' : '查看订单' }}
          </el-button>
          <el-button size="large" @click="$router.push('/home')">
            返回首页
          </el-button>
        </div>
      </div>

      <!-- 支付失败/待确认 -->
      <div v-else class="callback-content">
        <div class="result-icon pending-icon">
          <el-icon :size="64"><WarningFilled /></el-icon>
        </div>
        <h2>{{ errorMsg ? '查询异常' : '支付结果待确认' }}</h2>
        <p>{{ errorMsg || '我们暂时未能确认您的支付结果，请稍后查看订单状态' }}</p>
        <p class="order-no">订单编号：{{ orderNo }}</p>
        <div class="callback-actions">
          <el-button type="primary" size="large" @click="$router.push('/orders')">
            查看订单
          </el-button>
          <el-button size="large" @click="checkAgain" :loading="checking">
            重新查询
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { paymentApi } from '@/api/modules'
import { Loading, CircleCheckFilled, WarningFilled } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()

const checking = ref(true)
const success = ref(false)
const isCourseOrder = ref(false)
const orderNo = ref('')
const amount = ref('0.00')
const errorMsg = ref('')
let pollingTimer = null

onMounted(() => {
  // 支付宝同步回调携带的参数:
  // out_trade_no, trade_no, total_amount, seller_id, app_id, sign, sign_type, charset
  orderNo.value = route.query.out_trade_no || ''
  amount.value = route.query.total_amount || '0.00'

  if (orderNo.value) {
    // 直接通过订单号查询支付状态（公开接口，无需登录）
    startPolling()
  } else {
    checking.value = false
    errorMsg.value = '未获取到订单号，无法确认支付结果'
  }
})

onUnmounted(() => {
  if (pollingTimer) {
    clearInterval(pollingTimer)
    pollingTimer = null
  }
})

const startPolling = () => {
  // 立即查询一次
  checkPaymentStatus()

  // 每2秒轮询一次，最多15次（30秒），等待异步通知完成
  let attempts = 0
  const maxAttempts = 15

  pollingTimer = setInterval(async () => {
    attempts++
    if (attempts >= maxAttempts || success.value) {
      clearInterval(pollingTimer)
      pollingTimer = null
      if (!success.value) {
        checking.value = false
      }
      return
    }
    await checkPaymentStatus()
  }, 2000)
}

const checkPaymentStatus = async () => {
  if (!orderNo.value) return

  try {
    const result = await paymentApi.queryStatusByNo(orderNo.value)
    const status = result.status
    const payStatus = result.pay_status
    const goodsType = result.goods_type

    const isPaid = status === 'paid' || status === 'shipped' || status === 'completed'
    const isCustomPaid = goodsType === 'custom' && payStatus === 'paid'

    if (isPaid || isCustomPaid) {
      success.value = true
      checking.value = false
      isCourseOrder.value = goodsType === 2
      if (pollingTimer) {
        clearInterval(pollingTimer)
        pollingTimer = null
      }
    }
    // 如果还是 pending，继续轮询（异步通知可能还没到）
  } catch (err) {
    console.error('查询支付状态失败:', err)
    // 404 表示订单不存在，立即停止轮询
    if (err.response?.status === 404) {
      errorMsg.value = '未找到对应订单'
      checking.value = false
      if (pollingTimer) {
        clearInterval(pollingTimer)
        pollingTimer = null
      }
    }
    // 其他错误（网络问题等）继续轮询，不中断
  }
}

const checkAgain = () => {
  errorMsg.value = ''
  checking.value = true
  success.value = false
  startPolling()
}

const goToOrders = () => {
  const dest = isCourseOrder.value ? '/my-courses' : '/orders'
  // 检查登录状态，未登录则跳转登录页并携带 redirect
  const token = localStorage.getItem('token')
  if (!token) {
    router.push({ name: 'Login', query: { redirect: dest } })
  } else {
    router.push(dest)
  }
}
</script>

<style scoped>
.pay-callback-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.callback-card {
  background: white;
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  max-width: 500px;
  width: 100%;
  padding: 60px 40px;
}

.callback-content {
  text-align: center;
}

.callback-content h2 {
  font-size: 24px;
  color: #333;
  margin: 24px 0 12px;
}

.callback-content > p {
  color: #666;
  font-size: 14px;
  margin: 8px 0;
}

.loading-icon {
  color: #1890ff;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.result-icon {
  margin-bottom: 8px;
}

.success-icon {
  color: #52c41a;
}

.pending-icon {
  color: #fa8c16;
}

.order-no {
  color: #999;
  font-size: 13px !important;
  word-break: break-all;
}

.amount {
  font-size: 16px;
  margin-top: 12px !important;
}

.amount span {
  color: #ff4d4f;
  font-size: 22px;
  font-weight: bold;
}

.callback-actions {
  display: flex;
  gap: 12px;
  margin-top: 36px;
  justify-content: center;
}
</style>
