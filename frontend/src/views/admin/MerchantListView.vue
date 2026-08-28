<template>
  <div>
    <h2 class="page-title">商家列表</h2>
    <div class="card">
      <div class="filter-bar">
        <el-input
          v-model="keyword"
          placeholder="搜索商家名称/专长"
          clearable
          style="width: 250px"
          @clear="loadMerchants"
          @keyup.enter="loadMerchants"
        >
          <template #append>
            <el-button @click="loadMerchants">搜索</el-button>
          </template>
        </el-input>
      </div>
      <el-table :data="merchants" style="width: 100%" v-loading="loading">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="real_name" label="姓名" width="120" />
        <el-table-column prop="specialty" label="专长" width="150" />
        <el-table-column prop="shop_name" label="店铺名称" width="150" />
        <el-table-column prop="bio" label="简介" min-width="200" show-overflow-tooltip />
        <el-table-column prop="fans_count" label="粉丝数" width="100" />
        <el-table-column label="总销售额" width="120">
          <template #default="{ row }">¥{{ formatNum(row.total_sales) }}</template>
        </el-table-column>
        <el-table-column label="入驻时间" width="180">
          <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button type="primary" link @click="viewDetail(row)">详情</el-button>
            <el-button type="danger" link @click="handleDisable(row.id)">禁用</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div style="margin-top: 16px; text-align: right; color: #999">
        共 {{ total }} 条记录
      </div>
    </div>

    <!-- 详情弹窗 -->
    <el-dialog v-model="detailVisible" title="商家详情" width="600px">
      <el-descriptions :column="2" border v-if="currentMerchant">
        <el-descriptions-item label="姓名">{{ currentMerchant.real_name }}</el-descriptions-item>
        <el-descriptions-item label="专长">{{ currentMerchant.specialty }}</el-descriptions-item>
        <el-descriptions-item label="店铺名称">{{ currentMerchant.shop_name }}</el-descriptions-item>
        <el-descriptions-item label="粉丝数">{{ currentMerchant.fans_count }}</el-descriptions-item>
        <el-descriptions-item label="总销售额">¥{{ formatNum(currentMerchant.total_sales) }}</el-descriptions-item>
        <el-descriptions-item label="简介" :span="2">{{ currentMerchant.bio || '-' }}</el-descriptions-item>
        <el-descriptions-item label="入驻时间" :span="2">{{ formatDate(currentMerchant.created_at) }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { adminApi } from '@/api/modules'
import { ElMessage, ElMessageBox } from 'element-plus'

const formatNum = (v) => { if (!v && v !== 0) return '0'; return Number(v).toFixed(2) }
const formatDate = (d) => d ? d.replace('T', ' ').substring(0, 16) : ''

const merchants = ref([])
const total = ref(0)
const keyword = ref('')
const loading = ref(false)
const detailVisible = ref(false)
const currentMerchant = ref(null)

const loadMerchants = async () => {
  loading.value = true
  try {
    const res = await adminApi.getArtisanApplications({ status: 'approved', keyword: keyword.value, skip: 0, limit: 50 })
    merchants.value = res.items
    total.value = res.total
  } catch (err) {
    console.error(err)
  } finally {
    loading.value = false
  }
}

onMounted(loadMerchants)

const viewDetail = (row) => {
  currentMerchant.value = row
  detailVisible.value = true
}

const handleDisable = async (id) => {
  try {
    await ElMessageBox.confirm('确定要禁用该商家吗？', '提示', { type: 'warning' })
    ElMessage.success('操作成功')
    loadMerchants()
  } catch (err) {
    if (err !== 'cancel') ElMessage.error('操作失败')
  }
}
</script>

<style scoped>
.page-title { margin: 0 0 20px; font-size: 20px; }
.filter-bar { margin-bottom: 16px; }
</style>
