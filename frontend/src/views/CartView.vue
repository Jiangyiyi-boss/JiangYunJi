<template>
  <MainLayout>
    <div class="container">
      <h2 class="page-title">购物车</h2>
      <div class="card" v-loading="loading">
        <el-table :data="cartItems" style="width: 100%">
          <el-table-column label="商品" min-width="300">
            <template #default="{ row }">
              <div class="cart-item">
                <el-image v-if="row.product?.images?.length" :src="row.product.images[0]" style="width: 80px; height: 80px" fit="cover" />
                <div class="cart-item-info">
                  <span class="cart-item-name">{{ row.product?.name }}</span>
                  <span v-if="row.spec_name" class="cart-item-spec">规格: {{ row.spec_name }}</span>
                </div>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="单价" width="120">
            <template #default="{ row }">¥{{ row.spec_price || row.product?.price }}</template>
          </el-table-column>
          <el-table-column label="数量" width="150">
            <template #default="{ row }">
              <el-input-number v-model="row.qty" :min="1" :max="row.product?.stock ?? 99" size="small" @change="updateQty(row)" />
            </template>
          </el-table-column>
          <el-table-column label="小计" width="120">
            <template #default="{ row }">¥{{ ((row.spec_price || row.product?.price) * row.qty).toFixed(2) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="80">
            <template #default="{ row }">
              <el-button type="danger" link @click="removeItem(row.id)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
        <div class="cart-footer" v-if="cartItems.length">
          <div>
            <span>合计：</span>
            <span class="total-price">¥{{ totalPrice }}</span>
          </div>
          <el-button type="primary" size="large" @click="handleCheckout">结算</el-button>
        </div>
        <el-empty v-else description="购物车是空的" />
      </div>
    </div>
  </MainLayout>

</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import MainLayout from '@/components/MainLayout.vue'
import { orderApi } from '@/api/modules'
import { ElMessage } from 'element-plus'

const router = useRouter()

const cartItems = ref([])
const loading = ref(false)

const totalPrice = computed(() => {
  return cartItems.value.reduce((sum, item) => {
    const price = item.spec_price || item.product?.price || 0
    return sum + price * item.qty
  }, 0).toFixed(2)
})

const loadCart = async () => {
  loading.value = true
  try {
    cartItems.value = await orderApi.getCart()
  } catch (err) {
    console.error(err)
  } finally {
    loading.value = false
  }
}

onMounted(loadCart)

const updateQty = async (item) => {
  try {
    await orderApi.updateCart(item.id, item.qty)
  } catch (err) {
    loadCart()
  }
}

const removeItem = async (id) => {
  try {
    await orderApi.removeCart(id)
    ElMessage.success('已删除')
    loadCart()
  } catch (err) {
    ElMessage.error('删除失败')
  }
}

const handleCheckout = async () => {
  checkingOut.value = true
  try {
    // 获取用户已有地址
    try {
      const addresses = await orderApi.getAddresses()
      existingAddresses.value = Array.isArray(addresses) ? addresses : []
    } catch (addrErr) {
      console.warn('获取地址失败:', addrErr)
      existingAddresses.value = []
    }

    // 如果有地址，选中第一个；否则清空选择
    if (existingAddresses.value.length > 0) {
      const defaultAddr = existingAddresses.value.find(a => a.is_default)
      selectedAddressId.value = defaultAddr ? defaultAddr.id : existingAddresses.value[0].id
    } else {
      selectedAddressId.value = null
    }

    // 重置新增地址表单
    addressForm.value = {
      name: '',
      phone: '',
      province: '',
      city: '',
      district: '',
      detail: '',
      is_default: false,
    }

    // 弹出地址选择对话框
    showAddressDialog.value = true
  } catch (err) {
    console.error('准备结算失败:', err)
    ElMessage.error('请稍后重试')
  } finally {
    checkingOut.value = false
  }
}

const handleConfirmAddressAndCheckout = async () => {
  checkingOut.value = true
  try {
    let addressId = null

    // 判断是选择已有地址还是使用新地址
    if (selectedAddressId.value) {
      // 使用已有地址
      addressId = selectedAddressId.value
    } else {
      // 验证新地址表单
      if (!addressForm.value.name || !addressForm.value.phone || !addressForm.value.detail) {
        ElMessage.error('请填写完整的新地址信息，或选择已有地址')
        return
      }
      if (!/^1[3-9]\d{9}$/.test(addressForm.value.phone)) {
        ElMessage.error('请输入正确的手机号')
        return
      }
      // 创建新地址
      const newAddress = await orderApi.createAddress(addressForm.value)
      addressId = newAddress.id
    }

    // 创建订单（但不支付）
    const items = cartItems.value.map(item => ({
      product_id: item.product_id,
      qty: item.qty,
      spec_name: item.spec_name || '',
      spec_price: item.spec_price,
    }))
    const order = await orderApi.createOrder({ items, address_id: addressId })
    
    ElMessage.success('订单创建成功，正在跳转支付...')
    showAddressDialog.value = false
    
    // 跳转到支付页面
    router.push(`/pay/${order.id}`)
  } catch (err) {
    console.error('下单失败:', err)
    const msg = err?.detail || err?.message || '下单失败，请稍后重试'
    ElMessage.error(msg)
  } finally {
    checkingOut.value = false
  }
}

</script>

<style scoped>
.page-title {
  margin: 20px 0;
}

.cart-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.cart-item-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.cart-item-name {
  font-weight: 500;
}

.cart-item-spec {
  font-size: 12px;
  color: var(--color-text-secondary);
}

.cart-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #eee;
}

.total-price {
  font-size: 24px;
  color: #f56c6c;
  font-weight: bold;
}
</style>
