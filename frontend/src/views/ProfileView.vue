<template>
  <MainLayout>
    <div class="profile-page">
      <div class="profile-header">
        <h2 class="page-title">账号管理</h2>
      </div>
      <div class="profile-card">
        <div class="profile-content">
          <!-- 左侧：头像区域 -->
          <div class="avatar-section">
            <el-avatar :size="100" :src="form.avatar" class="avatar-preview">
              {{ form.nickname?.[0] || 'U' }}
            </el-avatar>
            <el-upload
              class="avatar-upload"
              action="#"
              :auto-upload="false"
              :show-file-list="false"
              :on-change="handleAvatarChange"
              accept="image/*"
            >
              <el-button size="small" type="primary" plain>更换头像</el-button>
            </el-upload>
            <p class="avatar-tip">支持 JPG/PNG/WebP，不超过 10MB</p>
          </div>

          <!-- 右侧：表单区域 -->
          <div class="form-section">
            <el-form :model="form" label-width="80px" label-position="left">
              <el-form-item label="账号">
                <el-input v-model="form.username" disabled placeholder="账号不可修改" />
              </el-form-item>
              <el-form-item label="昵称">
                <el-input v-model="form.nickname" placeholder="请输入昵称" maxlength="20" show-word-limit />
              </el-form-item>
              <el-form-item label="手机号">
                <el-input v-model="form.phone" disabled placeholder="手机号不可修改" />
              </el-form-item>
              <el-form-item label="简介">
                <el-input
                  v-model="form.bio"
                  type="textarea"
                  :rows="3"
                  placeholder="介绍一下自己吧~"
                  maxlength="200"
                  show-word-limit
                />
              </el-form-item>
              <el-form-item>
                <el-button type="primary" @click="handleUpdate" :loading="saving">保存修改</el-button>
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
import { useUserStore } from '@/stores/user'
import { userApi, courseApi } from '@/api/modules'
import { ElMessage } from 'element-plus'

const userStore = useUserStore()
const form = ref({ username: '', nickname: '', phone: '', avatar: '', bio: '' })
const originalForm = ref({})
const saving = ref(false)

onMounted(() => {
  loadUserInfo()
})

const loadUserInfo = () => {
  if (userStore.user) {
    const data = {
      username: userStore.user.username || '',
      nickname: userStore.user.nickname || '',
      phone: userStore.user.phone || '',
      avatar: userStore.user.avatar || '',
      bio: userStore.user.bio || '',
    }
    form.value = { ...data }
    originalForm.value = { ...data }
  }
}

const handleReset = () => {
  form.value = { ...originalForm.value }
  ElMessage.info('已重置为原始信息')
}

const handleAvatarChange = async (file) => {
  if (!file.raw) return
  // 校验文件类型和大小
  const allowedTypes = ['image/jpeg', 'image/png', 'image/webp']
  if (!allowedTypes.includes(file.raw.type)) {
    ElMessage.warning('仅支持 JPG/PNG/WebP 格式的图片')
    return
  }
  if (file.raw.size > 10 * 1024 * 1024) {
    ElMessage.warning('图片大小不能超过 10MB')
    return
  }
  try {
    const res = await courseApi.uploadImage(file.raw)
    form.value.avatar = res.url
    ElMessage.success('头像上传成功')
  } catch (err) {
    ElMessage.error('头像上传失败')
  }
}

const handleUpdate = async () => {
  saving.value = true
  try {
    const res = await userApi.updateMe({
      nickname: form.value.nickname,
      phone: form.value.phone,
      avatar: form.value.avatar,
      bio: form.value.bio,
    })
    userStore.setUser(res)
    originalForm.value = { ...form.value }
    ElMessage.success('保存成功')
  } catch (err) {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.profile-page {
  max-width: 900px;
  margin: 0 auto;
  padding: 24px 16px;
}

.profile-header {
  margin-bottom: 24px;
}

.page-title {
  margin: 0;
  font-size: 22px;
  font-weight: 600;
  color: #333;
}

.profile-card {
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  padding: 32px;
}

.profile-content {
  display: flex;
  gap: 48px;
}

.avatar-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  min-width: 160px;
  padding-top: 8px;
}

.avatar-preview {
  border: 3px solid #f0f0f0;
}

.avatar-upload {
  display: inline-block;
}

.avatar-tip {
  font-size: 12px;
  color: #999;
  margin: 0;
  text-align: center;
}

.form-section {
  flex: 1;
  min-width: 0;
}

.form-section :deep(.el-form-item__label) {
  font-weight: 500;
  color: #606266;
}

.form-section :deep(.el-input.is-disabled .el-input__wrapper) {
  background-color: #f5f7fa;
}
</style>
