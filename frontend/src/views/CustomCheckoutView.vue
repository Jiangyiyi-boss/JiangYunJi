<template>
  <MainLayout>
    <div class="checkout-container">
      <h2 class="page-title">确认定制订单</h2>

      <div class="checkout-content">
        <div class="checkout-main">
          <!-- 收货地址 -->
          <div class="section-card">
            <div class="section-header">
              <h3><el-icon><Location /></el-icon> 收货地址</h3>
              <el-button type="primary" link size="small" @click="showAddressDialog">选择地址</el-button>
            </div>
            <div class="address-info" @click="showAddressDialog" style="cursor:pointer">
              <template v-if="shippingAddress.name">
                <div class="address-detail">
                  <span class="receiver-name">{{ shippingAddress.name }}</span>
                  <span class="receiver-phone">{{ shippingAddress.phone }}</span>
                </div>
                <div class="address-location">{{ shippingAddress.full }}</div>
              </template>
              <div v-else class="no-address">点击选择收货地址</div>
            </div>
          </div>

          <!-- 定制图片 -->
          <div class="section-card">
            <div class="section-header">
              <h3><el-icon><Picture /></el-icon> 定制参考图</h3>
            </div>
            <div v-if="order.reference_images?.length" class="image-grid">
              <el-image
                v-for="(img, idx) in order.reference_images"
                :key="idx"
                :src="img"
                fit="cover"
                class="ref-image"
                :preview-src-list="order.reference_images"
                :initial-index="idx"
              />
            </div>
            <el-empty v-else description="暂无参考图片" :image-size="60" />
          </div>

          <!-- 需求描述 -->
          <div class="section-card" v-if="order.description">
            <div class="section-header">
              <h3><el-icon><Document /></el-icon> 需求描述</h3>
            </div>
            <p class="desc-text">{{ order.description }}</p>
          </div>
        </div>

        <!-- 右侧：价格明细 -->
        <div class="checkout-sidebar">
          <div class="price-card">
            <h3>订单明细</h3>

            <div class="price-row">
              <span>定制报价</span>
              <span>¥{{ fmt(order.quote_amount) }}</span>
            </div>

            <div class="price-row" v-if="order.quote_deadline">
              <span>预计工期</span>
              <span>{{ order.quote_deadline }} 天</span>
            </div>

            <div class="price-row" v-if="estimatedDelivery">
              <span>预计发货</span>
              <span>{{ estimatedDelivery }}</span>
            </div>

            <el-divider />

            <div class="price-total">
              <span>应付金额</span>
              <span class="total-amount">¥{{ fmt(order.quote_amount) }}</span>
            </div>

            <el-button
              type="danger"
              size="large"
              class="confirm-btn"
              :loading="submitting"
              @click="handlePay"
            >
              立即支付
            </el-button>

            <div class="tips">
              <el-icon><InfoFilled /></el-icon>
              <span>请在10分钟内完成支付，超时订单将自动取消</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 地址选择弹窗 -->
    <el-dialog v-model="addressVisible" title="选择收货地址" width="520px">
      <div v-if="addresses.length" class="addr-list">
        <div
          v-for="addr in addresses"
          :key="addr.id"
          class="addr-item"
          :class="{ selected: selectedAddrId === addr.id }"
          @click="selectedAddrId = addr.id"
        >
          <div class="addr-header">
            <strong>{{ addr.name }}</strong>
            <span class="addr-phone">{{ addr.phone }}</span>
            <el-tag v-if="addr.is_default" size="small" type="warning">默认</el-tag>
          </div>
          <div class="addr-detail">{{ addr.province }}{{ addr.city }}{{ addr.district }} {{ addr.detail }}</div>
        </div>
      </div>
      <el-empty v-else description="暂无地址，请添加" :image-size="60" />
      <el-collapse style="margin-top:16px">
        <el-collapse-item title="添加新地址" name="new">
          <el-form :model="addrForm" label-width="80px">
            <el-form-item label="收货人">
              <el-input v-model="addrForm.name" placeholder="请输入收货人" />
            </el-form-item>
            <el-form-item label="手机号">
              <el-input v-model="addrForm.phone" placeholder="请输入手机号" />
            </el-form-item>
            <el-form-item label="省市区">
              <el-cascader
                v-model="addrForm.region"
                :options="regionData"
                :props="{ value: 'value', label: 'label', children: 'children', emitPath: true }"
                placeholder="请选择省/市/区"
                style="width: 100%"
                clearable
                filterable
              />
            </el-form-item>
            <el-form-item label="详细地址">
              <el-input v-model="addrForm.detail" type="textarea" :rows="2" placeholder="请输入详细地址" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="handleAddAddress">保存地址</el-button>
            </el-form-item>
          </el-form>
        </el-collapse-item>
      </el-collapse>
      <template #footer>
        <el-button @click="addressVisible = false">取消</el-button>
        <el-button type="primary" @click="handleConfirmAddress" :disabled="!selectedAddrId">确认</el-button>
      </template>
    </el-dialog>
  </MainLayout>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Location, Picture, Document, InfoFilled } from '@element-plus/icons-vue'
import MainLayout from '@/components/MainLayout.vue'
import { artisanApi, orderApi } from '@/api/modules'
import { regionData, getRegionText } from '@/utils/regionData'

