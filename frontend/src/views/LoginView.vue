<template>
  <div class="login-container">
    <div class="login-box">
      <div class="login-header">
        <div class="logo-wrapper">
          <span class="logo-icon">匠</span>
          <h1 class="logo-text">匠韵集</h1>
        </div>
        <p class="subtitle">传承非遗文化，发现匠心好物</p>
      </div>

      <!-- 阻止浏览器自动填充 -->
      <input type="text" style="display:none" autocomplete="off" />
      <input type="password" style="display:none" autocomplete="off" />

      <el-tabs v-model="activeTab" class="login-tabs">
        <!-- 密码登录 -->
        <el-tab-pane label="密码登录" name="pwd">
          <el-form :model="pwdForm" :rules="pwdRules" ref="pwdFormRef" autocomplete="off" @keyup.enter="handlePwdLogin">
            <el-form-item prop="phone">
              <el-input v-model="pwdForm.phone" placeholder="请输入手机号或账号" size="large" :prefix-icon="Iphone" :name="`phone_${rand}`" autocomplete="username" />
            </el-form-item>
            <el-form-item prop="password">
              <el-input v-model="pwdForm.password" type="password" placeholder="密码" size="large" :prefix-icon="Lock" show-password :name="`pwd_${rand}`" autocomplete="new-password" />
            </el-form-item>
            <div class="extra-row">
              <el-checkbox v-model="pwdForm.remember">记住登录</el-checkbox>
              <a class="forgot-link" @click="showReset = true">忘记密码</a>
            </div>
            <el-form-item>
              <el-button type="primary" size="large" style="width:100%" :loading="loading" @click="handlePwdLogin">登录</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <!-- 短信登录 -->
        <el-tab-pane label="短信登录" name="sms">
          <el-form :model="smsForm" :rules="smsRules" ref="smsFormRef" autocomplete="off" @keyup.enter="handleSmsLogin">
            <el-form-item prop="phone">
              <el-input v-model="smsForm.phone" placeholder="请输入手机号" size="large" :prefix-icon="Iphone" :name="`sms_phone_${rand}`" autocomplete="off" />
            </el-form-item>
            <el-form-item prop="code">
              <div class="sms-row">
                <el-input v-model="smsForm.code" placeholder="验证码" size="large" :prefix-icon="Lock" style="flex:1" :name="`sms_code_${rand}`" autocomplete="off" />
                <el-button size="large" :disabled="!!smsCountdown" :loading="sending" @click="handleSendSms" style="min-width:120px;margin-left:8px">
                  {{ smsCountdown ? `${smsCountdown}s` : '获取验证码' }}
                </el-button>
              </div>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" size="large" style="width:100%" :loading="loading" @click="handleSmsLogin">登录</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>

      <div class="login-footer">
        <router-link to="/register" class="link">立即注册</router-link>
        <span class="divider">|</span>
        <router-link to="/admin/login" class="link admin-link">管理员登录</router-link>
      </div>
    </div>

    <!-- 忘记密码弹窗 -->
    <el-dialog v-model="showReset" title="重置密码" width="400px" :close-on-click-modal="false">
      <el-form :model="resetForm" :rules="resetRules" ref="resetFormRef" size="large">
        <el-form-item prop="phone">
          <el-input v-model="resetForm.phone" placeholder="请输入注册手机号" autocomplete="off" />
        </el-form-item>
        <el-form-item prop="code">
          <div class="sms-row">
            <el-input v-model="resetForm.code" placeholder="验证码" style="flex:1" autocomplete="off" />
            <el-button :disabled="!!smsCountdown2" :loading="sending2" @click="sendResetSms" style="min-width:120px;margin-left:8px">
              {{ smsCountdown2 ? `${smsCountdown2}s` : '获取验证码' }}
            </el-button>
          </div>
        </el-form-item>
        <el-form-item prop="password">
          <el-input v-model="resetForm.password" type="password" placeholder="新密码（6-20位，含字母和数字）" show-password autocomplete="new-password" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showReset = false">取消</el-button>
        <el-button type="primary" :loading="resetting" @click="handleResetPwd">确认重置</el-button>
      </template>
    </el-dialog>

    <!-- 注册并登录弹窗 -->
    <el-dialog v-model="showRegister" title="注册并登录" width="400px" :close-on-click-modal="false">
      <p style="color:#666;margin-bottom:16px">该手机号尚未注册，请设置密码后完成注册</p>
      <el-form :model="registerForm" :rules="registerRules" ref="registerFormRef" size="large">
        <el-form-item prop="password">
          <el-input v-model="registerForm.password" type="password" placeholder="请设置密码（6-20位，含字母和数字）" show-password autocomplete="new-password" />
        </el-form-item>
        <el-form-item prop="password2">
          <el-input v-model="registerForm.password2" type="password" placeholder="请再次确认密码" show-password autocomplete="new-password" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showRegister = false">取消</el-button>
        <el-button type="primary" :loading="registering" @click="handleRegisterBySms">注册并登录</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { authApi } from '@/api/modules'
