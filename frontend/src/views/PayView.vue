<template>
  <div class="pay-container">
    <div class="pay-card">
      <!-- 生成二维码中 -->
      <div v-if="generating" class="pay-status">
        <el-icon class="spin-icon" :size="48"><Loading /></el-icon>
        <p>正在生成支付二维码...</p>
      </div>

      <!-- 二维码展示 -->
      <div v-else-if="qrCodeUrl && !paid" class="qr-section">
        <div class="pay-header">
          <h2>扫码支付</h2>
          <div class="order-info">
            <p>订单编号：{{ orderNo }}</p>
            <p class="amount">应付金额：<span>¥{{ amount }}</span></p>
            <el-tag v-if="isCourseOrder" type="info" size="small" style="margin-top: 8px">线上课程</el-tag>
            <el-tag v-if="isCustomOrder" type="warning" size="small" style="margin-top: 8px">定制订单</el-tag>
          </div>
        </div>

        <div class="qr-wrapper">
          <div class="qr-box">
            <qrcode-vue :value="qrCodeUrl" :size="220" level="M" render-as="svg" class="qr-code" />
            <div class="qr-overlay" v-if="qrExpired">
              <div class="qr-overlay-text">
                <el-icon :size="36"><WarningFilled /></el-icon>
                <p>二维码已过期</p>
                <el-button type="primary" size="small" @click="generateQrCode">点击刷新</el-button>
              </div>
            </div>
          </div>
          <div class="qr-hint">
            <div class="pay-badge">
              <svg viewBox="0 0 24 24" width="20" height="20">
                <path fill="#1677FF" d="M21.422 15.358c-1.38-.523-2.82-1.102-4.29-1.68.72-1.32 1.26-2.82 1.56-4.44h-3.48v-1.56h4.2V7.2h-4.2V4.8h-2.04c-.24 0-.42.18-.42.42v2.01H8.52v1.56h4.23v1.56H9.48v1.56h5.76c-.24 1.26-.66 2.4-1.2 3.42-1.86-.6-3.78-1.02-5.52-1.02-2.82 0-4.68 1.56-4.68 3.72 0 2.22 1.92 3.66 4.92 3.66 1.92 0 3.78-.72 5.34-1.98 1.56 1.2 3.3 2.22 5.1 3.06.72-1.02 1.38-2.1 1.92-3.24zM8.52 18.18c-1.92 0-3.18-.9-3.18-2.22 0-1.26 1.2-2.16 3.12-2.16 1.38 0 2.88.3 4.38.78-1.08 1.98-2.58 3.6-4.32 3.6z"/>
              </svg>
              <span>支付宝</span>
            </div>
            <p>请使用 <strong>支付宝</strong> 扫码支付</p>
          </div>
        </div>

        <div class="pay-tips">
          <el-icon><InfoFilled /></el-icon>
          <span>请在10分钟内完成支付，超时订单将自动取消</span>
          <PaymentCountdown
            v-if="paymentStartedAt"
            :payment-started-at="paymentStartedAt"
            style="margin-left:8px;font-size:14px"
          />
        </div>

        <div class="pay-actions">
          <el-button size="large" @click="$router.back()">返回</el-button>
          <el-button size="large" @click="generateQrCode" :loading="generating">
            <el-icon style="margin-right:4px"><Refresh /></el-icon>
            刷新二维码
          </el-button>
        </div>
      </div>

      <!-- 支付成功 -->
      <div v-else-if="paid" class="pay-success">
        <div class="success-icon">
          <el-icon :size="64"><CircleCheckFilled /></el-icon>
        </div>
        <h2>支付成功</h2>
        <p class="order-no">订单编号：{{ orderNo }}</p>
        <p class="amount">支付金额：<span>¥{{ amount }}</span></p>
        <div class="success-actions">
          <el-button type="primary" size="large" @click="goToNext">
            {{ isCourseOrder ? '去学习' : '查看订单' }}
          </el-button>
          <el-button size="large" @click="$router.push('/home')">返回首页</el-button>
        </div>
      </div>

      <!-- 生成失败 -->
      <div v-else class="pay-status">
        <div class="error-icon">
          <el-icon :size="48"><WarningFilled /></el-icon>
        </div>
        <p class="error-msg">{{ errorMsg || '支付二维码生成失败' }}</p>
        <el-button type="primary" size="large" @click="generateQrCode">重新生成</el-button>
        <el-button size="large" @click="$router.back()">返回</el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { paymentApi } from '@/api/modules'
