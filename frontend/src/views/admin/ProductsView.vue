<template>
  <div>
    <h2 class="page-title">商品审核</h2>

    <el-tabs v-model="activeTab" @tab-change="loadProducts">
      <el-tab-pane label="待审核" name="pending" />
      <el-tab-pane label="已通过" name="approved" />
      <el-tab-pane label="审核通过待上架" name="reviewed" />
      <el-tab-pane label="已拒绝" name="rejected" />
    </el-tabs>

    <div class="card">
      <el-table :data="products" style="width: 100%" v-loading="loading">
        <el-table-column prop="name" label="商品名称" min-width="200" show-overflow-tooltip />
        <el-table-column label="价格" width="100">
          <template #default="{ row }">¥{{ row.price }}</template>
        </el-table-column>
        <el-table-column label="分类" width="120">
          <template #default="{ row }">{{ row.category_name || '-' }}</template>
        </el-table-column>
        <el-table-column label="佣金比例" width="100">
          <template #default="{ row }">
            <span v-if="row.commission_rate">{{ (row.commission_rate * 100).toFixed(2) }}%</span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="库存" width="80" prop="stock" />
        <el-table-column label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)">{{ statusText(row.status) }}</el-tag>
            <el-tag v-if="row.listing_mode === 'manual'" type="info" size="small" style="margin-left:4px">手动上架</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="拒绝原因" min-width="150" show-overflow-tooltip>
          <template #default="{ row }">{{ row.reject_reason || '-' }}</template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <template v-if="activeTab === 'pending'">
              <el-button type="success" link @click="showApproveDialog(row)">通过</el-button>
              <el-button type="danger" link @click="handleReject(row)">拒绝</el-button>
            </template>
            <template v-else-if="activeTab === 'approved' || activeTab === 'reviewed'">
              <el-button v-if="row.status === 'approved'" type="warning" link @click="handleOffline(row.id)">下架</el-button>
              <el-button type="info" link @click="viewDetail(row)">详情</el-button>
            </template>
            <template v-else-if="activeTab === 'rejected'">
              <el-button type="info" link @click="viewDetail(row)">详情</el-button>
            </template>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!loading && !products.length" :description="emptyText" />
    </div>

    <!-- 审核通过对话框 -->
    <el-dialog v-model="showApprove" title="审核通过" width="500px">
      <div v-if="selectedProduct" class="approve-info">
        <p><strong>商品名称：</strong>{{ selectedProduct.name }}</p>
        <p><strong>商品分类：</strong>{{ selectedProduct.category_name || '未分类' }}</p>
        <p><strong>商品价格：</strong>¥{{ selectedProduct.price }}</p>
        <el-divider />
        <el-form label-width="120px">
          <el-form-item label="系统匹配佣金比例">
            <span style="color: #e6a23c; font-weight: bold; font-size: 16px">{{ (autoRate * 100).toFixed(2) }}%</span>
          </el-form-item>
          <el-form-item label="佣金比例调整">
            <el-input-number
              v-model="commissionRate"
              :min="0"
              :max="1"
              :step="0.01"
              :precision="4"
              style="width: 200px"
            />
            <span style="margin-left: 10px; color: #999">（0 = 0%，1 = 100%）</span>
          </el-form-item>
          <el-form-item label="预计佣金金额">
            <span style="color: #f56c6c">¥{{ (selectedProduct.price * commissionRate).toFixed(2) }}</span>
          </el-form-item>
          <el-form-item label="商家预计实收">
            <span style="color: #67c23a; font-weight: bold">¥{{ (selectedProduct.price * (1 - commissionRate)).toFixed(2) }}</span>
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <el-button @click="showApprove = false">取消</el-button>
        <el-button type="primary" @click="handleApprove" :loading="approveLoading">确认通过</el-button>
      </template>
    </el-dialog>

    <!-- 拒绝对话框 -->
    <el-dialog v-model="showReject" title="拒绝商品" width="500px">
      <el-form>
        <el-form-item label="拒绝原因">
          <el-input v-model="rejectReason" type="textarea" :rows="3" placeholder="请输入拒绝原因" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showReject = false">取消</el-button>
        <el-button type="danger" @click="confirmReject" :loading="rejectLoading">确认拒绝</el-button>
      </template>
    </el-dialog>

    <!-- 审核详情对话框 -->
    <el-dialog v-model="showDetail" title="审核详情" width="600px">
      <div v-if="selectedProduct" class="detail-info">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="商品名称">{{ selectedProduct.name }}</el-descriptions-item>
          <el-descriptions-item label="价格">¥{{ selectedProduct.price }}</el-descriptions-item>
          <el-descriptions-item label="分类">{{ selectedProduct.category_name }}</el-descriptions-item>
          <el-descriptions-item label="库存">{{ selectedProduct.stock }}</el-descriptions-item>
          <el-descriptions-item label="佣金比例">{{ selectedProduct.commission_rate ? (selectedProduct.commission_rate * 100).toFixed(2) + '%' : '-' }}</el-descriptions-item>
          <el-descriptions-item label="状态">{{ statusText(selectedProduct.status) }}</el-descriptions-item>
          <el-descriptions-item label="拒绝原因" :span="2">{{ selectedProduct.reject_reason || '-' }}</el-descriptions-item>
          <el-descriptions-item label="创建时间" :span="2">{{ selectedProduct.created_at }}</el-descriptions-item>
        </el-descriptions>
        <el-divider />
        <h4>商品描述</h4>
        <p style="color: #666; white-space: pre-wrap">{{ selectedProduct.description || '暂无描述' }}</p>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { adminApi } from '@/api/modules'
