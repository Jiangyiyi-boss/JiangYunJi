<template>
  <MainLayout>
    <div class="container">
      <h2 class="page-title">商家入驻</h2>

      <!-- Loading -->
      <div class="card" v-if="loading" v-loading="true" style="min-height: 200px" />

      <!-- Approved -->
      <div class="card" v-else-if="appStatus === 'approved'">
        <el-result icon="success" title="入驻申请已通过" sub-title="恭喜！您已成为匠人，现在可以管理您的店铺了">
          <template #extra>
            <el-button type="primary" @click="$router.push('/artisan/dashboard')">进入匠人中心</el-button>
            <el-button @click="$router.push('/artisan/products')">管理商品</el-button>
            <el-button @click="refreshUserInfo">刷新用户信息</el-button>
          </template>
        </el-result>
      </div>

      <!-- Pending -->
      <div class="card" v-else-if="appStatus === 'pending'">
        <el-result icon="info" title="审核中" sub-title="您的入驻申请正在审核中，请耐心等待。我们会尽快处理您的申请。">
          <template #extra>
            <el-button type="primary" @click="$router.push('/home')">返回首页</el-button>
          </template>
        </el-result>
      </div>

      <!-- Rejected -->
      <div class="card" v-else-if="appStatus === 'rejected'">
        <el-result icon="warning" title="申请未通过" :sub-title="'拒绝原因：' + (rejectReason || '未说明')">
          <template #extra>
            <el-button type="primary" @click="handleReapply">重新申请</el-button>
            <el-button @click="$router.push('/home')">返回首页</el-button>
          </template>
        </el-result>
      </div>

      <!-- Application Form -->
      <div class="card" v-else>
        <h3 class="form-title">填写入驻信息</h3>
        <p class="form-desc">提交入驻申请后，平台管理员将对您的信息进行审核。审核通过后，您将成为匠人，可以发布商品、开设课程。</p>
        <el-form :model="form" :rules="rules" ref="formRef" label-width="100px" style="max-width: 600px">
          <el-form-item label="真实姓名" prop="real_name">
            <el-input v-model="form.real_name" placeholder="请输入您的真实姓名" />
          </el-form-item>
          <el-form-item label="身份证号" prop="id_card">
            <el-input v-model="form.id_card" placeholder="请输入身份证号" maxlength="18" />
          </el-form-item>
          <el-form-item label="手艺特长" prop="specialty">
            <el-input v-model="form.specialty" placeholder="例如：景德镇陶瓷、苏绣、木雕、传统糕点、酿酒技艺..." />
          </el-form-item>
          <el-form-item label="店铺名称" prop="shop_name">
            <el-input v-model="form.shop_name" placeholder="请输入您的店铺名称" />
          </el-form-item>
          <el-form-item label="联系方式" prop="contact">
            <el-input v-model="form.contact" placeholder="手机号或微信号" />
          </el-form-item>
          <el-form-item label="个人介绍" prop="bio">
            <el-input v-model="form.bio" type="textarea" :rows="4" placeholder="请介绍您的手艺经历、传承背景、获得的荣誉等" />
          </el-form-item>
          <el-form-item label="资质证书" prop="certifications">
            <el-input v-model="form.certifications" type="textarea" :rows="2" placeholder="请列出您持有的相关证书、荣誉、奖项等（选填）" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" size="large" :loading="submitting" @click="handleSubmit">提交申请</el-button>
            <el-button size="large" @click="$router.push('/home')">取消</el-button>
          </el-form-item>
        </el-form>
      </div>
    </div>
  </MainLayout>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import MainLayout from '@/components/MainLayout.vue'
import { artisanApi } from '@/api/modules'
import { userApi } from '@/api/modules'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'

const router = useRouter()
const userStore = useUserStore()
const loading = ref(true)
const submitting = ref(false)
const appStatus = ref(null)  // null | 'pending' | 'approved' | 'rejected'
const rejectReason = ref('')
const formRef = ref()

const form = reactive({
  real_name: '',
  id_card: '',
  specialty: '',
  shop_name: '',
  contact: '',
  bio: '',
  certifications: '',
})

const rules = {
  real_name: [{ required: true, message: '请输入真实姓名', trigger: 'blur' }],
  id_card: [
    { required: true, message: '请输入身份证号', trigger: 'blur' },
    { pattern: /^\d{17}[\dXx]$/, message: '身份证号格式不正确', trigger: 'blur' },
  ],
  specialty: [{ required: true, message: '请输入手艺特长', trigger: 'blur' }],
  shop_name: [{ required: true, message: '请输入店铺名称', trigger: 'blur' }],
  contact: [{ required: true, message: '请输入联系方式', trigger: 'blur' }],
  bio: [{ required: true, message: '请输入个人介绍', trigger: 'blur' }],
}

onMounted(async () => {
  try {
    const artisan = await artisanApi.getMy()
    if (artisan) {
      appStatus.value = artisan.status
      if (artisan.status === 'rejected') {
        rejectReason.value = artisan.reject_reason || ''
      }
    }
  } catch (err) {
    // 404 means no application yet — show form
    if (err?.status === 404 || err?.response?.status === 404) {
      appStatus.value = null
    } else {
      console.error('Failed to check application status', err)
    }
  } finally {
    loading.value = false
  }
})

const handleSubmit = async () => {
  try {
    await formRef.value.validate()
    submitting.value = true
    await artisanApi.apply({
      real_name: form.real_name,
      id_card: form.id_card,
      specialty: form.specialty,
      shop_name: form.shop_name,
      contact: form.contact,
      bio: form.bio,
      certifications: form.certifications,
    })
    ElMessage.success('申请已提交，请等待审核')
    appStatus.value = 'pending'
  } catch (err) {
    if (err.detail) {
      ElMessage.error(err.detail || '提交失败')
    }
  } finally {
    submitting.value = false
  }
}

const handleReapply = () => {
  appStatus.value = null
  // Pre-fill form from previous rejected data if we had it
}

const refreshUserInfo = async () => {
  try {
    const res = await userApi.getMe()
    userStore.setUser(res)
    ElMessage.success('用户信息已刷新')
  } catch (err) {
    ElMessage.error('刷新失败')
  }
}
</script>

<style scoped>
.page-title { margin: 20px 0; }

.form-title {
  font-size: 18px;
  margin: 0 0 8px;
  color: #333;
}

.form-desc {
  color: #999;
  font-size: 14px;
  margin: 0 0 24px;
  line-height: 1.6;
}
</style>
