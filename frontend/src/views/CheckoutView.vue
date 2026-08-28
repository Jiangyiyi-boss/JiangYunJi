<template>
  <MainLayout>
    <div class="checkout-container">
      <h2 class="page-title">确认订单</h2>
      
      <div class="checkout-content">
        <!-- 左侧：收货地址和商品信息 -->
        <div class="checkout-main">
          <!-- 收货地址 -->
          <div class="section-card">
            <div class="section-header">
              <h3><el-icon><Location /></el-icon> 收货地址</h3>
              <el-button type="primary" link @click="showAddressDialog = true">
                管理地址
              </el-button>
            </div>
            
            <div v-if="selectedAddress" class="address-info">
              <div class="address-default">
                <el-tag type="success" size="small" effect="plain">默认</el-tag>
              </div>
              <div class="address-detail">
                <span class="receiver-name">{{ selectedAddress.name }}</span>
                <span class="receiver-phone">{{ selectedAddress.phone }}</span>
              </div>
              <div class="address-location">
                {{ selectedAddress.province }}{{ selectedAddress.city }}{{ selectedAddress.district }}{{ selectedAddress.detail }}
              </div>
            </div>
            
            <div v-else class="no-address">
              <el-empty description="暂无收货地址" :image-size="80">
                <el-button type="primary" @click="showAddressDialog = true">添加收货地址</el-button>
              </el-empty>
            </div>
          </div>

          <!-- 商品信息 -->
          <div class="section-card">
            <div class="section-header">
              <h3><el-icon><ShoppingCart /></el-icon> 商品信息</h3>
            </div>
            
            <div class="product-list">
              <div v-for="item in orderItems" :key="item.product_id" class="product-item">
                <img :src="item.image || '/default-product.png'" :alt="item.name" class="product-image">
                <div class="product-info">
                  <h4 class="product-name">{{ item.name }}</h4>
                  <p v-if="item.spec_name" class="product-spec">规格：{{ item.spec_name }}</p>
                  <div class="product-meta">
                    <span class="product-price">¥{{ item.price }}</span>
                    <span class="product-qty">×{{ item.qty }}</span>
                  </div>
                </div>
                <div class="product-subtotal">
                  ¥{{ (item.price * item.qty).toFixed(2) }}
                </div>
              </div>
            </div>
          </div>

        </div>

        <!-- 右侧：价格明细 -->
        <div class="checkout-sidebar">
          <div class="price-card">
            <h3>价格明细</h3>
            
            <div class="price-row">
              <span>商品总价</span>
              <span>¥{{ productTotal.toFixed(2) }}</span>
            </div>
            
            <div class="price-row">
              <span>运费</span>
              <span>¥{{ shippingFee.toFixed(2) }}</span>
            </div>
            
            <el-divider />
            
            <div class="price-total">
              <span>合计</span>
              <span class="total-amount">¥{{ totalAmount.toFixed(2) }}</span>
            </div>
            
            <el-button 
              type="danger" 
              size="large" 
              class="confirm-btn"
              :loading="submitting"
              :disabled="!canSubmit"
              @click="handleConfirmOrder"
            >
              确认购买
            </el-button>
            
            <div class="tips">
              <el-icon><InfoFilled /></el-icon>
              <span>请在10分钟内完成支付，超时订单将自动取消</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 地址选择对话框 -->
      <el-dialog v-model="showAddressDialog" title="选择收货地址" width="600px" append-to-body>
        <div class="address-selector">
          <!-- 已有地址列表 -->
          <div v-if="existingAddresses.length > 0" class="address-list">
            <h4 class="section-title">我的地址</h4>
            <el-radio-group v-model="selectedAddressId" class="address-radio-group">
              <el-card 
                v-for="addr in existingAddresses" 
                :key="addr.id" 
                class="address-card"
                :class="{ 'is-selected': selectedAddressId === addr.id }"
                shadow="hover"
              >
                <el-radio :label="addr.id" class="address-radio">
                  <div class="address-content">
                    <div class="address-header">
                      <span class="receiver-name">{{ addr.name }}</span>
                      <span class="receiver-phone">{{ addr.phone }}</span>
                      <el-tag v-if="addr.is_default" type="success" size="small" effect="plain">默认</el-tag>
                    </div>
                    <div class="address-detail">
                      {{ addr.province }}{{ addr.city }}{{ addr.district }}{{ addr.detail }}
                    </div>
                  </div>
                </el-radio>
              </el-card>
            </el-radio-group>
          </div>
          
          <el-divider v-if="existingAddresses.length > 0">或使用新地址</el-divider>
          
          <!-- 新增地址表单 -->
          <div class="new-address-section">
            <h4 class="section-title">添加新地址</h4>
            <el-form :model="addressForm" label-width="80px" size="small">
              <el-form-item label="姓名">
                <el-input v-model="addressForm.name" placeholder="请输入收件人姓名" />
              </el-form-item>
              <el-form-item label="手机号">
                <el-input v-model="addressForm.phone" placeholder="请输入手机号" maxlength="11" />
              </el-form-item>
              <el-form-item label="所在地区">
                <el-cascader
                  v-model="addressForm.region"
                  :options="regionData"
                  :props="{ value: 'value', label: 'label', children: 'children', emitPath: true }"
                  placeholder="请选择省/市/区"
                  style="width: 100%"
                  clearable
                  filterable
                />
              </el-form-item>
              <el-form-item label="详细地址">
                <el-input v-model="addressForm.detail" type="textarea" :rows="2" placeholder="街道、门牌号等" />
              </el-form-item>
              <el-form-item>
                <el-checkbox v-model="addressForm.is_default">设为默认地址</el-checkbox>
              </el-form-item>
            </el-form>
          </div>
        </div>
        
        <template #footer>
          <el-button @click="showAddressDialog = false">取消</el-button>
          <el-button type="primary" @click="handleSaveAddress" :loading="savingAddress">
            保存地址
          </el-button>
        </template>
      </el-dialog>
    </div>
  </MainLayout>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Location, ShoppingCart, InfoFilled } from '@element-plus/icons-vue'
