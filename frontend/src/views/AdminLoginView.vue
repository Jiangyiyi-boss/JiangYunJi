<template>
  <div class="login-container">
    <div class="login-box">
      <div class="login-header">
        <div class="logo-wrapper">
          <span class="logo-icon">匠</span>
          <h1 class="logo-text">匠韵集</h1>
        </div>
        <p class="subtitle">管理员登录</p>
      </div>
      <input type="text" style="display:none" />
      <input type="password" style="display:none" />
      <el-form :model="form" :rules="rules" ref="formRef" size="large" autocomplete="off" @keyup.enter="handleLogin">
        <el-form-item prop="username">
          <el-input v-model="form.username" placeholder="管理员账号" :prefix-icon="User" />
        </el-form-item>
        <el-form-item prop="password">
          <el-input v-model="form.password" type="password" placeholder="密码" :prefix-icon="Lock" show-password />
        </el-form-item>
        <el-form-item prop="admin_secret">
          <el-input v-model="form.admin_secret" type="password" placeholder="管理员密钥" :prefix-icon="Key" show-password />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" style="width:100%" :loading="loading" @click="handleLogin">管理员登录</el-button>
        </el-form-item>
      </el-form>
      <div class="login-footer">
        <router-link to="/login" class="link">返回用户登录</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { authApi } from '@/api/modules'
import { ElMessage } from 'element-plus'
import { User, Lock, Key } from '@element-plus/icons-vue'

const router = useRouter()
const userStore = useUserStore()
const formRef = ref()
const loading = ref(false)
const form = reactive({ username: '', password: '', admin_secret: '' })
const rules = {
  username: [{ required: true, message: '请输入管理员账号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
  admin_secret: [{ required: true, message: '请输入管理员密钥', trigger: 'blur' }],
}

const handleLogin = async () => {
  try { await formRef.value.validate() } catch { return }
  loading.value = true
  try {
    const res = await authApi.adminLogin(form)
    userStore.setToken(res.access_token)
    userStore.setUser(res.user)
    ElMessage.success('管理员登录成功')
    router.push('/admin')
  } catch (err) { if (err.detail) ElMessage.error(err.detail || '登录失败') }
  finally { loading.value = false }
}
</script>

<style scoped>
.login-container { min-height: 100vh; display: flex; align-items: center; justify-content: center; background: linear-gradient(135deg, #3B4F6B 0%, #5A7090 50%, #7A8FA8 100%); }
.login-box { width: 420px; background: #fff; border-radius: 16px; padding: 40px 36px; box-shadow: 0 20px 60px rgba(0,0,0,0.25); }
.login-header { text-align: center; margin-bottom: 28px; }
.logo-wrapper { display: flex; align-items: center; justify-content: center; gap: 12px; margin-bottom: 8px; }
.logo-icon { display: flex; align-items: center; justify-content: center; width: 44px; height: 44px; background: #3B4F6B; color: #fff; font-size: 22px; font-weight: 600; border-radius: 10px; }
.logo-text { font-size: 28px; font-weight: 600; color: #3B4F6B; margin: 0; letter-spacing: 3px; }
.subtitle { color: #999; margin: 0; font-size: 14px; }
.login-footer { text-align: center; margin-top: 8px; }
.link { color: #3B4F6B; font-size: 14px; font-weight: 500; }
</style>
