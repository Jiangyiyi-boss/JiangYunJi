<template>
  <div>
    <h2 class="page-title">轮播图管理</h2>

    <el-card class="card">
      <template #header>
        <div class="card-header">
          <el-radio-group v-model="filterType" @change="loadBanners">
            <el-radio-button value="">全部</el-radio-button>
            <el-radio-button value="platform_activity">平台活动</el-radio-button>
            <el-radio-button value="platform_pick">平台精选</el-radio-button>
          </el-radio-group>
          <el-button type="primary" @click="showAddDialog">新增轮播图</el-button>
        </div>
      </template>

      <el-table :data="banners" style="width: 100%" v-loading="loading">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="title" label="标题" width="200" show-overflow-tooltip />
        <el-table-column label="图片" width="120">
          <template #default="{ row }">
            <el-image :src="row.image_url" style="width: 80px; height: 50px" fit="cover" />
          </template>
        </el-table-column>
        <el-table-column label="来源" width="120">
          <template #default="{ row }">
            <el-tag :type="sourceTypeTag(row.source_type)">{{ sourceTypeText(row.source_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="排序" width="80" prop="sort" />
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.enabled ? 'success' : 'info'">{{ row.enabled ? '启用' : '禁用' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="有效期" width="200">
          <template #default="{ row }">
            <span v-if="row.start_date && row.end_date">
              {{ formatDate(row.start_date) }} ~ {{ formatDate(row.end_date) }}
            </span>
            <span v-else style="color: #999">不限</span>
          </template>
        </el-table-column>
        <el-table-column prop="link_url" label="链接地址" show-overflow-tooltip />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="showEditDialog(row)">编辑</el-button>
            <el-button :type="row.enabled ? 'warning' : 'success'" link @click="toggleEnabled(row)">
              {{ row.enabled ? '禁用' : '启用' }}
            </el-button>
            <el-button type="danger" link @click="handleDelete(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新增/编辑对话框 -->
    <el-dialog v-model="showDialog" :title="isEdit ? '编辑轮播图' : '新增轮播图'" width="600px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="标题">
          <el-input v-model="form.title" placeholder="轮播图标题" />
        </el-form-item>
        <el-form-item label="图片">
          <el-input v-model="form.image_url" placeholder="图片URL" />
          <el-upload
            action="/api/upload/image"
            :on-success="(res) => form.image_url = res.url"
            :show-file-list="false"
            accept="image/*"
            style="margin-top: 8px"
          >
            <el-button size="small">上传图片</el-button>
          </el-upload>
        </el-form-item>
        <el-form-item label="链接地址">
          <el-input v-model="form.link_url" placeholder="点击跳转链接" />
        </el-form-item>
        <el-form-item label="关联商品">
          <el-select v-model="form.product_id" clearable placeholder="选择关联商品（可选）" style="width: 100%" @change="onProductChange">
            <el-option v-for="p in products" :key="p.id" :label="p.name" :value="p.id">
              <div style="display: flex; align-items: center; gap: 8px">
                <el-image v-if="p.images?.length" :src="p.images[0]" style="width: 30px; height: 30px" fit="cover" />
                <span>{{ p.name }}</span>
                <span style="color: #999; margin-left: auto">¥{{ p.price }}</span>
              </div>
            </el-option>
          </el-select>
          <div style="font-size: 12px; color: #999; margin-top: 4px">关联商品下架时，轮播图会自动禁用</div>
        </el-form-item>
        <el-form-item label="来源类型">
          <el-select v-model="form.source_type" style="width: 100%">
            <el-option label="平台活动" value="platform_activity" />
            <el-option label="平台精选" value="platform_pick" />
          </el-select>
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="form.sort" :min="0" />
        </el-form-item>
        <el-form-item label="有效期">
          <el-date-picker
            v-model="dateRange"
            type="datetimerange"
            start-placeholder="开始时间"
            end-placeholder="结束时间"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitLoading">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '@/api'

const loading = ref(false)
const banners = ref([])
const filterType = ref('')
const showDialog = ref(false)
const isEdit = ref(false)
const submitLoading = ref(false)
const editId = ref(null)
const dateRange = ref([])

const form = ref({
  title: '',
  image_url: '',
  link_url: '',
  product_id: null,
  source_type: 'platform_activity',
  sort: 0,
})

const products = ref([])

const onProductChange = (productId) => {
  if (productId) {
    const product = products.value.find(p => p.id === productId)
    if (product) {
      form.value.link_url = `/product/${productId}`
    }
  }
}

const loadProducts = async () => {
  try {
    const res = await api.get('/products', { params: { limit: 100, status: 'approved' } })
    products.value = res.items || []
  } catch (err) {
    console.error('加载商品列表失败', err)
  }
}

const sourceTypeText = (t) => ({
  platform_activity: '平台活动',
  platform_pick: '平台精选',
}[t] || t)

const sourceTypeTag = (t) => ({
  platform_activity: '',
  platform_pick: 'success',
}[t] || '')

const formatDate = (d) => d ? d.replace('T', ' ').substring(0, 16) : ''

const loadBanners = async () => {
  loading.value = true
  try {
    const params = { skip: 0, limit: 100 }
    if (filterType.value) params.source_type = filterType.value
    const res = await api.get('/banners/admin', { params })
    banners.value = res.items || []
  } catch (err) {
    console.error(err)
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

const showAddDialog = () => {
  isEdit.value = false
  editId.value = null
  form.value = { title: '', image_url: '', link_url: '', source_type: 'platform_activity', sort: 0 }
  dateRange.value = []
  loadProducts()
  showDialog.value = true
}

const showEditDialog = (row) => {
  isEdit.value = true
  editId.value = row.id
  form.value = { ...row }
  dateRange.value = row.start_date && row.end_date ? [row.start_date, row.end_date] : []
  loadProducts()
  showDialog.value = true
}

const handleSubmit = async () => {
  if (!form.value.image_url) {
    ElMessage.warning('请上传图片')
    return
  }
  submitLoading.value = true
  try {
    const data = { ...form.value }
    if (dateRange.value && dateRange.value.length === 2) {
      data.start_date = dateRange.value[0]
      data.end_date = dateRange.value[1]
    }
    if (isEdit.value) {
      await api.put(`/banners/admin/${editId.value}`, data)
      ElMessage.success('编辑成功')
    } else {
      await api.post('/banners/admin', data)
      ElMessage.success('新增成功')
    }
    showDialog.value = false
    loadBanners()
  } catch (err) {
    ElMessage.error('操作失败')
  } finally {
    submitLoading.value = false
  }
}

const toggleEnabled = async (row) => {
  try {
    await api.put(`/banners/admin/${row.id}`, { enabled: !row.enabled })
    ElMessage.success('操作成功')
    loadBanners()
  } catch (err) {
    ElMessage.error('操作失败')
  }
}

const handleDelete = async (id) => {
  try {
    await ElMessageBox.confirm('确定删除该轮播图吗？', '提示', { type: 'warning' })
    await api.delete(`/banners/admin/${id}`)
    ElMessage.success('删除成功')
    loadBanners()
  } catch (err) {
    if (err !== 'cancel') ElMessage.error('删除失败')
  }
}

onMounted(() => loadBanners())
</script>

<style scoped>
.page-title { margin: 0 0 20px; font-size: 20px; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
</style>
