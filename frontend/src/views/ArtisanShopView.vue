<template>
  <div class="shop-page">
    <!-- 店铺页专用导航栏（始终显示用户视角） -->
    <header class="shop-header">
      <div class="header-inner container">
        <router-link to="/home" class="logo">
          <span class="logo-icon">匠</span>
          <span class="logo-text">匠韵集</span>
        </router-link>
        <el-button
          v-if="isOwner"
          size="small"
          class="back-btn"
          @click="goBackToDashboard"
        >
          返回商家中心
        </el-button>
      </div>
    </header>

    <!-- 店铺信息区 -->
    <div class="container" v-loading="loading">
      <div class="shop-card" v-if="artisan">
        <div class="shop-card-inner">
          <el-avatar :size="72" :src="artisan.shop_avatar" class="shop-avatar">
            {{ (artisan.shop_name || artisan.real_name)?.[0] }}
          </el-avatar>
          <div class="shop-info">
            <div class="shop-name-row">
              <h1>{{ artisan.shop_name || artisan.real_name }}</h1>
            </div>
            <p class="shop-bio" v-if="artisan.bio">{{ artisan.bio }}</p>
            <div class="shop-stats">
              <span><strong>{{ artisan.fans_count }}</strong> 粉丝</span>
              <span><strong>{{ products.length }}</strong> 商品</span>
            </div>
          </div>
          <div class="shop-actions">
            <el-button
              type="primary"
              plain
              @click="handleCustomClick"
              v-if="!isOwner"
            >
              定制服务
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 定制服务弹窗 -->
    <el-dialog v-model="showCustom" title="发起定制需求" width="520px" :close-on-click-modal="false">
      <el-form :model="customForm" label-width="80px">
        <el-form-item label="需求描述">
          <el-input
            v-model="customForm.description"
            type="textarea"
            :rows="4"
            placeholder="请描述您想要的定制商品，包括材质、尺寸、风格等"
            maxlength="1000"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="预算范围">
          <el-row :gutter="12" style="width:100%">
            <el-col :span="11">
              <el-input-number v-model="customForm.budget_min" :min="0" placeholder="最低" controls-position="right" style="width:100%" />
            </el-col>
            <el-col :span="2" style="text-align:center;line-height:32px">-</el-col>
            <el-col :span="11">
              <el-input-number v-model="customForm.budget_max" :min="0" placeholder="最高" controls-position="right" style="width:100%" />
            </el-col>
          </el-row>
        </el-form-item>
        <el-form-item label="期望交付">
          <el-date-picker
            v-model="customForm.deadline"
            type="date"
            placeholder="选择日期"
            value-format="YYYY-MM-DD"
            style="width:100%"
          />
        </el-form-item>
        <el-form-item label="参考图片">
          <el-upload
            v-model:file-list="refImages"
            action="#"
            list-type="picture-card"
            :auto-upload="false"
            :limit="5"
            accept="image/*"
          >
            <el-icon><Plus /></el-icon>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCustom = false">取消</el-button>
        <el-button type="primary" @click="handleCustomSubmit" :loading="customSubmitting">提交</el-button>
      </template>
    </el-dialog>

    <!-- 公告（如有） -->
    <div class="container" v-if="artisan?.shop_notice">
      <div class="shop-notice">
        <el-icon><Bell /></el-icon>
        <span>{{ artisan.shop_notice }}</span>
      </div>
    </div>

    <!-- 商品/课程 标签切换 -->
    <div class="container">
      <div class="shop-tabs">
        <div :class="['tab-item', { active: activeTab === 'products' }]" @click="activeTab = 'products'">商品</div>
        <div :class="['tab-item', { active: activeTab === 'courses' }]" @click="activeTab = 'courses'">课程</div>
      </div>

      <!-- 商品 -->
      <div v-if="activeTab === 'products'">
        <el-empty v-if="!products.length" description="暂无商品" />
        <el-row v-else :gutter="16">
          <el-col v-for="product in products" :key="product.id" :xs="12" :sm="8" :md="6">
            <div class="product-card" @click="$router.push(`/product/${product.id}`)">
              <div class="product-image">
                <el-image v-if="product.images?.length" :src="product.images[0]" fit="cover" style="width:100%;aspect-ratio:1" />
                <div v-else class="image-placeholder">
                  <el-icon :size="40"><Picture /></el-icon>
                </div>
              </div>
              <div class="product-info">
                <h4>{{ product.name }}</h4>
                <div class="product-bottom">
                  <span class="price">¥{{ product.price }}</span>
                  <span class="sales" v-if="product.sales">已售 {{ product.sales }}</span>
                </div>
              </div>
            </div>
          </el-col>
        </el-row>
      </div>

      <!-- 课程 -->
      <div v-if="activeTab === 'courses'">
        <el-empty v-if="!courses.length" description="暂无课程" />
        <el-row v-else :gutter="16">
          <el-col v-for="c in courses" :key="c.id" :xs="12" :sm="8" :md="6">
            <div class="product-card" @click="$router.push(`/course/${c.id}`)">
              <div class="product-image">
                <el-image v-if="c.cover_image" :src="c.cover_image" fit="cover" style="width:100%;aspect-ratio:1" />
                <div v-else class="image-placeholder">
                  <el-icon :size="40"><VideoCamera /></el-icon>
                </div>
              </div>
              <div class="product-info">
                <h4>{{ c.title }}</h4>
                <div class="product-bottom">
                  <span class="price">{{ c.price > 0 ? '¥' + c.price : '免费' }}</span>
                  <span class="sales" v-if="c.enrolled_count">{{ c.enrolled_count }} 人已学</span>
                </div>
              </div>
            </div>
          </el-col>
        </el-row>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Bell, Picture, Plus, VideoCamera } from '@element-plus/icons-vue'
