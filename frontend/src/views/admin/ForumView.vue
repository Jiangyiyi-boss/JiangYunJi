<template>
  <div>
    <h2 class="page-title">论坛管理</h2>

    <!-- 状态筛选 -->
    <div class="filter-bar">
      <el-radio-group v-model="filterStatus" @change="loadPosts">
        <el-radio-button value="pending">待审核</el-radio-button>
        <el-radio-button value="approved">已通过</el-radio-button>
        <el-radio-button value="rejected">已拒绝</el-radio-button>
        <el-radio-button value="">全部</el-radio-button>
      </el-radio-group>
    </div>

    <div class="card">
      <el-table :data="posts" style="width: 100%" v-loading="loading">
        <el-table-column prop="title" label="标题" min-width="180" show-overflow-tooltip>
          <template #default="{ row }">
            <span v-if="row.title">{{ row.title }}</span>
            <span v-else class="text-muted">{{ (row.content || '').slice(0, 30) }}...</span>
          </template>
        </el-table-column>
        <el-table-column prop="author_nickname" label="作者" width="120" />
        <el-table-column label="分类" width="80" prop="category" />
        <el-table-column label="点赞" width="70" prop="like_count" />
        <el-table-column label="评论" width="70" prop="comment_count" />
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="发布时间" width="170">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <template v-if="row.status === 'pending'">
              <el-button type="success" size="small" @click="handleApprove(row)">通过</el-button>
              <el-button type="danger" size="small" @click="handleReject(row)">拒绝</el-button>
            </template>
            <el-button type="danger" link size="small" @click="handleDelete(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrap" v-if="total > limit">
        <el-pagination
          v-model:current-page="page"
          :page-size="limit"
          :total="total"
          layout="prev, pager, next"
          @current-change="loadPosts"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { adminApi } from '@/api/modules'
import { ElMessage, ElMessageBox } from 'element-plus'

const posts = ref([])
const loading = ref(false)
const filterStatus = ref('pending')
const page = ref(1)
const limit = 20
const total = ref(0)

const statusType = (s) => {
  if (s === 'approved') return 'success'
  if (s === 'rejected') return 'danger'
  return 'warning'
}

const statusLabel = (s) => {
  if (s === 'approved') return '已通过'
  if (s === 'rejected') return '已拒绝'
  if (s === 'pending') return '待审核'
  if (s === 'draft') return '草稿'
  return s
}

const loadPosts = async () => {
  loading.value = true
  try {
    const params = { skip: (page.value - 1) * limit, limit }
    if (filterStatus.value) params.status = filterStatus.value
    const res = await adminApi.getForumPosts(params)
    posts.value = res.items || []
    total.value = res.total || 0
  } catch (err) {
    console.error('加载帖子失败:', err)
    ElMessage.error('加载帖子失败')
  } finally {
    loading.value = false
  }
}

const handleApprove = async (row) => {
  try {
    await adminApi.approveForumPost(row.id)
    ElMessage.success('审核通过')
    loadPosts()
  } catch (err) {
    ElMessage.error('操作失败')
  }
}

const handleReject = async (row) => {
  try {
    const { value: reason } = await ElMessageBox.prompt('请输入拒绝原因（选填）', '拒绝帖子', {
      confirmButtonText: '确认拒绝',
      cancelButtonText: '取消',
      inputType: 'textarea',
      inputPlaceholder: '拒绝原因...',
    })
    await adminApi.rejectForumPost(row.id, reason || '')
    ElMessage.success('已拒绝')
    loadPosts()
  } catch (err) {
    if (err !== 'cancel') ElMessage.error('操作失败')
  }
}

const handleDelete = async (id) => {
  try {
    await ElMessageBox.confirm('确定删除该帖子吗？', '确认删除', { type: 'warning' })
    await adminApi.deleteForumPost(id)
    ElMessage.success('已删除')
    loadPosts()
  } catch (err) {
    if (err !== 'cancel') ElMessage.error('删除失败')
  }
}

const formatTime = (time) => {
  if (!time) return ''
  const d = new Date(time)
  if (isNaN(d.getTime())) return ''
  return d.toLocaleString('zh-CN')
}

// 初始化加载
loadPosts()
</script>

<style scoped>
.page-title { margin: 0 0 16px; font-size: 20px; }
.filter-bar { margin-bottom: 16px; }
.card { background: #fff; border-radius: 8px; padding: 16px; }
.pagination-wrap { display: flex; justify-content: center; margin-top: 16px; }
.text-muted { color: #999; }
</style>
