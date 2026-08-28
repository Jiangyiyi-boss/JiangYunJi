<template>
  <div>
    <h2 class="page-title">佣金管理</h2>

    <!-- 佣金比例设置 -->
    <el-card class="card" style="margin-bottom: 20px">
      <template #header>
        <div class="card-header">
          <span>佣金比例设置</span>
          <el-button type="primary" size="small" @click="showAddDialog = true">
            <el-icon><Plus /></el-icon> 新增配置
          </el-button>
        </div>
      </template>

      <el-table :data="rates" style="width: 100%" v-loading="loading">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column label="商品分类" width="200">
          <template #default="{ row }">
            <el-tag>{{ row.category_name || '默认' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="佣金比例" width="150">
          <template #default="{ row }">
            <span style="color: #e6a23c; font-weight: bold">{{ (row.rate * 100).toFixed(2) }}%</span>
          </template>
        </el-table-column>
        <el-table-column prop="remark" label="备注" />
        <el-table-column prop="updated_at" label="更新时间" width="180" />
        <el-table-column label="操作" width="180">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="editRate(row)">编辑</el-button>
            <el-button type="danger" size="small" @click="deleteRate(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 佣金申诉列表 -->
    <el-card class="card">
      <template #header>
        <div class="card-header">
          <span>佣金申诉列表</span>
          <el-radio-group v-model="appealFilter" size="small" @change="loadAppeals">
            <el-radio-button label="">全部</el-radio-button>
            <el-radio-button label="pending">待处理</el-radio-button>
            <el-radio-button label="approved">已通过</el-radio-button>
            <el-radio-button label="rejected">已拒绝</el-radio-button>
          </el-radio-group>
        </div>
      </template>

      <el-table :data="appeals" style="width: 100%" v-loading="appealLoading">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="artisan_name" label="匠人" width="120" />
        <el-table-column label="商品/订单" min-width="180">
          <template #default="{ row }">
            <span v-if="row.product_name">{{ row.product_name }}</span>
            <span v-else-if="row.order_no">{{ row.order_no }}</span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="金额" width="100">
          <template #default="{ row }">
            <span v-if="row.product_price">¥{{ row.product_price?.toFixed(2) }}</span>
            <span v-else-if="row.order_amount">¥{{ row.order_amount?.toFixed(2) }}</span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="reason" label="申诉理由" show-overflow-tooltip />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'approved' ? 'success' : row.status === 'rejected' ? 'danger' : 'warning'">
              {{ row.status === 'pending' ? '待处理' : row.status === 'approved' ? '已通过' : '已拒绝' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="admin_note" label="处理意见" show-overflow-tooltip />
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button v-if="row.status === 'pending'" type="primary" size="small" @click="processAppeal(row)">
              处理
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新增/编辑佣金比例对话框 -->
    <el-dialog v-model="showAddDialog" :title="editingRate ? '编辑佣金比例' : '新增佣金比例'" width="500px">
      <el-form :model="rateForm" label-width="100px">
        <el-form-item label="商品分类">
          <el-select v-model="rateForm.category_id" placeholder="选择分类（不选则为默认）" clearable style="width: 100%">
            <el-option
              v-for="cat in categories"
              :key="cat.id"
              :label="cat.name"
              :value="cat.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="佣金比例">
          <el-input-number v-model="rateForm.rate" :min="0" :max="1" :step="0.01" :precision="4" style="width: 100%" />
          <span style="margin-left: 10px; color: #999">{{ (rateForm.rate * 100).toFixed(2) }}%</span>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="rateForm.remark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="saveRate">保存</el-button>
      </template>
    </el-dialog>

    <!-- 处理申诉对话框 -->
    <el-dialog v-model="showProcessDialog" title="处理佣金申诉" width="500px">
      <el-form :model="processForm" label-width="100px">
        <el-form-item label="处理结果">
          <el-radio-group v-model="processForm.status">
            <el-radio label="approved">通过</el-radio>
            <el-radio label="rejected">拒绝</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item v-if="processForm.status === 'approved'" label="调整佣金">
          <el-input-number v-model="processForm.commission_rate" :min="0" :max="1" :step="0.01" :precision="4" style="width: 200px" />
          <span style="margin-left:8px;color:#e6a23c">{{ ((processForm.commission_rate || 0.1) * 100).toFixed(1) }}%</span>
        </el-form-item>
        <el-form-item label="处理意见">
          <el-input v-model="processForm.admin_note" type="textarea" :rows="3" placeholder="请输入处理意见" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showProcessDialog = false">取消</el-button>
        <el-button type="primary" @click="submitProcess">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/api'

const loading = ref(false)
const rates = ref([])
const categories = ref([])
const showAddDialog = ref(false)
const editingRate = ref(null)
const rateForm = ref({ category_id: null, rate: 0.1, remark: '' })

const appealLoading = ref(false)
const appeals = ref([])
const appealFilter = ref('')
const showProcessDialog = ref(false)
const processForm = ref({ status: 'approved', admin_note: '', commission_rate: null })
const processingAppeal = ref(null)

const loadRates = async () => {
  loading.value = true
  try {
    const res = await api.get('/commissions/rates')
    rates.value = res.items || []
  } catch (err) {
    console.error('加载佣金配置失败:', err)
  } finally {
    loading.value = false
  }
}

const loadCategories = async () => {
  try {
    const res = await api.get('/products/categories')
    categories.value = res || []
  } catch (err) {
    console.error('加载分类失败:', err)
  }
}

const loadAppeals = async () => {
  appealLoading.value = true
  try {
    const params = { skip: 0, limit: 50 }
    if (appealFilter.value) params.status = appealFilter.value
    const res = await api.get('/commissions/admin/appeals', { params })
    appeals.value = res.items || []
  } catch (err) {
    console.error('加载申诉列表失败:', err)
    ElMessage.error('加载申诉列表失败')
  } finally {
    appealLoading.value = false
  }
}

const editRate = (row) => {
  editingRate.value = row
  rateForm.value = { category_id: row.category_id, rate: row.rate, remark: row.remark || '' }
  showAddDialog.value = true
}

const saveRate = async () => {
  try {
    if (editingRate.value) {
      await api.put(`/commissions/rates/${editingRate.value.id}`, rateForm.value)
      ElMessage.success('更新成功')
    } else {
      await api.post('/commissions/rates', rateForm.value)
      ElMessage.success('创建成功')
    }
    showAddDialog.value = false
    editingRate.value = null
    rateForm.value = { category_id: null, rate: 0.1, remark: '' }
    loadRates()
  } catch (err) {
    ElMessage.error('操作失败')
  }
}

const deleteRate = async (id) => {
  try {
    await ElMessageBox.confirm('确定删除该佣金配置？', '提示', { type: 'warning' })
    await api.delete(`/commissions/rates/${id}`)
    ElMessage.success('删除成功')
    loadRates()
  } catch (err) {
    if (err !== 'cancel') ElMessage.error('删除失败')
  }
}

const processAppeal = (row) => {
  processingAppeal.value = row
  processForm.value = { status: 'approved', admin_note: '', commission_rate: null }
  showProcessDialog.value = true
}

const submitProcess = async () => {
  try {
    await api.post(`/commissions/admin/appeals/${processingAppeal.value.id}/process`, processForm.value)
    ElMessage.success('处理成功')
    showProcessDialog.value = false
    loadAppeals()
  } catch (err) {
    ElMessage.error('处理失败')
  }
}

onMounted(() => {
  loadRates()
  loadCategories()
  loadAppeals()
})
</script>

<style scoped>
.page-title { margin: 0 0 20px; font-size: 20px; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
</style>
