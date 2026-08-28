<template>
  <div>
    <h2 class="page-title">匠人审核</h2>
    <div class="card">
      <el-tabs v-model="status" @tab-click="loadArtisans">
        <el-tab-pane label="待审核" name="pending" />
        <el-tab-pane label="已通过" name="approved" />
        <el-tab-pane label="已拒绝" name="rejected" />
      </el-tabs>
      <el-table :data="artisans" style="width: 100%">
        <el-table-column prop="real_name" label="姓名" width="120" />
        <el-table-column prop="specialty" label="专长" width="150" />
        <el-table-column prop="shop_name" label="店铺名称" width="150" />
        <el-table-column prop="bio" label="简介" min-width="200" show-overflow-tooltip />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'approved' ? 'success' : row.status === 'rejected' ? 'danger' : 'warning'">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="申请时间" width="180" />
        <el-table-column label="操作" width="150" v-if="status === 'pending'">
          <template #default="{ row }">
            <el-button type="success" link @click="handleApprove(row.id)">通过</el-button>
            <el-button type="danger" link @click="handleReject(row.id)">拒绝</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { adminApi } from '@/api/modules'
import { ElMessage, ElMessageBox } from 'element-plus'

const artisans = ref([])
const status = ref('pending')

const loadArtisans = async () => {
  try {
    const res = await adminApi.getArtisanApplications({ status: status.value, skip: 0, limit: 50 })
    artisans.value = res.items
  } catch (err) {
    console.error(err)
  }
}

onMounted(loadArtisans)

const handleApprove = async (id) => {
  try {
    await adminApi.approveArtisan(id)
    ElMessage.success('审核通过')
    loadArtisans()
  } catch (err) {
    ElMessage.error('操作失败')
  }
}

const handleReject = async (id) => {
  try {
    const { value } = await ElMessageBox.prompt('请输入拒绝原因', '拒绝申请', {
      inputPlaceholder: '拒绝原因',
    })
    await adminApi.rejectArtisan(id, value)
    ElMessage.success('已拒绝')
    loadArtisans()
  } catch (err) {
    if (err !== 'cancel') ElMessage.error('操作失败')
  }
}
</script>

<style scoped>
.page-title { margin: 0 0 20px; font-size: 20px; }
</style>
