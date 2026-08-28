<template>
  <MainLayout>
    <div class="container">
      <h2 class="page-title">收货地址管理</h2>
      <div class="card">
        <el-button type="primary" @click="showAddDialog = true">
          <el-icon><Plus /></el-icon>
          新增地址
        </el-button>
        
        <el-table :data="addresses" v-loading="loading" style="width: 100%; margin-top: 16px">
          <el-table-column label="收货人" width="120">
            <template #default="{ row }">{{ row.name }}</template>
          </el-table-column>
          <el-table-column label="手机号" width="130">
            <template #default="{ row }">{{ row.phone }}</template>
          </el-table-column>
          <el-table-column label="所在地区" min-width="200">
            <template #default="{ row }">{{ row.province }} {{ row.city }} {{ row.district }}</template>
          </el-table-column>
          <el-table-column label="详细地址" min-width="250" show-overflow-tooltip>
            <template #default="{ row }">{{ row.detail }}</template>
          </el-table-column>
          <el-table-column label="默认地址" width="100">
            <template #default="{ row }">
              <el-tag v-if="row.is_default" type="success" size="small">默认</el-tag>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="180">
            <template #default="{ row }">
              <el-button type="primary" link size="small" @click="handleEdit(row)">编辑</el-button>
              <el-button 
                v-if="!row.is_default" 
                type="warning" 
                link 
                size="small" 
                @click="handleSetDefault(row.id)"
              >
                设为默认
              </el-button>
              <el-button type="danger" link size="small" @click="handleDelete(row.id)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
        
        <el-empty v-if="!addresses.length && !loading" description="暂无收货地址，请添加" />
      </div>
    </div>
  </MainLayout>

  <!-- 新增/编辑地址对话框 -->
  <el-dialog 
    v-model="showAddDialog" 
    :title="editMode ? '编辑地址' : '新增地址'" 
    width="500px" 
    append-to-body
  >
    <el-form :model="addressForm" label-width="80px" ref="formRef" :rules="rules">
      <el-form-item label="收货人" prop="name">
        <el-input v-model="addressForm.name" placeholder="请输入收货人姓名" />
      </el-form-item>
      <el-form-item label="手机号" prop="phone">
        <el-input v-model="addressForm.phone" placeholder="请输入手机号" maxlength="11" />
      </el-form-item>
      <el-form-item label="省市区" prop="region">
        <el-cascader
          v-model="addressForm.region"
          :options="regionData"
          :props="{ value: 'value', label: 'label', children: 'children', emitPath: true }"
          placeholder="请选择省/市/区"
          style="width: 100%"
          clearable
          filterable
        />
      </el-form-item>
      <el-form-item label="详细地址" prop="detail">
        <el-input 
          v-model="addressForm.detail" 
          type="textarea" 
          :rows="2" 
          placeholder="请输入街道、门牌号等详细地址" 
        />
      </el-form-item>
      <el-form-item label="默认地址">
        <el-switch v-model="addressForm.is_default" />
        <span class="form-tip">设为默认后，下单时将自动使用此地址</span>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="showAddDialog = false">取消</el-button>
      <el-button type="primary" @click="handleSubmit" :loading="submitting">确定</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import MainLayout from '@/components/MainLayout.vue'
import { orderApi } from '@/api/modules'
import { Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { regionData, getRegionText } from '@/utils/regionData'

const addresses = ref([])
const loading = ref(false)
const showAddDialog = ref(false)
const editMode = ref(false)
const editingId = ref(null)
const submitting = ref(false)
const formRef = ref(null)

const addressForm = ref({
  name: '',
  phone: '',
  region: [],
  detail: '',
  is_default: false,
})

const rules = {
  name: [{ required: true, message: '请输入收货人姓名', trigger: 'blur' }],
  phone: [
    { required: true, message: '请输入手机号', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号', trigger: 'blur' }
  ],
  region: [{ required: true, message: '请选择省/市/区', trigger: 'change' }],
  detail: [{ required: true, message: '请输入详细地址', trigger: 'blur' }],
}

const loadAddresses = async () => {
  loading.value = true
  try {
    const res = await orderApi.getAddresses()
    addresses.value = Array.isArray(res) ? res : []
  } catch (err) {
    console.error('加载地址失败:', err)
    addresses.value = []
  } finally {
    loading.value = false
  }
}

onMounted(loadAddresses)

const handleEdit = (row) => {
  editMode.value = true
  editingId.value = row.id
  addressForm.value = {
    name: row.name,
    phone: row.phone,
    region: [row.province, row.city, row.district],
    detail: row.detail,
    is_default: row.is_default,
  }
  showAddDialog.value = true
}

const handleSubmit = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    
    submitting.value = true
    try {
      const { province, city, district } = getRegionText(addressForm.value.region)
      const payload = {
        name: addressForm.value.name,
        phone: addressForm.value.phone,
        province,
        city,
        district,
        detail: addressForm.value.detail,
        is_default: addressForm.value.is_default,
      }
      if (editMode.value) {
        await orderApi.updateAddress(editingId.value, payload)
        ElMessage.success('地址更新成功')
      } else {
        await orderApi.createAddress(payload)
        ElMessage.success('地址添加成功')
      }
      showAddDialog.value = false
      resetForm()
      loadAddresses()
    } catch (err) {
      ElMessage.error(err.detail || err.message || '操作失败')
    } finally {
      submitting.value = false
    }
  })
}

const handleSetDefault = async (id) => {
  try {
    const addr = addresses.value.find(a => a.id === id)
    if (addr) {
      await orderApi.updateAddress(id, { ...addr, is_default: true })
      ElMessage.success('已设为默认地址')
      loadAddresses()
    }
  } catch (err) {
    ElMessage.error(err.detail || err.message || '操作失败')
  }
}

const handleDelete = async (id) => {
  try {
    await ElMessageBox.confirm('确定要删除这个地址吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await orderApi.deleteAddress(id)
    ElMessage.success('删除成功')
    loadAddresses()
  } catch (err) {
    if (err !== 'cancel') {
      ElMessage.error(err.detail || err.message || '删除失败')
    }
  }
}

const resetForm = () => {
  editMode.value = false
  editingId.value = null
  addressForm.value = {
    name: '',
    phone: '',
    region: [],
    detail: '',
    is_default: false,
  }
  if (formRef.value) {
    formRef.value.resetFields()
  }
}
</script>

<style scoped>
.page-title {
  margin: 20px 0;
}

.form-tip {
  font-size: 12px;
  color: var(--color-text-secondary);
  margin-left: 8px;
}
</style>
