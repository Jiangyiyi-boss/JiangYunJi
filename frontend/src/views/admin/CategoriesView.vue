<template>
  <div>
    <h2 class="page-title">分类管理</h2>
    <div class="card">
      <el-button type="primary" @click="showCreate = true">添加分类</el-button>
      <el-table :data="categories" style="width: 100%; margin-top: 16px" row-key="id" :tree-props="{ children: 'children' }">
        <el-table-column prop="name" label="分类名称" min-width="200" />
        <el-table-column prop="icon" label="图标" width="100" />
        <el-table-column prop="sort" label="排序" width="100" />
        <el-table-column prop="level" label="层级" width="80" />
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button type="danger" link @click="handleDelete(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-dialog v-model="showCreate" title="添加分类" width="500px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="分类名称"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="父分类">
          <el-select v-model="form.parent_id" clearable placeholder="顶级分类" style="width: 100%">
            <el-option v-for="cat in categories" :key="cat.id" :label="cat.name" :value="cat.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="图标"><el-input v-model="form.icon" placeholder="Emoji 图标" /></el-form-item>
        <el-form-item label="排序"><el-input-number v-model="form.sort" :min="0" style="width: 100%" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreate = false">取消</el-button>
        <el-button type="primary" @click="handleCreate">添加</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { adminApi } from '@/api/modules'
import { productApi } from '@/api/modules'
import { ElMessage } from 'element-plus'

const categories = ref([])
const showCreate = ref(false)
const form = ref({ name: '', parent_id: null, icon: '', sort: 0 })

const loadCategories = async () => {
  try {
    categories.value = await productApi.getCategories()
  } catch (err) {
    console.error(err)
  }
}

onMounted(loadCategories)

const handleCreate = async () => {
  try {
    await adminApi.createCategory(form.value)
    ElMessage.success('添加成功')
    showCreate.value = false
    loadCategories()
  } catch (err) {
    ElMessage.error('添加失败')
  }
}

const handleDelete = async (id) => {
  try {
    await adminApi.deleteCategory(id)
    ElMessage.success('删除成功')
    loadCategories()
  } catch (err) {
    ElMessage.error('删除失败')
  }
}
</script>

<style scoped>
.page-title { margin: 0 0 20px; font-size: 20px; }
</style>