import { artisanApi, productApi, courseApi } from '@/api/modules'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const userStore = useUserStore()
const artisan = ref(null)
const products = ref([])
const courses = ref([])
const posts = ref([])
const loading = ref(false)

const activeTab = ref('products')

// 定制服务
const showCustom = ref(false)
const customSubmitting = ref(false)
const customForm = ref({ description: '', budget_min: null, budget_max: null, deadline: '' })
const refImages = ref([])

const router = useRouter()

const isOwner = computed(() => {
  if (!userStore.user || !artisan.value) return false
  return userStore.user.id === artisan.value.user_id
})

const goBackToDashboard = () => {
  sessionStorage.removeItem('browse_as_user')
  router.push('/artisan/dashboard')
}

onMounted(async () => {
  loading.value = true
  try {
    artisan.value = await artisanApi.getArtisan(route.params.id)
    if (userStore.user && artisan.value.user_id === userStore.user.id) {
      sessionStorage.setItem('browse_as_user', '1')
    }
    // 默认加载商品
    await loadProducts()
  } catch (err) {
    console.error(err)
  } finally {
    loading.value = false
  }
})

const loadProducts = async () => {
  try {
    const res = await productApi.getProducts({ artisan_id: route.params.id, skip: 0, limit: 50 })
    products.value = res.items || []
  } catch (_) {}
}

const loadCourses = async () => {
  if (courses.value.length) return
  try {
    const res = await courseApi.getCourses({ artisan_id: route.params.id })
    courses.value = res.items || []
  } catch (_) {}
}

watch(activeTab, (tab) => {
  if (tab === 'courses') loadCourses()
})

const requireLogin = () => {
  ElMessageBox.confirm('请先登录，登录后方可操作', '提示', {
    confirmButtonText: '去登录',
    cancelButtonText: '取消',
    type: 'warning',
  }).then(() => router.push({ path: '/login', query: { redirect: router.currentRoute.value.fullPath } })).catch(() => {})
}

const handleCustomClick = () => {
  if (!userStore.token) { requireLogin(); return }
  showCustom.value = true
}

const handleCustomSubmit = async () => {
  if (!userStore.user) {
    ElMessage.warning('请先登录')
    return
  }
  if (!customForm.value.description.trim()) {
    ElMessage.warning('请填写需求描述')
    return
  }
  customSubmitting.value = true
  try {
    // 上传参考图片
    const imageUrls = []
    for (const item of refImages.value) {
      if (item.raw) {
        const res = await courseApi.uploadImage(item.raw)
        imageUrls.push(res.url)
      }
    }
    await artisanApi.createCustomOrder({
      artisan_id: artisan.value.id,
      description: customForm.value.description,
      budget_min: customForm.value.budget_min || null,
      budget_max: customForm.value.budget_max || null,
      deadline: customForm.value.deadline || null,
      reference_images: imageUrls,
    })
    ElMessage.success('定制需求已发送')
    showCustom.value = false
    customForm.value = { description: '', budget_min: null, budget_max: null, deadline: '' }
    refImages.value = []
  } catch (err) {
    ElMessage.error('提交失败')
  } finally {
    customSubmitting.value = false
  }
}
</script>

<style scoped>
.shop-page {
  min-height: 100vh;
  background: #f5f5f5;
  padding-bottom: 40px;
}