import MainLayout from '@/components/MainLayout.vue'
import { orderApi } from '@/api/modules'
import { regionData, getRegionText } from '@/utils/regionData'

const route = useRoute()
const router = useRouter()

// 数据
const orderItems = ref([])
const selectedAddress = ref(null)
const selectedAddressId = ref(null)
const submitting = ref(false)
const savingAddress = ref(false)
const showAddressDialog = ref(false)
const existingAddresses = ref([])
const addressForm = ref({
  name: '',
  phone: '',
  region: [],
  detail: '',
  is_default: false,
})

// 计算属性
const productTotal = computed(() => {
  return orderItems.value.reduce((sum, item) => sum + item.price * item.qty, 0)
})

// 计算运费：根据商品包邮设置
const shippingFee = computed(() => {
  let totalFee = 0
  for (const item of orderItems.value) {
    if (item.shipping_type === 'fixed') {
      totalFee += (item.shipping_fee || 0) * item.qty
    }
  }
  return totalFee
})

const totalAmount = computed(() => {
  return productTotal.value + shippingFee.value
})

const canSubmit = computed(() => {
  return !!selectedAddress.value && orderItems.value.length > 0
})

// 生命周期
onMounted(async () => {
  // 从路由参数获取商品信息
  const itemsData = route.query.items
  if (itemsData) {
    try {
      orderItems.value = JSON.parse(itemsData)
    } catch (err) {
      console.error('解析商品信息失败:', err)
      ElMessage.error('商品信息错误')
      router.push('/home')
      return
    }
  } else {
    ElMessage.warning('没有商品信息')
    router.push('/home')
    return
  }

  // 加载用户地址
  await loadAddresses()
})

// 方法
const loadAddresses = async () => {
  try {
    const addresses = await orderApi.getAddresses()
    existingAddresses.value = Array.isArray(addresses) ? addresses : []
    
    // 选中默认地址或第一个地址
    if (existingAddresses.value.length > 0) {
      const defaultAddr = existingAddresses.value.find(a => a.is_default)
      selectedAddress.value = defaultAddr || existingAddresses.value[0]
      selectedAddressId.value = selectedAddress.value.id
    }
  } catch (err) {
    console.warn('获取地址失败:', err)
  }
}

