<template>
  <MainLayout>
    <div class="home-page">
      <!-- 搜索栏 - 优化后更紧凑 -->
      <div class="search-section">
        <div class="container">
          <div class="search-content">
            <h1 class="search-title">传承非遗文化，发现匠心好物</h1>
            <p class="search-subtitle">每一件作品，都承载着匠人的心血与传承</p>
            <div class="search-box">
              <el-input
                v-model="searchKeyword"
                placeholder="搜索非遗好物..."
                size="large"
                @keyup.enter="handleSearch"
                @input="handleKeywordInput"
                @focus="showSuggestions = true"
                @blur="hideSuggestionsDelayed"
              >
                <template #append>
                  <el-button type="primary" @click="handleSearch">
                    <el-icon><Search /></el-icon>
                  </el-button>
                </template>
              </el-input>

              <!-- 搜索建议下拉框 -->
              <div v-if="showSuggestions && suggestions.length > 0" class="suggestions-dropdown">
                <div
                  v-for="suggestion in suggestions"
                  :key="suggestion"
                  class="suggestion-item"
                  @mousedown.prevent="selectSuggestion(suggestion)"
                >
                  <span v-html="highlightSuggestion(suggestion)"></span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="container">
        <!-- 京东风格分类导航 + 轮播图 -->
        <div class="category-nav-wrapper">
          <!-- 左侧分类列表 -->
          <div class="category-sidebar">
            <div class="sidebar-header">
              <el-icon><Menu /></el-icon>
              <span>分类</span>
            </div>
            <div v-if="isLoadingCategories" class="sidebar-loading">
              <el-skeleton :rows="6" animated />
            </div>
            <div v-else-if="categoryLoadError" class="sidebar-error">
              {{ categoryLoadError }}
            </div>
            <template v-else>
              <div
                v-for="cat in parentCategories"
                :key="cat.id"
                class="sidebar-item"
                :class="{ active: activeCategory === String(cat.id), hover: hoveredCategory === cat.id }"
                @mouseenter="hoveredCategory = cat.id"
                @click="goToCategory(cat.name)"
              >
                <span class="item-name">{{ cat.name }}</span>
                <el-icon v-if="cat.children?.length" class="item-arrow"><ArrowRight /></el-icon>
              </div>
              <div v-if="parentCategories.length === 0" class="sidebar-empty">
                暂无分类
              </div>
            </template>
          </div>

          <!-- 右侧轮播图 -->
          <div class="banner-area">
            <el-carousel height="360px" indicator-position="outside" :interval="5000" arrow="always">
              <el-carousel-item v-for="item in displayBanners" :key="item.id">
                <div v-if="item.image_url" class="banner-item banner-image-mode" @click="handleBannerClick(item)">
                  <el-image
                    :src="item.image_url"
                    fit="contain"
                    class="banner-img"
                    :preview-src-list="[item.image_url]"
                  />
                  <div class="banner-overlay-text" v-if="item.title">
                    <h2>{{ item.title }}</h2>
                  </div>
                </div>
                <div v-else class="banner-item" :style="{ background: item.gradient }">
                  <div class="banner-text">
                    <h2>{{ item.title }}</h2>
                    <p>{{ item.subtitle }}</p>
                  </div>
                  <div class="banner-decoration"></div>
                </div>
              </el-carousel-item>
            </el-carousel>
          </div>

          <!-- 右侧分类详情面板（悬浮） -->
          <div
            class="category-panel"
            v-show="hoveredCategory"
            @mouseenter="hoveredCategory = hoveredCategory"
            @mouseleave="hoveredCategory = null"
          >
            <template v-for="cat in parentCategories" :key="cat.id">
              <div v-if="cat.id === hoveredCategory && cat.children?.length" class="panel-content">
                <div class="panel-section">
                  <div class="panel-section-header" @click.stop="goToCategory(cat.name)">
                    <span class="section-name">{{ cat.name }}</span>
                    <el-icon class="section-arrow"><ArrowRight /></el-icon>
                  </div>
                  <div class="panel-section-body">
                    <div
                      v-for="sub in cat.children"
                      :key="sub.id"
                      class="sub-category-link"
                      @click.stop="goToCategory(sub.name)"
                    >
                      {{ sub.name }}
                    </div>
                  </div>
                </div>
              </div>
            </template>
          </div>
        </div>

        <!-- 推荐商品 -->
        <div class="section">
          <div class="section-header">
            <div class="section-title">
              <span class="title-icon"></span>
              <h2>推荐好物</h2>
            </div>
            <el-radio-group v-model="sortBy" size="default" @change="loadProducts" class="sort-group">
              <el-radio-button label="created_at">最新</el-radio-button>
              <el-radio-button label="sales">销量</el-radio-button>
              <el-radio-button label="price_asc">价格↑</el-radio-button>
              <el-radio-button label="price_desc">价格↓</el-radio-button>
            </el-radio-group>
          </div>

          <div class="product-grid">
            <div
              v-for="(product, index) in products"
              :key="product.id"
              class="product-card"
              :style="{ animationDelay: `${index * 0.05}s` }"
              @click="$router.push(`/product/${product.id}`)"
            >
              <div class="product-image">
                <el-image
                  v-if="product.images?.length"
                  :src="product.images[0]"
                  fit="cover"
                  class="product-img"
                />
                <div v-else class="image-placeholder">
                  <el-icon :size="40"><Picture /></el-icon>
                </div>
                <div class="product-overlay">
                  <el-button
                    size="small"
                    type="primary"
                    circle
                    @click.stop="handleFavorite(product)"
                  >
                    <el-icon><Star /></el-icon>
                  </el-button>
                </div>
              </div>
              <div class="product-info">
                <h4 class="product-name">{{ product.name }}</h4>
                <div class="product-price">
                  <span class="price">¥{{ product.price }}</span>
                  <span v-if="product.original_price" class="original-price">¥{{ product.original_price }}</span>
                </div>
                <div class="product-meta">
                  <span class="sales">已售 {{ product.sales }}</span>
                </div>
              </div>
            </div>
          </div>

          <div v-if="isLoadingProducts" class="loading-state">
            <el-skeleton :rows="3" animated />
          </div>

          <div v-else-if="productLoadError" class="error-state">
            <el-alert :title="productLoadError" type="error" show-icon />
          </div>

          <div v-else-if="products.length === 0" class="empty-state">
            <el-empty description="暂无推荐商品" />
          </div>

          <div class="pagination-wrapper" v-if="total > pageSize">
            <el-pagination
              v-model:current-page="currentPage"
              :page-size="pageSize"
              :total="total"
              layout="prev, pager, next"
              @current-change="loadProducts"
            ></el-pagination>
          </div>
        </div>
      </div>
    </div>
  </MainLayout>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import MainLayout from '@/components/MainLayout.vue'