import { ElMessage } from 'element-plus'
import { Iphone, Lock } from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const activeTab = ref('pwd')
const loading = ref(false)

// 随机 name 防 Chrome 自动填充
const rand = Math.random().toString(36).slice(2, 8)

// 密码登录
const pwdFormRef = ref()
const pwdForm = reactive({ phone: '', password: '', remember: false })
const pwdRules = {
  phone: [{ required: true, message: '请输入手机号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

// 短信登录
const smsFormRef = ref()
const sending = ref(false)
const smsCountdown = ref(0)
let smsTimer = null
const smsForm = reactive({ phone: '', code: '' })
const smsRules = {
  phone: [
    { required: true, message: '请输入手机号', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号', trigger: 'blur' },
  ],
  code: [{ required: true, message: '请输入验证码', trigger: 'blur' }],
}

const handlePwdLogin = async () => {
  try { await pwdFormRef.value.validate() } catch { return }
  loading.value = true
  try {
    const res = await authApi.login(pwdForm)
    userStore.setToken(res.access_token)
    userStore.setUser(res.user)
    ElMessage.success('登录成功')
    let defaultPath = '/home'
    if (res.user?.role === 'artisan') defaultPath = '/artisan/dashboard'
    else if (res.user?.role === 'admin') defaultPath = '/admin'
    router.push(route.query.redirect || defaultPath)
  } catch (err) { if (err.detail) ElMessage.error(err.detail || '登录失败') }
  finally { loading.value = false }
}

const handleSendSms = async () => {
  if (!/^1[3-9]\d{9}$/.test(smsForm.phone)) { ElMessage.warning('请输入正确的手机号'); return }
  sending.value = true
  try {
    await authApi.sendSms({ phone: smsForm.phone, purpose: 'login' })
    ElMessage.success('验证码已发送')
    smsCountdown.value = 60
    smsTimer = setInterval(() => { smsCountdown.value--; if (smsCountdown.value <= 0) { clearInterval(smsTimer); smsTimer = null } }, 1000)
  } catch (err) { ElMessage.error(err.detail || '发送失败') }
  finally { sending.value = false }
}

const handleSmsLogin = async () => {
  try { await smsFormRef.value.validate() } catch { return }
  loading.value = true
  try {
    const res = await authApi.loginBySms(smsForm)
    if (res.need_register) {
      // 手机号未注册，弹出设置密码对话框
      registerForm.phone = smsForm.phone
      registerForm.code = smsForm.code
      registerForm.password = ''
      registerForm.password2 = ''
      showRegister.value = true
      return
    }
    userStore.setToken(res.access_token)
    userStore.setUser(res.user)
    ElMessage.success('登录成功')
    let defaultPath = '/home'
    if (res.user?.role === 'artisan') defaultPath = '/artisan/dashboard'
    else if (res.user?.role === 'admin') defaultPath = '/admin'
    router.push(route.query.redirect || defaultPath)
  } catch (err) { if (err.detail) ElMessage.error(err.detail || '登录失败') }
  finally { loading.value = false }
}

// 忘记密码
const showReset = ref(false)
const resetFormRef = ref()
const resetting = ref(false)
const sending2 = ref(false)
const smsCountdown2 = ref(0)
let smsTimer2 = null
const resetForm = reactive({ phone: '', code: '', password: '' })
const resetRules = {
  phone: [
    { required: true, message: '请输入手机号', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号', trigger: 'blur' },
  ],
  code: [{ required: true, message: '请输入验证码', trigger: 'blur' }],
  password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度 6-20 位', trigger: 'blur' },
    { pattern: /^(?=.*[a-zA-Z])(?=.*\d)/, message: '需包含字母与数字', trigger: 'blur' },
  ],
}

const sendResetSms = async () => {
  if (!/^1[3-9]\d{9}$/.test(resetForm.phone)) { ElMessage.warning('请输入正确的手机号'); return }
  sending2.value = true
  try {
    await authApi.sendSms({ phone: resetForm.phone, purpose: 'reset' })
    ElMessage.success('验证码已发送')
    smsCountdown2.value = 60
    smsTimer2 = setInterval(() => { smsCountdown2.value--; if (smsCountdown2.value <= 0) { clearInterval(smsTimer2); smsTimer2 = null } }, 1000)
  } catch (err) { ElMessage.error(err.detail || '发送失败') }
  finally { sending2.value = false }
}

const handleResetPwd = async () => {
  try { await resetFormRef.value.validate() } catch { return }
  resetting.value = true
  try {
    await authApi.resetPassword(resetForm)
    ElMessage.success('密码重置成功，请登录')
    showReset.value = false
    pwdForm.phone = resetForm.phone
  } catch (err) { if (err.detail) ElMessage.error(err.detail || '重置失败') }
  finally { resetting.value = false }
}

// 注册并登录（短信登录时手机号未注册）
const showRegister = ref(false)
const registerFormRef = ref()
const registering = ref(false)
const registerForm = reactive({ phone: '', code: '', password: '', password2: '' })
const registerRules = {
  password: [
    { required: true, message: '请设置密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度 6-20 位', trigger: 'blur' },
    { pattern: /^(?=.*[a-zA-Z])(?=.*\d)/, message: '需包含字母与数字', trigger: 'blur' },
  ],
  password2: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== registerForm.password) callback(new Error('两次密码不一致'))
        else callback()
      },
      trigger: 'blur',
    },
  ],
}