const route = useRoute()
const router = useRouter()
const order = ref({})
const submitting = ref(false)

// 地址
const addressVisible = ref(false)
const addresses = ref([])
const selectedAddrId = ref(null)
const addrForm = ref({ name: '', phone: '', region: [], detail: '' })
const shippingAddress = ref({ name: '', phone: '', full: '' })

const fmt = (v) => (Number(v) || 0).toFixed(2)

const estimatedDelivery = computed(() => {
  if (!order.value.quote_deadline || !order.value.updated_at) return ''
  const updated = new Date(order.value.updated_at)
  const deadline = order.value.quote_deadline
  const delivery = new Date(updated.getTime() + deadline * 24 * 60 * 60 * 1000)
  return delivery.toLocaleDateString('zh-CN')
})

onMounted(async () => {
  try {
    const id = parseInt(route.params.orderId)
    const res = await artisanApi.getCustomOrder(id)
    order.value = res
    if (order.value.status !== 'accepted' || order.value.pay_status === 'paid') {
      ElMessage.warning('订单状态不正确')
      router.push('/orders')
    }
    // 已有地址则显示
    if (res.receiver_name) {
      shippingAddress.value = {
        name: res.receiver_name,
        phone: res.receiver_phone,
        full: res.receiver_address,
      }
    }
  } catch (err) {
    ElMessage.error('加载订单失败')
    router.push('/orders')
  }
})

const showAddressDialog = async () => {
  try {
    const res = await orderApi.getAddresses()
    addresses.value = res || []
    const def = addresses.value.find(a => a.is_default)
    selectedAddrId.value = def?.id || addresses.value[0]?.id || null
    addressVisible.value = true
  } catch (_) {
    addressVisible.value = true
  }
}

const handleAddAddress = async () => {
  if (!addrForm.value.name || !addrForm.value.phone || !addrForm.value.detail) {
    ElMessage.warning('请填写完整地址信息')
    return
  }
  if (!addrForm.value.region || addrForm.value.region.length < 3) {
    ElMessage.warning('请选择完整的省/市/区')
    return
  }
  try {
    const { province, city, district } = getRegionText(addrForm.value.region)
    await orderApi.createAddress({
      name: addrForm.value.name,
      phone: addrForm.value.phone,
      province,
      city,
      district,
      detail: addrForm.value.detail,
      is_default: addresses.value.length === 0,
    })
    ElMessage.success('地址已保存')
    const res = await orderApi.getAddresses()
    addresses.value = res || []
    addrForm.value = { name: '', phone: '', region: [], detail: '' }
  } catch (err) {
    ElMessage.error('保存地址失败')
  }
}

const handleConfirmAddress = async () => {
  const addr = addresses.value.find(a => a.id === selectedAddrId.value)
  if (!addr) return
  await artisanApi.updateCustomAddress(order.value.id, {
    name: addr.name,
    phone: addr.phone,
    province: addr.province,
    city: addr.city,
    district: addr.district,
    detail: addr.detail,
  })
  shippingAddress.value = {
    name: addr.name,
    phone: addr.phone,
    full: `${addr.province}${addr.city}${addr.district} ${addr.detail}`,
  }
  addressVisible.value = false
}

const handlePay = () => {
  if (!shippingAddress.value.name) {
    ElMessage.warning('请先选择收货地址')
    return
  }
  router.push(`/pay/${order.value.id}?type=custom`)
}
</script>

<style scoped>
.checkout-container {
  max-width: 1000px;
  margin: 0 auto;
  padding: 20px;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 24px;
}

.checkout-content {
  display: grid;
  grid-template-columns: 1fr 360px;
  gap: 24px;
}

.checkout-main {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.section-card {
  background: #fff;
  border-radius: 10px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}

.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 14px;
}

.section-header h3 {
  font-size: 16px;
  font-weight: 600;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 6px;
}

.address-info {
  padding: 12px;
  background: #f8f9fa;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
}
.address-info:hover {
  background: #ecf5ff;
}

.receiver-name { font-weight: 600; margin-right: 12px; }
.receiver-phone { color: #666; }
.address-location { color: #666; margin-top: 6px; font-size: 14px; }
.no-address { color: #999; }

/* 地址弹窗 */
.addr-list {
  max-height: 300px;
  overflow-y: auto;
}
.addr-item {
  padding: 12px;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  margin-bottom: 8px;
  cursor: pointer;
  transition: border-color 0.2s;
}
.addr-item:hover { border-color: #409eff; }
.addr-item.selected { border-color: #409eff; background: #ecf5ff; }
.addr-header { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
.addr-phone { color: #999; font-size: 13px; }
.addr-detail { color: #666; font-size: 13px; }

.image-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
}

.ref-image {
  width: 100%;
  aspect-ratio: 1;
  border-radius: 8px;
  cursor: pointer;
}

.desc-text {
  color: #666;
  font-size: 14px;
  line-height: 1.6;
  margin: 0;
  white-space: pre-wrap;
}

.checkout-sidebar {
  position: sticky;
  top: 20px;
  height: fit-content;
}

.price-card {
  background: #fff;
  border-radius: 10px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
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

@media (max-width: 768px) {
  .checkout-content {
    grid-template-columns: 1fr;
  }
  .checkout-sidebar {
    position: static;
  }
  .image-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>