import { productApi } from '@/api/modules'
import { ElMessage } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import api from '@/api'
import { useRouter } from 'vue-router'
import { searchApi } from '@/api/modules'

const categories = ref([])
const products = ref([])
const activeCategory = ref('')
const searchKeyword = ref('')
const showSuggestions = ref(false)
const suggestions = ref([])
const suggestionTimer = ref(null)
const sortBy = ref('created_at')
const currentPage = ref(1)
const pageSize = ref(12)
const total = ref(0)
const hoveredCategory = ref(null)

const banners = ref([])

// 加载状态
const isLoadingCategories = ref(false)
const isLoadingProducts = ref(false)
const categoryLoadError = ref('')
const productLoadError = ref('')
const bannerLoadError = ref('')

const defaultBanners = [
  {
    id: 1,
    gradient: 'linear-gradient(135deg, #3B4F6B 0%, #5A7090 50%, #7A8FA8 100%)',
    title: '传承非遗文化',
    subtitle: '发现匠心独运的非遗好物'
  },
  {
    id: 2,
    gradient: 'linear-gradient(135deg, #C45C4A 0%, #D4786A 50%, #B8976A 100%)',
    title: '匠人匠心',
    subtitle: '每一件作品都是时间的礼物'
  },
  {
    id: 3,
    gradient: 'linear-gradient(135deg, #7A9B76 0%, #9BB897 50%, #B8976A 100%)',
    title: '非遗好物',
    subtitle: '让传统技艺走进现代生活'
  }
]

const router = useRouter()

const displayBanners = computed(() => {
  if (banners.value.length > 0) return banners.value
  return defaultBanners
})

// 获取一级分类（parent_id 为 null 的分类）
const parentCategories = computed(() => {
  return categories.value.filter(cat => !cat.parent_id)
})

