<template>
  <div class="register-container">
    <div class="register-box">
      <div class="register-header">
        <div class="logo-wrapper">
          <span class="logo-icon">匠</span>
          <h1 class="logo-text">匠韵集</h1>
        </div>
        <p class="subtitle">手机号注册</p>
      </div>

      <!-- 阻止浏览器自动填充 -->
      <input type="text" style="display:none" />
      <input type="password" style="display:none" />

      <el-form :model="form" :rules="rules" ref="formRef" size="large" autocomplete="off">
        <el-form-item prop="phone">
          <el-input v-model="form.phone" placeholder="请输入手机号" :prefix-icon="Iphone" :name="fieldNames.phone" autocomplete="off" />
        </el-form-item>

        <el-form-item prop="code">
          <div class="sms-row">
            <el-input v-model="form.code" placeholder="短信验证码" :prefix-icon="Lock" style="flex:1" :name="fieldNames.code" autocomplete="off" />
            <el-button :disabled="!!smsCountdown" :loading="sending" @click="sendCode" style="min-width:120px;margin-left:8px">
              {{ smsCountdown ? `${smsCountdown}s` : '获取验证码' }}
            </el-button>
          </div>
        </el-form-item>

        <el-form-item prop="password">
          <el-input v-model="form.password" type="password" placeholder="设置密码" :prefix-icon="Lock" show-password :name="fieldNames.pwd" autocomplete="new-password" />
        </el-form-item>
        <div class="pwd-hint">密码长度 6-20 位，需同时包含字母与数字</div>

        <el-form-item prop="confirmPassword">
          <el-input v-model="form.confirmPassword" type="password" placeholder="确认密码" :prefix-icon="Lock" show-password :name="fieldNames.cpwd" autocomplete="new-password" />
        </el-form-item>
        <div class="pwd-hint">请再次输入密码以确认</div>

        <el-form-item prop="agreed">
          <el-checkbox v-model="form.agreed">
            我已阅读并同意 <a href="#" @click.prevent>《用户服务协议》</a>和 <a href="#" @click.prevent>《隐私政策》</a>
          </el-checkbox>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" style="width:100%" :loading="loading" @click="handleRegister">注册</el-button>
        </el-form-item>
      </el-form>

      <div class="register-footer">
        已有账号？<router-link to="/login" class="link">立即登录</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { authApi } from '@/api/modules'
import { ElMessage } from 'element-plus'
import { Iphone, Lock } from '@element-plus/icons-vue'

const router = useRouter()
const userStore = useUserStore()
const formRef = ref()
const loading = ref(false)
const sending = ref(false)
const smsCountdown = ref(0)
let smsTimer = null

// 随机 name 属性，防止 Chrome 自动填充
const rand = Math.random().toString(36).slice(2, 8)
const fieldNames = { phone: `phone_${rand}`, code: `code_${rand}`, pwd: `pwd_${rand}`, cpwd: `cpwd_${rand}` }

const form = reactive({
  phone: '', code: '', password: '', confirmPassword: '', agreed: false,
})

// 挂载时强制清空，防止浏览器残留
onMounted(() => {
  form.phone = ''
  form.code = ''
  form.password = ''
  form.confirmPassword = ''
  form.agreed = false
})

const validateConfirm = (rule, value, callback) => {
  if (value !== form.password) callback(new Error('两次输入的密码不一致'))
  else callback()
}

const rules = {
  phone: [
    { required: true, message: '请输入手机号', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号', trigger: 'blur' },
  ],
  code: [{ required: true, message: '请输入验证码', trigger: 'blur' }],
  password: [
    { required: true, message: '请设置密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度 6-20 位', trigger: 'blur' },
    { pattern: /^(?=.*[a-zA-Z])(?=.*\d)/, message: '需同时包含字母与数字', trigger: 'blur' },
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    { validator: validateConfirm, trigger: 'blur' },
  ],
  agreed: [
    { validator: (rule, value, callback) => { if (!value) callback(new Error('请阅读并同意服务协议与隐私政策')); else callback() }, trigger: 'change' },
  ],
}

const sendCode = async () => {
  if (!/^1[3-9]\d{9}$/.test(form.phone)) { ElMessage.warning('请输入正确的手机号'); return }
  sending.value = true
  try {
    await authApi.sendSms({ phone: form.phone, purpose: 'register' })
    ElMessage.success('验证码已发送')
    smsCountdown.value = 60
    smsTimer = setInterval(() => { smsCountdown.value--; if (smsCountdown.value <= 0) { clearInterval(smsTimer); smsTimer = null } }, 1000)
  } catch (err) { ElMessage.error(err.detail || '发送失败') }
  finally { sending.value = false }
}

const handleRegister = async () => {
  try {
    await formRef.value.validate()
    loading.value = true
    const res = await authApi.register({ phone: form.phone, code: form.code, password: form.password })
    userStore.setToken(res.access_token)
    userStore.setUser(res.user)
    ElMessage.success('注册成功')
    router.push('/home')
  } catch (err) { if (err.detail) ElMessage.error(err.detail || '注册失败') }
  finally { loading.value = false }
}

onUnmounted(() => { if (smsTimer) clearInterval(smsTimer) })
</script>

<style scoped>
.register-container { min-height: 100vh; display: flex; align-items: center; justify-content: center; background: linear-gradient(135deg, #3B4F6B 0%, #5A7090 50%, #7A8FA8 100%); }
.register-box { width: 420px; background: #fff; border-radius: 16px; padding: 40px 36px; box-shadow: 0 20px 60px rgba(0,0,0,0.25); animation: fadeInUp 0.5s ease; }
.register-header { text-align: center; margin-bottom: 28px; }
.logo-wrapper { display: flex; align-items: center; justify-content: center; gap: 12px; margin-bottom: 8px; }
.logo-icon { display: flex; align-items: center; justify-content: center; width: 44px; height: 44px; background: #3B4F6B; color: #fff; font-size: 22px; font-weight: 600; border-radius: 10px; }
.logo-text { font-size: 28px; font-weight: 600; color: #3B4F6B; margin: 0; letter-spacing: 3px; }
.subtitle { color: #999; margin: 0; font-size: 14px; }
.sms-row { display: flex; align-items: center; }
.pwd-hint { color: #aaa; font-size: 12px; margin-top: -16px; margin-bottom: 16px; padding-left: 4px; }
.register-footer { text-align: center; font-size: 14px; color: #999; margin-top: 8px; }
.link { color: #3B4F6B; font-weight: 500; }
@keyframes fadeInUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
@media (max-width: 480px) { .register-box { width: calc(100% - 32px); margin: 16px; padding: 32px 24px; } }
</style>