import { ElMessage } from 'element-plus'
import api from '@/api'

const activeTab = ref('pending')
const products = ref([])
const loading = ref(false)

const showApprove = ref(false)
const selectedProduct = ref(null)
const autoRate = ref(0.1)
const commissionRate = ref(0.1)
const approveLoading = ref(false)

const showReject = ref(false)
const rejectReason = ref('')
const rejectLoading = ref(false)

const showDetail = ref(false)

const emptyText = computed(() => {
  if (activeTab.value === 'pending') return '暂无待审核商品'
  if (activeTab.value === 'approved') return '暂无已通过商品'
  return '暂无已拒绝商品'
})

const statusText = (s) => ({
  pending: '待审核', approved: '已通过', rejected: '已拒绝', offline: '已下架', reviewed: '审核通过待上架',
}[s] || s)

const statusType = (s) => ({
  pending: 'warning', approved: 'success', rejected: 'danger', offline: 'info', reviewed: '',
}[s] || '')

onMounted(() => {
  loadProducts()
})

const loadProducts = async () => {
  loading.value = true
  try {
    const res = await api.get('/products', {
      params: { skip: 0, limit: 50, status: activeTab.value }
    })
    products.value = res.items || []
  } catch (err) {
    console.error(err)
  } finally {
    loading.value = false
  }
}

const showApproveDialog = async (row) => {
  selectedProduct.value = row
  try {
    const rates = await api.get('/commissions/rates')
    const rateItem = rates.find(r => r.category_id === row.category_id)
    autoRate.value = rateItem ? rateItem.rate : 0.1
  } catch (err) {
    autoRate.value = 0.1
  }
  commissionRate.value = autoRate.value
  showApprove.value = true
}

const handleApprove = async () => {
  approveLoading.value = true
  try {
    await api.post(`/products/${selectedProduct.value.id}/approve`, null, {
      params: { commission_rate: commissionRate.value }
    })
    ElMessage.success('审核通过')
    showApprove.value = false
    loadProducts()
  } catch (err) {
    ElMessage.error('操作失败')
  } finally {
    approveLoading.value = false
  }
}

const handleReject = (row) => {
  selectedProduct.value = row
  rejectReason.value = ''
  showReject.value = true
}

const confirmReject = async () => {
  if (!rejectReason.value.trim()) {
    ElMessage.warning('请输入拒绝原因')
    return
  }
  rejectLoading.value = true
  try {
    await api.post(`/products/${selectedProduct.value.id}/reject`, null, {
      params: { reason: rejectReason.value }
    })
    ElMessage.success('已拒绝')
    showReject.value = false
    loadProducts()
  } catch (err) {
    ElMessage.error('操作失败')
  } finally {
    rejectLoading.value = false
  }
}

const handleOffline = async (id) => {
  try {
    await api.post(`/products/${id}/offline`)
    ElMessage.success('已下架')
    loadProducts()
  } catch (err) {
    ElMessage.error('操作失败')
  }
}

const viewDetail = (row) => {
  selectedProduct.value = row
  showDetail.value = true
}
</script>

<style scoped>
.page-title { margin: 0 0 20px; font-size: 20px; }
.approve-info p { margin: 8px 0; font-size: 14px; }
.detail-info h4 { margin: 12px 0 8px; }
</style>