const handleBannerClick = (item) => {
  if (!item.link_url) return

  let url = item.link_url.trim()
  if (!url) return

  // 如果链接是绝对 URL，尝试提取内部路径；如果已经是相对路径则直接使用
  let path = url
  try {
    const parsed = new URL(url)
    // 只处理当前站点或 localhost 开发地址，提取 pathname 走前端路由
    if (parsed.pathname) {
      path = parsed.pathname
    }
  } catch (e) {
    // 不是合法 URL，当作相对路径处理
  }

  // 内部路由跳转（商品详情、课程、搜索、店铺等）
  if (path.startsWith('/') && !path.startsWith('//')) {
    router.push(path)
  } else {
    window.open(url, '_blank')
  }
}

onMounted(async () => {
  await loadBanners()
  await loadCategories()
  await loadProducts()
})

const loadBanners = async () => {
  try {
    bannerLoadError.value = ''
    const res = await api.get('/banners')
    banners.value = res || []
  } catch (err) {
    bannerLoadError.value = '轮播图加载失败，显示默认推荐'
    console.error('加载轮播图失败', err)
  }
}

const loadCategories = async () => {
  isLoadingCategories.value = true
  categoryLoadError.value = ''
  try {
    // 后端已返回树形结构（含Redis缓存）
    const data = await productApi.getCategories()
    categories.value = Array.isArray(data) ? data : []
  } catch (err) {
    categoryLoadError.value = '分类加载失败，请刷新页面重试'
    console.error('加载分类失败', err)
  } finally {
    isLoadingCategories.value = false
  }
}

const loadProducts = async () => {
  isLoadingProducts.value = true
  productLoadError.value = ''
  try {
    const params = {
      skip: (currentPage.value - 1) * pageSize.value,
      limit: pageSize.value,
      sort_by: sortBy.value,
    }
    if (activeCategory.value) {
      params.category_id = parseInt(activeCategory.value)
    }
    if (searchKeyword.value) {
      params.keyword = searchKeyword.value
    }
    const res = await productApi.getProducts(params)
    products.value = res?.items || []
    total.value = res?.total || 0
  } catch (err) {
    productLoadError.value = '商品加载失败，请刷新页面重试'
    products.value = []
    total.value = 0
    console.error('加载商品失败', err)
  } finally {
    isLoadingProducts.value = false
  }
}

const handleCategorySelect = (index) => {
  activeCategory.value = index
  currentPage.value = 1
  hoveredCategory.value = null
  loadProducts()
}

const handleSearch = () => {
  showSuggestions.value = false
  if (searchKeyword.value.trim()) {
    router.push({ path: '/search', query: { keyword: searchKeyword.value.trim() } })
  }
}

// 分类跳转
const goToCategory = (name) => {
  if (name) {
    router.push({ path: '/search', query: { category: name } })
  }
}

// 搜索建议
const handleKeywordInput = () => {
  if (searchKeyword.value.length > 0) {
    if (suggestionTimer.value) clearTimeout(suggestionTimer.value)
    suggestionTimer.value = setTimeout(() => {
      loadSuggestions()
    }, 300)
  } else {
    suggestions.value = []
  }
}

const loadSuggestions = async () => {
  if (!searchKeyword.value) return
  try {
    const response = await searchApi.suggest({
      prefix: searchKeyword.value,
      size: 10,
    })
    if (response.code === 200) {
      suggestions.value = response.data.slice(0, 10)
    }
  } catch (error) {
    console.error('加载搜索建议失败:', error)
  }
}

const selectSuggestion = (suggestion) => {
  searchKeyword.value = suggestion
  showSuggestions.value = false
  handleSearch()
}

const highlightSuggestion = (text) => {
  if (!searchKeyword.value) return text
  const regex = new RegExp(`(${searchKeyword.value})`, 'gi')
  return text.replace(regex, '<strong style="color: #409eff;">$1</strong>')
}

const hideSuggestionsDelayed = () => {
  setTimeout(() => {
    showSuggestions.value = false
  }, 200)
}

const handleFavorite = async (product) => {
  try {
    const res = await productApi.favorite(product.id)
    ElMessage.success(res.action === 'added' ? '已收藏' : '已取消收藏')
  } catch (err) {
    ElMessage.error('操作失败')
  }
}
</script>

<style scoped>
.home-page {
  min-height: 100vh;
}

