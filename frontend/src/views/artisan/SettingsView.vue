<template>
  <MainLayout>
    <div class="settings-page">
      <div class="settings-header">
        <h2 class="page-title">店铺设置</h2>
        <p class="page-desc">修改店铺信息后，将即时更新到店铺页面</p>
      </div>

      <div class="settings-card" v-loading="loading">
        <div class="settings-content">
          <!-- 店铺头像 -->
          <div class="image-section">
            <h3 class="section-label">店铺头像</h3>
            <div class="image-upload-area">
              <el-upload
                action="#"
                :auto-upload="false"
                :show-file-list="false"
                :on-change="handleAvatarChange"
                accept="image/*"
              >
                <el-avatar :size="100" :src="form.shop_avatar" class="image-preview">
                  {{ (form.shop_name || '店')?.[0] }}
                </el-avatar>
              </el-upload>
              <p class="image-tip">点击更换店铺头像</p>
            </div>
          </div>

          <!-- 表单区域 -->
          <div class="form-section">
            <el-form :model="form" label-width="100px" label-position="left">
              <el-form-item label="店铺名称">
                <el-input v-model="form.shop_name" placeholder="请输入店铺名称" maxlength="30" show-word-limit />
              </el-form-item>
              <el-form-item label="店铺公告">
                <el-input
                  v-model="form.shop_notice"
                  type="textarea"
                  :rows="3"
                  placeholder="发布店铺公告，如促销活动、发货说明等"
                  maxlength="200"
                  show-word-limit
                />
              </el-form-item>
              <el-form-item label="店铺简介">
                <el-input
                  v-model="form.bio"
                  type="textarea"
                  :rows="4"
                  placeholder="介绍您的店铺、手艺特色和产品风格"
                />
              </el-form-item>
              <el-form-item>
                <el-button type="primary" @click="handleSave" :loading="saving">保存修改</el-button>
                <el-button @click="handleReset">重置</el-button>
              </el-form-item>
            </el-form>
          </div>
        </div>
      </div>
    </div>
  </MainLayout>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import MainLayout from '@/components/MainLayout.vue'
import { artisanApi, courseApi } from '@/api/modules'
import { ElMessage } from 'element-plus'

const loading = ref(false)
const saving = ref(false)
const form = ref({
  shop_name: '',
  shop_avatar: '',
  shop_notice: '',
  bio: '',
})
const originalForm = ref({})

onMounted(() => {
  loadShopInfo()
})

const loadShopInfo = async () => {
  loading.value = true
  try {
    const artisan = await artisanApi.getMy()
    const data = {
      shop_name: artisan.shop_name || '',
      shop_avatar: artisan.shop_avatar || '',
      shop_notice: artisan.shop_notice || '',
      bio: artisan.bio || '',
    }
    form.value = { ...data }
    originalForm.value = { ...data }
  } catch (err) {
    ElMessage.error('加载店铺信息失败')
  } finally {
    loading.value = false
  }
}

const handleAvatarChange = async (file) => {
  if (!file.raw) return
  const allowedTypes = ['image/jpeg', 'image/png', 'image/webp']
  if (!allowedTypes.includes(file.raw.type)) {
    ElMessage.warning('仅支持 JPG/PNG/WebP 格式')
    return
  }
  if (file.raw.size > 10 * 1024 * 1024) {
    ElMessage.warning('图片不能超过 10MB')
    return
  }
  try {
    const res = await courseApi.uploadImage(file.raw)
    form.value.shop_avatar = res.url
    ElMessage.success('店铺头像上传成功')
  } catch (err) {
    ElMessage.error('上传失败')
  }
}

const handleReset = () => {
  form.value = { ...originalForm.value }
  ElMessage.info('已重置')
}

const handleSave = async () => {
  if (!form.value.shop_name.trim()) {
    ElMessage.warning('店铺名称不能为空')
    return
  }
  saving.value = true
  try {
    const res = await artisanApi.updateMy({
      shop_name: form.value.shop_name,
      shop_avatar: form.value.shop_avatar,
      shop_notice: form.value.shop_notice,
      bio: form.value.bio,
    })
    originalForm.value = { ...form.value }
    ElMessage.success('店铺信息已更新')
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.settings-page {
  max-width: 900px;
  margin: 0 auto;
  padding: 24px 16px;
}

.settings-header {
  margin-bottom: 24px;
}

.page-title {
  margin: 0;
  font-size: 22px;
  font-weight: 600;
  color: #333;
}

.page-desc {
  margin: 8px 0 0;
  font-size: 14px;
  color: #999;
}

.settings-card {
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  padding: 32px;
}

.settings-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* 图片上传区域 */
.image-section {
  display: flex;
  align-items: center;
  gap: 20px;
}

.section-label {
  font-size: 14px;
  font-weight: 500;
  color: #606266;
  margin: 0;
  min-width: 100px;
}

.image-upload-area {
  display: flex;
  align-items: center;
  gap: 12px;
}

.image-preview {
  border: 3px solid #f0f0f0;
  cursor: pointer;
  transition: border-color 0.2s;
}

.image-preview:hover {
  border-color: var(--color-primary, #3B4F6B);
}

.image-tip {
  font-size: 12px;
  color: #999;
  margin: 0;
}

/* 表单 */
.form-section {
  border-top: 1px solid #f0f0f0;
  padding-top: 24px;
}

.form-section :deep(.el-form-item__label) {
  font-weight: 500;
  color: #606266;
}

@media (max-width: 768px) {
  .settings-card {
    padding: 20px;
  }

  .image-section {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