/* Header */
.shop-header {
  background: #fff;
  border-bottom: 1px solid #eee;
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-inner {
  display: flex;
  align-items: center;
  height: 60px;
  gap: 40px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.logo-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: #3B4F6B;
  color: #fff;
  font-size: 16px;
  font-weight: 600;
  border-radius: 6px;
}

.logo-text {
  font-size: 18px;
  font-weight: 600;
  color: #3B4F6B;
  letter-spacing: 2px;
}

.nav-links {
  display: flex;
  gap: 28px;
  flex: 1;
}

.nav-item {
  font-size: 14px;
  color: #666;
  transition: color 0.2s;
}

.nav-item:hover,
.nav-item.router-link-active {
  color: #3B4F6B;
  font-weight: 500;
}

.back-btn {
  flex-shrink: 0;
}

/* Shop Card */
.shop-card {
  background: #fff;
  border-radius: 12px;
  padding: 24px;
  margin-top: 20px;
  border: 1px solid #f0f0f0;
}

.shop-card-inner {
  display: flex;
  align-items: center;
  gap: 20px;
}

.shop-avatar {
  flex-shrink: 0;
  border: 2px solid #f0f0f0;
}

.shop-info {
  flex: 1;
  min-width: 0;
}

.shop-name-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 6px;
}

.shop-name-row h1 {
  font-size: 22px;
  font-weight: 600;
  margin: 0;
  color: #333;
}

.shop-bio {
  font-size: 14px;
  color: #999;
  margin: 0 0 10px;
}

.shop-stats {
  display: flex;
  gap: 20px;
  font-size: 13px;
  color: #999;
}

.shop-stats strong {
  color: #333;
  font-size: 15px;
}

.shop-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

/* Notice */
.shop-notice {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #fff;
  border-radius: 12px;
  padding: 14px 20px;
  margin-top: 20px;
  font-size: 14px;
  color: #666;
  border: 1px solid #f0f0f0;
}

.shop-notice .el-icon {
  color: #3B4F6B;
}

/* Section */
.section-title {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin: 24px 0 16px;
}

.section-title h2 {
  font-size: 20px;
  font-weight: 600;
  margin: 0;
  color: #333;
}

.product-count {
  font-size: 13px;
  color: #999;
}

/* Tabs */
.shop-tabs {
  display: flex;
  gap: 0;
  margin-top: 20px;
  border-bottom: 2px solid #f0f0f0;
}

.tab-item {
  padding: 12px 24px;
  font-size: 15px;
  color: #666;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  margin-bottom: -2px;
  transition: color 0.2s, border-color 0.2s;
}

.tab-item:hover {
  color: #3B4F6B;
}

.tab-item.active {
  color: #3B4F6B;
  font-weight: 600;
  border-bottom-color: #3B4F6B;
}

/* Post list */
.post-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 8px;
}

.post-item {
  background: #fff;
  border-radius: 10px;
  padding: 16px 20px;
  cursor: pointer;
  border: 1px solid #f0f0f0;
  transition: box-shadow 0.2s;
}

.post-item:hover {
  box-shadow: 0 2px 12px rgba(0,0,0,0.06);
}

.post-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.post-title {
  font-size: 15px;
  font-weight: 600;
  color: #333;
}

.post-excerpt {
  font-size: 13px;
  color: #999;
  margin: 0 0 8px;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.post-meta {
  font-size: 12px;
  color: #bbb;
  display: flex;
  gap: 16px;
}

/* Custom intro */
.custom-intro {
  margin-top: 8px;
  text-align: center;
  padding: 40px 20px;
}

.custom-intro h3 {
  font-size: 18px;
  margin: 0 0 12px;
  color: #333;
}

.custom-intro p {
  color: #999;
  margin: 0 0 20px;
  max-width: 500px;
  margin-left: auto;
  margin-right: auto;
}

.card {
  background: #fff;
  border-radius: 10px;
  border: 1px solid #f0f0f0;
}

/* Products */
.product-card {
  background: #fff;
  border-radius: 12px;
  overflow: hidden;
  cursor: pointer;
  margin-bottom: 16px;
  transition: transform 0.2s, box-shadow 0.2s;
  border: 1px solid #f0f0f0;
}

.product-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0,0,0,0.1);
}

.image-placeholder {
  aspect-ratio: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f5f5;
  color: #ccc;
}

.product-info {
  padding: 12px 14px;
}

.product-info h4 {
  font-size: 14px;
  margin: 0 0 8px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #333;
}

.product-bottom {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.price {
  color: #e85d5d;
  font-weight: 700;
  font-size: 16px;
}

.sales {
  font-size: 12px;
  color: #bbb;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 16px;
}
</style>