import { ElMessage } from 'element-plus'
import {
  Loading, InfoFilled, CircleCheckFilled, WarningFilled, Refresh,
} from '@element-plus/icons-vue'
import QrcodeVue from 'qrcode.vue'
import PaymentCountdown from '@/components/PaymentCountdown.vue'

const route = useRoute()
const router = useRouter()

const orderId = ref(route.params.orderId)
const orderNo = ref('')
const amount = ref('0.00')
const isCourseOrder = ref(false)
const isCustomOrder = ref(false)
const paymentStartedAt = ref('')

const generating = ref(false)
const qrCodeUrl = ref('')
const paid = ref(false)
const errorMsg = ref('')
const qrExpired = ref(false)

const isCustom = route.query.type === 'custom'

let pollingTimer = null
let expiredTimer = null

onMounted(() => {
  initPayment()
})

onUnmounted(() => {
  stopPolling()
  if (expiredTimer) {
    clearTimeout(expiredTimer)
  }
})

const initPayment = async () => {
  // 先加载订单信息
  await loadOrderInfo()
  // 再生成二维码
  await generateQrCode()
}

const loadOrderInfo = async () => {
  try {
    if (isCustom) {
      const info = await paymentApi.queryCustomPaymentStatus(orderId.value)
      orderNo.value = info.order_no
      amount.value = info.pay_amount
      isCustomOrder.value = true
      paymentStartedAt.value = info.payment_started_at || ''

      // 如果已经支付过，直接显示成功
      if (info.pay_status === 'paid' || info.status !== 'accepted') {
        paid.value = true
      }
    } else {
      const orderInfo = await paymentApi.queryPaymentStatus(orderId.value)
      orderNo.value = orderInfo.order_no
      amount.value = orderInfo.pay_amount
      isCourseOrder.value = orderInfo.goods_type === 2
      paymentStartedAt.value = orderInfo.payment_started_at || ''

      // 如果已经支付过，直接显示成功
      if (orderInfo.status !== 'pending') {
        paid.value = true
      }
    }
  } catch (err) {
    ElMessage.error('获取订单信息失败')
    router.push('/orders')
  }
}

const generateQrCode = async () => {
  if (generating.value || paid.value) return

  generating.value = true
  errorMsg.value = ''
  qrExpired.value = false
  stopPolling()

  try {
    let result
    if (isCustom) {
      result = await paymentApi.createCustomAlipayPayment(orderId.value)
    } else {
      result = await paymentApi.createAlipayPayment(orderId.value)
    }

    if (result.qr_code) {
      qrCodeUrl.value = result.qr_code
      // 更新订单号和金额（首次生成时后端可能刚创建 order_no）
      if (result.order_no) orderNo.value = result.order_no
      if (result.amount) amount.value = result.amount

      // 重新加载支付开始时间（用于倒计时）
      await refreshPaymentStartedAt()

      // 开始轮询支付状态
      startPolling()

      // 9 分钟后标记二维码过期（留 1 分钟缓冲）
      if (expiredTimer) clearTimeout(expiredTimer)
      expiredTimer = setTimeout(() => {
        if (!paid.value) {
          qrExpired.value = true
          stopPolling()
        }
      }, 9 * 60 * 1000)
    } else {
      errorMsg.value = '未获取到支付二维码'
    }
  } catch (err) {
    errorMsg.value = err.response?.data?.detail || err.message || '支付二维码生成失败'
  } finally {
    generating.value = false
  }
}

const refreshPaymentStartedAt = async () => {
  try {
    if (isCustom) {
      const info = await paymentApi.queryCustomPaymentStatus(orderId.value)
      paymentStartedAt.value = info.payment_started_at || ''
    } else {
      const info = await paymentApi.queryPaymentStatus(orderId.value)
      paymentStartedAt.value = info.payment_started_at || ''
    }
  } catch {
    // 忽略，不影响主流程
  }
}

const startPolling = () => {
  stopPolling()
  // 立即查询一次
  checkPaymentStatus()
  // 每 2 秒轮询
  pollingTimer = setInterval(checkPaymentStatus, 2000)
}