/* --- Search Section - 优化后更紧凑 --- */
.search-section {
  background: linear-gradient(135deg, #3B4F6B 0%, #5A7090 50%, #7A8FA8 100%);
  padding: 40px 0 36px;
  margin-bottom: 24px;
  position: relative;
}

.search-section::before {
  content: '';
  position: absolute;
  top: -50%;
  right: -10%;
  width: 400px;
  height: 400px;
  background: radial-gradient(circle, rgba(184, 151, 106, 0.15) 0%, transparent 70%);
  border-radius: 50%;
}

.search-section::after {
  content: '';
  position: absolute;
  bottom: -30%;
  left: -5%;
  width: 300px;
  height: 300px;
  background: radial-gradient(circle, rgba(196, 92, 74, 0.1) 0%, transparent 70%);
  border-radius: 50%;
}

.search-content {
  text-align: center;
  position: relative;
  z-index: 1;
}

.search-title {
  font-size: 28px;
  font-weight: 600;
  color: #fff;
  margin: 0 0 8px;
  letter-spacing: 2px;
}

.search-subtitle {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.7);
  margin: 0 0 20px;
}

.search-box {
  max-width: 520px;
  margin: 0 auto;
  position: relative;
}

.suggestions-dropdown {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  right: 0;
  background: #fff;
  border: 1px solid #dcdfe6;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 9999;
  max-height: 360px;
  overflow-y: auto;
  width: 100%;
  box-sizing: border-box;
}

.suggestion-item {
  padding: 10px 16px;
  cursor: pointer;
  font-size: 14px;
  color: #333;
  transition: background 0.15s;
  text-align: left;
}

.suggestion-item span {
  display: block;
  text-align: left;
}

.suggestion-item:hover {
  background: #f5f7fa;
}

.search-box :deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.95) !important;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15) !important;
  border-radius: 8px !important;
}

.search-box :deep(.el-input__inner) {
  font-size: 15px !important;
}

.search-box :deep(.el-input-group__append) {
  background: var(--color-primary) !important;
  border: none !important;
}

.search-box :deep(.el-input-group__append .el-button) {
  background: var(--color-primary) !important;
  border-color: var(--color-primary) !important;
  color: #fff !important;
}

/* --- JD Style Category Navigation + Banner --- */
.category-nav-wrapper {
  position: relative;
  margin-bottom: 24px;
  display: flex;
  gap: 0;
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-md);
}

.category-sidebar {
  width: 200px;
  background: var(--color-primary);
  overflow: hidden;
  flex-shrink: 0;
  z-index: 10;
  border-radius: var(--radius-md) 0 0 var(--radius-md);
}

.sidebar-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: var(--color-primary-dark);
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  letter-spacing: 0.5px;
}

.sidebar-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px;
  cursor: pointer;
  transition: all var(--transition-fast);
  color: rgba(255, 255, 255, 0.85);
  font-size: 13px;
  border-left: 3px solid transparent;
}

.sidebar-item:hover,
.sidebar-item.active,
.sidebar-item.hover {
  background: rgba(255, 255, 255, 0.12);
  color: #fff;
  border-left-color: var(--color-accent);
}

.sidebar-item.active {
  border-left-color: var(--color-accent);
  background: rgba(255, 255, 255, 0.08);
}

.item-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.item-arrow {
  font-size: 12px;
  opacity: 0.6;
}

/* Banner Area */
.banner-area {
  flex: 1;
  border-radius: 0 var(--radius-md) var(--radius-md) 0;
  overflow: hidden;
}

.banner-area :deep(.el-carousel) {
  border-radius: 0 var(--radius-md) var(--radius-md) 0;
}

/* Category Panel - compact overlay */
.category-panel {
  position: absolute;
  top: 0;
  left: 200px;
  height: 360px;
  width: calc(100% - 200px);
  background: var(--color-surface);
  border-radius: 0 var(--radius-md) var(--radius-md) 0;
  box-shadow: var(--shadow-lg);
  z-index: 11;
  padding: 16px 20px;
  overflow-y: auto;
}

.panel-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.panel-section {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.panel-section-header {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 80px;
  padding-top: 2px;
}

.section-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text);
  white-space: nowrap;
}

.section-arrow {
  font-size: 12px;
  color: var(--color-text-light);
}

.panel-section-body {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 12px;
  flex: 1;
}

.sub-category-link {
  font-size: 13px;
  color: var(--color-text-secondary);
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  transition: all var(--transition-fast);
  white-space: nowrap;
}