const handleRegisterBySms = async () => {
  try { await registerFormRef.value.validate() } catch { return }
  registering.value = true
  try {
    const res = await authApi.registerBySms({
      phone: registerForm.phone,
      code: registerForm.code,
      password: registerForm.password,
    })
    userStore.setToken(res.access_token)
    userStore.setUser(res.user)
    ElMessage.success('注册成功')
    showRegister.value = false
    let defaultPath = '/home'
    if (res.user?.role === 'artisan') defaultPath = '/artisan/dashboard'
    else if (res.user?.role === 'admin') defaultPath = '/admin'
    router.push(route.query.redirect || defaultPath)
  } catch (err) { if (err.detail) ElMessage.error(err.detail || '注册失败') }
  finally { registering.value = false }
}

onMounted(() => {
  pwdForm.phone = ''; pwdForm.password = ''; pwdForm.remember = false
  smsForm.phone = ''; smsForm.code = ''
})

onUnmounted(() => {
  if (smsTimer) clearInterval(smsTimer)
  if (smsTimer2) clearInterval(smsTimer2)
})
</script>

<style scoped>
.login-container { min-height: 100vh; display: flex; align-items: center; justify-content: center; background: linear-gradient(135deg, #3B4F6B 0%, #5A7090 50%, #7A8FA8 100%); position: relative; overflow: hidden; }
.login-box { width: 420px; background: #fff; border-radius: 16px; padding: 40px 36px; box-shadow: 0 20px 60px rgba(0,0,0,0.25); position: relative; z-index: 1; animation: fadeInUp 0.5s ease; }
.login-header { text-align: center; margin-bottom: 24px; }
.logo-wrapper { display: flex; align-items: center; justify-content: center; gap: 12px; margin-bottom: 8px; }
.logo-icon { display: flex; align-items: center; justify-content: center; width: 44px; height: 44px; background: #3B4F6B; color: #fff; font-size: 22px; font-weight: 600; border-radius: 10px; }
.logo-text { font-size: 28px; font-weight: 600; color: #3B4F6B; margin: 0; letter-spacing: 3px; }
.subtitle { color: #999; margin: 0; font-size: 14px; }
.login-tabs :deep(.el-tabs__header) { margin-bottom: 20px; }
.login-tabs :deep(.el-tabs__nav-wrap::after) { height: 1px; }
.sms-row { display: flex; align-items: center; }
.extra-row { display: flex; justify-content: space-between; align-items: center; margin-top: -8px; margin-bottom: 16px; }
.forgot-link { color: #3B4F6B; font-size: 13px; cursor: pointer; }
.forgot-link:hover { text-decoration: underline; }
.login-footer { display: flex; justify-content: center; align-items: center; gap: 12px; }
.link { color: #3B4F6B; font-size: 14px; font-weight: 500; }
.divider { color: #ddd; }
.admin-link { font-size: 12px; color: #bbb; }
@keyframes fadeInUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
@media (max-width: 480px) { .login-box { width: calc(100% - 32px); margin: 16px; padding: 32px 24px; } }
</style>