const handleSaveAddress = async () => {
  // 验证表单
  if (!addressForm.value.name || !addressForm.value.phone || !addressForm.value.detail) {
    ElMessage.error('请填写完整的新地址信息')
    return
  }
  if (!addressForm.value.region || addressForm.value.region.length < 3) {
    ElMessage.error('请选择完整的省/市/区')
    return
  }
  if (!/^1[3-9]\d{9}$/.test(addressForm.value.phone)) {
    ElMessage.error('请输入正确的手机号')
    return
  }

  savingAddress.value = true
  try {
    const { province, city, district } = getRegionText(addressForm.value.region)
    const payload = {
      name: addressForm.value.name,
      phone: addressForm.value.phone,
      province,
      city,
      district,
      detail: addressForm.value.detail,
      is_default: addressForm.value.is_default,
    }
    const newAddress = await orderApi.createAddress(payload)
    existingAddresses.value.push(newAddress)
    
    // 选中新地址
    selectedAddress.value = newAddress
    selectedAddressId.value = newAddress.id
    
    ElMessage.success('地址添加成功')
    showAddressDialog.value = false
    
    // 重置表单
    addressForm.value = {
      name: '',
      phone: '',
      region: [],
      detail: '',
      is_default: false,
    }
  } catch (err) {
    ElMessage.error(err.message || '添加地址失败')
  } finally {
    savingAddress.value = false
  }
}

const handleConfirmOrder = async () => {
  if (!selectedAddress.value) {
    ElMessage.warning('请选择收货地址')
    return
  }

  submitting.value = true
  try {
    // 构建订单项
    const items = orderItems.value.map(item => ({
      product_id: item.product_id,
      qty: item.qty,
      spec_name: item.spec_name || '',
      spec_price: item.price,
    }))

    // 创建订单
    const order = await orderApi.createOrder({
      items,
      address_id: selectedAddress.value.id,
    })

    ElMessage.success('订单创建成功')
    
    // 跳转到支付页面
    router.push(`/pay/${order.id}`)
  } catch (err) {
    console.error('创建订单失败:', err)
    ElMessage.error(err.message || '创建订单失败')
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.checkout-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: 24px;
}

.checkout-content {
  display: grid;
  grid-template-columns: 1fr 360px;
  gap: 24px;
}

/* 左侧主内容 */
.checkout-main {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.section-card {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text);
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
}

/* 收货地址 */
.address-info {
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
}

.address-default {
  margin-bottom: 8px;
}

.address-detail {
  margin-bottom: 8px;
}

.receiver-name {
  font-weight: 600;
  margin-right: 12px;
}

.receiver-phone {
  color: #666;
}

.address-location {
  color: #666;
  font-size: 14px;
}

.no-address {
  padding: 20px;
}

/* 商品列表 */
.product-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.product-item {
  display: flex;
  gap: 16px;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
}

.product-image {
  width: 80px;
  height: 80px;
  object-fit: cover;
  border-radius: 4px;
}

.product-info {
  flex: 1;
}

.product-name {
  font-size: 14px;
  font-weight: 500;
  margin: 0 0 4px;
}

.product-spec {
  font-size: 12px;
  color: #999;
  margin: 0 0 8px;
}

.product-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.product-price {
  font-size: 16px;
  font-weight: 600;
  color: #ff4d4f;
}

.product-qty {
  font-size: 14px;
  color: #999;
}

.product-subtotal {
  font-size: 16px;
  font-weight: 600;
  color: #ff4d4f;
}

/* 右侧侧边栏 */
.checkout-sidebar {
  position: sticky;
  top: 20px;
  height: fit-content;
}

.price-card {
  background: white;
  border-radius: 8px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.price-card h3 {
  font-size: 18px;
  font-weight: 600;
  margin: 0 0 16px;
}

.price-row {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  font-size: 14px;
  color: #666;
}

.price-total {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  font-size: 16px;
  font-weight: 600;
}

.total-amount {
  font-size: 24px;
  color: #ff4d4f;
}

.confirm-btn {
  width: 100%;
  margin-top: 16px;
  font-size: 16px;
  font-weight: 600;
}

.tips {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 12px;
  padding: 12px;
  background: #fff7e6;
  border-radius: 8px;
  color: #fa8c16;
  font-size: 12px;
}

/* 地址选择器样式 */
.address-selector {
  max-height: 60vh;
  overflow-y: auto;
}

.section-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text);
  margin: 0 0 12px;
}

.address-list {
  margin-bottom: 16px;
}

.address-radio-group {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.address-card {
  cursor: pointer;
  transition: all var(--transition-fast);
  border: 2px solid transparent;
}

.address-card:hover {
  border-color: var(--color-primary-light);
}

.address-card.is-selected {
  border-color: var(--color-primary);
  background: var(--color-bg-warm);
}

.address-radio {
  width: 100%;
}

.address-content {
  margin-left: 8px;
}

.address-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.new-address-section {
  margin-top: 16px;
}

@media (max-width: 768px) {
  .checkout-content {
    grid-template-columns: 1fr;
  }
  
  .checkout-sidebar {
    position: static;
  }
}
</style>