.sub-category-link:hover {
  color: var(--color-accent);
  background: var(--color-bg-warm);
}

.banner-item {
  height: 360px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  position: relative;
  overflow: hidden;
  cursor: pointer;
}

.banner-image-mode {
  background: var(--color-bg-warm);
}

.banner-img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.banner-img :deep(img) {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.banner-overlay-text {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 20px;
  background: linear-gradient(transparent, rgba(0,0,0,0.6));
  color: #fff;
  text-align: center;
}

.banner-overlay-text h2 {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
  letter-spacing: 2px;
}

.banner-text {
  text-align: center;
  z-index: 1;
}

.banner-text h2 {
  font-size: 36px;
  font-weight: 600;
  margin: 0 0 12px;
  letter-spacing: 3px;
  text-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

.banner-text p {
  font-size: 16px;
  opacity: 0.9;
  margin: 0;
  letter-spacing: 1px;
}

.banner-decoration {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 200px;
  height: 200px;
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 50%;
}

.banner-decoration::before {
  content: '';
  position: absolute;
  top: 20px;
  left: 20px;
  right: 20px;
  bottom: 20px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 50%;
}

/* --- Section --- */
.section {
  margin-bottom: 40px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--color-border-light);
}

.section-title {
  display: flex;
  align-items: center;
  gap: 10px;
}

.title-icon {
  width: 4px;
  height: 20px;
  background: var(--color-accent);
  border-radius: 2px;
}

.section-header h2 {
  font-size: 20px;
  font-weight: 600;
  margin: 0;
  color: var(--color-text);
  letter-spacing: 0.5px;
}

.sort-group {
  display: flex;
}

/* --- Product Grid --- */
.product-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
}

@media (max-width: 1200px) {
  .product-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 768px) {
  .product-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

/* --- Product Card --- */
.product-card {
  background: var(--color-surface);
  border-radius: var(--radius-md);
  overflow: hidden;
  cursor: pointer;
  transition: all var(--transition-base);
  margin-bottom: 20px;
  border: 1px solid var(--color-border-light);
  animation: fadeInUp 0.4s ease forwards;
  opacity: 0;
}

.product-card:hover {
  transform: translateY(-6px);
  box-shadow: var(--shadow-lg);
  border-color: transparent;
}

.product-image {
  position: relative;
  overflow: hidden;
  aspect-ratio: 1;
  background: var(--color-bg-warm);
}

.product-img {
  width: 100%;
  height: 100%;
  transition: transform var(--transition-slow);
}

.product-card:hover .product-img {
  transform: scale(1.05);
}

.image-placeholder {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg-warm);
  color: var(--color-text-light);
}

.product-overlay {
  position: absolute;
  top: 12px;
  right: 12px;
  opacity: 0;
  transform: translateY(-8px);
  transition: all var(--transition-base);
}

.product-card:hover .product-overlay {
  opacity: 1;
  transform: translateY(0);
}

.product-info {
  padding: 14px;
}

.product-name {
  font-size: 14px;
  color: var(--color-text);
  margin: 0 0 10px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-weight: 500;
}

.product-price {
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin-bottom: 8px;
}

.price {
  font-size: 18px;
  color: var(--color-accent);
  font-weight: 600;
}

.original-price {
  font-size: 12px;
  color: var(--color-text-light);
  text-decoration: line-through;
}

.product-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.sales {
  font-size: 12px;
  color: var(--color-text-secondary);
}

/* --- Pagination --- */
.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid var(--color-border-light);
}

/* --- Animations --- */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.sidebar-loading,
.sidebar-error,
.sidebar-empty {
  padding: 16px;
  color: rgba(255, 255, 255, 0.7);
  font-size: 13px;
}

.sidebar-error {
  color: #ffd4d4;
}

.loading-state,
.error-state,
.empty-state {
  padding: 40px 0;
  text-align: center;
}

.error-state {
  max-width: 600px;
  margin: 0 auto;
}

/* --- Responsive --- */
@media (max-width: 768px) {
  .search-section {
    padding: 32px 0 24px;
  }

  .search-title {
    font-size: 22px;
  }

  .search-subtitle {
    font-size: 13px;
  }

  .banner-item {
    height: 200px;
  }

  .banner-text h2 {
    font-size: 24px;
  }

  .section-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  /* 移动端隐藏京东风格分类导航 */
  .category-nav-wrapper {
    display: none;
  }
}
</style>