const stopPolling = () => {
  if (pollingTimer) {
    clearInterval(pollingTimer)
    pollingTimer = null
  }
}

const checkPaymentStatus = async () => {
  if (paid.value) {
    stopPolling()
    return
  }

  try {
    let isPaid = false

    if (isCustom) {
      const result = await paymentApi.queryCustomPaymentStatus(orderId.value)
      isPaid = result.pay_status === 'paid'
    } else {
      const result = await paymentApi.queryPaymentStatus(orderId.value)
      isPaid = result.status === 'paid' || result.status === 'shipped' || result.status === 'completed'
    }

    if (isPaid) {
      paid.value = true
      stopPolling()
      if (expiredTimer) {
        clearTimeout(expiredTimer)
        expiredTimer = null
      }
    }
  } catch (err) {
    // 网络错误不中断轮询，继续重试
  }
}

const goToNext = () => {
  if (isCourseOrder.value) {
    router.push('/my-courses')
  } else if (isCustomOrder.value) {
    router.push('/custom')
  } else {
    router.push('/orders')
  }
}
</script>

<style scoped>
.pay-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.pay-card {
  background: white;
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  max-width: 520px;
  width: 100%;
  padding: 40px;
}

/* 状态展示（加载中 / 错误） */
.pay-status {
  text-align: center;
  padding: 40px 0;
}

.pay-status p {
  color: #666;
  font-size: 16px;
  margin-top: 20px;
}

.pay-status .error-msg {
  color: #ff4d4f;
  margin-bottom: 24px;
}

.spin-icon {
  color: #1677FF;
  animation: spin 1s linear infinite;
}

.error-icon {
  color: #ff4d4f;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* 二维码区域 */
.pay-header {
  text-align: center;
  margin-bottom: 32px;
}

.pay-header h2 {
  font-size: 24px;
  color: #333;
  margin-bottom: 16px;
}

.order-info {
  background: #f8f9fa;
  padding: 16px 20px;
  border-radius: 8px;
}

.order-info p {
  margin: 6px 0;
  color: #666;
  font-size: 14px;
}

.order-info .amount {
  font-size: 16px;
  margin-top: 10px;
}

.order-info .amount span {
  color: #ff4d4f;
  font-size: 24px;
  font-weight: bold;
}

/* 二维码 */
.qr-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 24px;
}

.qr-box {
  position: relative;
  padding: 16px;
  border: 1px solid #e8e8e8;
  border-radius: 12px;
  background: #fff;
}

.qr-code {
  display: block;
}

.qr-overlay {
  position: absolute;
  inset: 16px;
  background: rgba(255, 255, 255, 0.92);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.qr-overlay-text {
  text-align: center;
  color: #999;
}

.qr-overlay-text p {
  margin: 12px 0;
  font-size: 14px;
}

.qr-hint {
  margin-top: 16px;
  text-align: center;
}

.qr-hint p {
  font-size: 14px;
  color: #666;
  margin-top: 8px;
}

.pay-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 14px;
  background: #f0f7ff;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 500;
  color: #1677FF;
}

/* 提示 */
.pay-tips {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  background: #fff7e6;
  border-radius: 8px;
  color: #fa8c16;
  font-size: 13px;
  margin-bottom: 20px;
}

.pay-tips .el-icon {
  font-size: 16px;
  flex-shrink: 0;
}

/* 按钮 */
.pay-actions {
  display: flex;
  gap: 12px;
}

.pay-actions .el-button {
  flex: 1;
}

/* 支付成功 */
.pay-success {
  text-align: center;
  padding: 20px 0;
}

.success-icon {
  color: #52c41a;
  margin-bottom: 8px;
}

.pay-success h2 {
  font-size: 24px;
  color: #333;
  margin: 16px 0 20px;
}

.pay-success .order-no {
  color: #999;
  font-size: 13px;
  margin: 8px 0;
  word-break: break-all;
}

.pay-success .amount {
  font-size: 16px;
  color: #666;
  margin-top: 8px;
}

.pay-success .amount span {
  color: #ff4d4f;
  font-size: 22px;
  font-weight: bold;
}

.success-actions {
  display: flex;
  gap: 12px;
  margin-top: 32px;
  justify-content: center;
}
</style>
