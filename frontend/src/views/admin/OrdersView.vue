<template>
  <div>
    <h2 class="page-title">订单管理</h2>
    <div class="card">
      <el-table :data="orders" style="width: 100%">
        <el-table-column prop="order_no" label="订单号" width="200" />
        <el-table-column label="类型" width="80">
          <template #default="{ row }">
            <el-tag size="small" :type="row.goods_type === 2 ? 'success' : ''">{{ row.goods_type === 2 ? '课程' : '商品' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="金额" width="120">
          <template #default="{ row }">¥{{ parseFloat(row.pay_amount || 0).toFixed(2) }}</template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)">{{ statusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="receiver_name" label="收货人" width="120" />
        <el-table-column prop="receiver_phone" label="电话" width="130" />
        <el-table-column prop="created_at" label="创建时间" width="180" />
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { adminApi } from '@/api/modules'

const orders = ref([])

const statusText = (s) => ({ pending: '待付款', paid: '已支付', shipped: '已发货', completed: '已完成', cancelled: '已取消' }[s] || s)
const statusType = (s) => ({ pending: 'danger', paid: 'warning', shipped: 'primary', completed: 'success', cancelled: 'info' }[s] || '')

onMounted(async () => {
  try {
    const res = await adminApi.getAllOrders({ skip: 0, limit: 50 })
    orders.value = res.items || []
  } catch (err) {
    console.error(err)
  }
})
</script>

<style scoped>
.page-title { margin: 0 0 20px; font-size: 20px; }
</style>