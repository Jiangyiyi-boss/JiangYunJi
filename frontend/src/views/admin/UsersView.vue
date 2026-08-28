<template>
  <div>
    <h2 class="page-title">用户管理</h2>

    <el-card class="card">
      <template #header>
        <div class="card-header">
          <el-input
            v-model="keyword"
            placeholder="搜索用户名/昵称"
            clearable
            style="width: 250px"
            @clear="loadUsers"
            @keyup.enter="loadUsers"
          >
            <template #append>
              <el-button @click="loadUsers">搜索</el-button>
            </template>
          </el-input>
          <div style="display: flex; gap: 10px">
            <el-select v-model="roleFilter" placeholder="角色筛选" clearable style="width: 120px" @change="loadUsers">
              <el-option label="普通用户" value="user" />
              <el-option label="匠人" value="artisan" />
              <el-option label="管理员" value="admin" />
            </el-select>
            <el-select v-model="statusFilter" placeholder="状态筛选" clearable style="width: 120px" @change="loadUsers">
              <el-option label="正常" :value="true" />
              <el-option label="禁用" :value="false" />
            </el-select>
          </div>
        </div>
      </template>

      <el-table :data="users" style="width: 100%" v-loading="loading">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="username" label="用户名" width="150" />
        <el-table-column prop="nickname" label="昵称" width="150" />
        <el-table-column prop="phone" label="手机号" width="150" />
        <el-table-column label="角色" width="100">
          <template #default="{ row }">
            <el-tag :type="row.role === 'admin' ? 'danger' : row.role === 'artisan' ? 'warning' : ''">{{ row.role }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status ? 'success' : 'danger'">{{ row.status ? '正常' : '禁用' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="注册时间" width="180" />
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button
              v-if="row.role !== 'admin'"
              :type="row.status ? 'danger' : 'success'"
              size="small"
              @click="toggleStatus(row)"
            >
              {{ row.status ? '禁用' : '启用' }}
            </el-button>
            <span v-else style="color: #999; font-size: 12px">不可操作</span>
          </template>
        </el-table-column>
      </el-table>

      <div style="margin-top: 16px; text-align: right; color: #999">
        共 {{ total }} 条记录
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/api'

const loading = ref(false)
const users = ref([])
const total = ref(0)
const keyword = ref('')
const roleFilter = ref('')
const statusFilter = ref('')

const loadUsers = async () => {
  loading.value = true
  try {
    const params = { skip: 0, limit: 100 }
    if (keyword.value) params.keyword = keyword.value
    if (roleFilter.value) params.role = roleFilter.value
    if (statusFilter.value !== '') params.status = statusFilter.value
    const res = await api.get('/user/admin/list', { params })
    users.value = res.items || []
    total.value = res.total || 0
  } catch (err) {
    console.error('加载用户列表失败:', err)
    ElMessage.error('加载用户列表失败')
  } finally {
    loading.value = false
  }
}

const toggleStatus = async (row) => {
  const action = row.status ? '禁用' : '启用'
  try {
    await ElMessageBox.confirm(`确定要${action}用户 "${row.username}" 吗？`, '提示', { type: 'warning' })
    await api.put(`/user/admin/${row.id}/status`, { status: !row.status })
    ElMessage.success(`${action}成功`)
    loadUsers()
  } catch (err) {
    if (err !== 'cancel') {
      console.error(err)
      ElMessage.error(`${action}失败`)
    }
  }
}

onMounted(() => {
  loadUsers()
})
</script>

<style scoped>
.page-title { margin: 0 0 20px; font-size: 20px; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
</style>
