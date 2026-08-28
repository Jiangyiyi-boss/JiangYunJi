<template>
  <MainLayout>
    <div class="search-page">
      <!-- 搜索栏 -->
      <div class="search-section">
        <div class="container">
          <div class="search-content">
            <h1 class="search-title">传承非遗文化，发现匠心好物</h1>
            <p class="search-subtitle">每一件作品，都承载着匠人的心血与传承</p>
            
            <!-- 搜索框区域 -->
            <div class="search-box-wrapper">
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
                    <el-button type="primary" @click="handleSearch" :loading="isLoading">
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
                    @click="selectSuggestion(suggestion)"
                  >
                    <span v-html="highlightSuggestion(suggestion)"></span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 搜索结果 -->
      <div class="container">
        <div class="results-header" v-if="categoryName || searchKeyword">
          <h2 class="results-title">
            <span v-if="categoryName">{{ categoryName }}</span>
            <span v-if="categoryName && searchKeyword"> · </span>
            <span v-if="searchKeyword">"{{ searchKeyword }}"</span>
          </h2>
          <p class="results-count" v-if="!isLoading">
            共 {{ total }} 件商品
            <span v-if="isFallback" class="fallback-tag">{{ fallbackMessage }}</span>
          </p>
        </div>
        <div class="results-section">
          <div v-if="isLoading" class="loading-state">
            <el-skeleton :rows="4" animated />
          </div>
          
          <div v-else-if="products.length === 0" class="empty-state">
            <el-empty description="暂无搜索结果" />
          </div>
          
          <div v-else class="product-grid">
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
                <h4 class="product-name" v-html="highlightText(product.name)"></h4>
                <div class="product-desc" v-html="highlightText(product.description)"></div>
                <div class="product-price">
                  <span class="price">¥{{ product.price }}</span>
                  <span v-if="product.original_price" class="original-price">¥{{ product.original_price }}</span>
                </div>
                <div class="product-meta">
                  <span class="sales">已售 {{ product.sales }}</span>
                  <span class="category">{{ product.category }}</span>
                </div>
              </div>
            </div>
          </div>
          
          <!-- 加载更多按钮（用于游标分页） -->
          <div v-if="hasMore && !isLoading" class="load-more-container">
            <el-button @click="loadMoreProducts" :loading="isLoadingMore" type="primary" size="large">
              加载更多
            </el-button>
          </div>
        </div>
      </div>
    </div>
  </MainLayout>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import { searchApi } from '@/api/modules'
import { productApi } from '@/api/modules'
import MainLayout from '@/components/MainLayout.vue'

// 搜索状态
const searchKeyword = ref('')
const categoryName = ref('')
const isLoading = ref(false)
const isLoadingMore = ref(false)
const isFallback = ref(false) // 是否使用 MySQL 兜底
const fallbackMessage = ref('') // 兜底提示信息

// 搜索建议
const showSuggestions = ref(false)
const suggestions = ref([])
const suggestionTimer = ref(null)

// 产品列表
const products = ref([])
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const hasMore = ref(false)
const searchAfter = ref(null)

// 路由
const router = useRouter()
const route = useRoute()

// 防抖处理
const debounceTimer = ref(null)

// 页面加载时获取路由参数
onMounted(() => {
  syncFromRoute()
})

// 监听路由参数变化，从 URL 恢复搜索条件并触发搜索
watch(() => route.query, (query) => {
  syncFromRoute(query)
}, { deep: true })

const syncFromRoute = (query = route.query) => {
  const newKeyword = query.keyword || ''
  const newCategory = query.category || ''

  // 避免输入框中的关键词和 URL 参数互相循环触发
  if (newKeyword !== searchKeyword.value) {
    searchKeyword.value = newKeyword
  }
  if (newCategory !== categoryName.value) {
    categoryName.value = newCategory
  }

  // 只要有搜索条件就执行搜索
  if (newKeyword || newCategory) {
    currentPage.value = 1
    searchAfter.value = null
    loadProducts()
  }
}

// 搜索处理
const handleSearch = () => {
  if (debounceTimer.value) {
    clearTimeout(debounceTimer.value)
  }

  debounceTimer.value = setTimeout(() => {
    // 更新 URL 参数，触发 watch 执行搜索
    const params = {}
    if (searchKeyword.value) params.keyword = searchKeyword.value
    if (categoryName.value) params.category = categoryName.value
    router.replace({ query: params })
  }, 300)
}

// 关键词输入防抖
const handleKeywordInput = () => {
  if (searchKeyword.value.length > 0) {
    if (suggestionTimer.value) {
      clearTimeout(suggestionTimer.value)
    }
    
    suggestionTimer.value = setTimeout(() => {
      loadSuggestions()
    }, 300)
  } else {
    suggestions.value = []
  }
}

// 加载搜索建议
const loadSuggestions = async () => {
  if (!searchKeyword.value) return
  
  try {
    const response = await searchApi.suggest({
      prefix: searchKeyword.value,
      size: 10
    })
    
    if (response.code === 200) {
      suggestions.value = response.data.slice(0, 10)
    }
  } catch (error) {
    console.error('加载搜索建议失败:', error)
  }
}

// 选择搜索建议
const selectSuggestion = (suggestion) => {
  searchKeyword.value = suggestion
  showSuggestions.value = false
  handleSearch()
}

// 高亮搜索建议
const highlightSuggestion = (text) => {
  if (!searchKeyword.value) return text
  
  const regex = new RegExp(`(${searchKeyword.value})`, 'gi')
  return text.replace(regex, '<strong style="color: #409eff;">$1</strong>')
}

// 隐藏建议延迟
const hideSuggestionsDelayed = () => {
  setTimeout(() => {
    showSuggestions.value = false
  }, 200)
}

// 高亮文本
const highlightText = (text) => {
  if (!searchKeyword.value || !text) return text
  
  const regex = new RegExp(`(${searchKeyword.value})`, 'gi')
  return text.replace(regex, '<strong style="color: #409eff;">$1</strong>')
}

// 加载产品列表
const loadProducts = async (page = 1) => {
  isLoading.value = true
  isFallback.value = false
  fallbackMessage.value = ''

  try {
    const params = buildSearchParams(page)

    const response = await searchApi.searchProducts(params)

    if (response.code === 200) {
      products.value = response.data.results
      total.value = response.data.total
      hasMore.value = response.data.has_more
      searchAfter.value = response.data.search_after
      isFallback.value = response.data.fallback || false
      if (isFallback.value) {
        fallbackMessage.value = '已切换至 MySQL 兜底搜索'
      }

      // 更新当前页（仅在非游标分页时）
      if (page > 0) {
        currentPage.value = page
      }

      // 显示性能信息
      if (response.data.took_ms) {
        console.log(`搜索耗时: ${response.data.took_ms}ms`)
      }
    } else {
      // 后端返回业务错误时，尝试 MySQL 兜底
      await fallbackToMySQL(page)
    }
  } catch (error) {
    console.error('ES 搜索失败，尝试 MySQL 兜底:', error)
    await fallbackToMySQL(page)
  } finally {
    isLoading.value = false
  }
}

// MySQL 兜底搜索
const fallbackToMySQL = async (page = 1) => {
  try {
    const params = buildMySQLParams(page)
    const res = await productApi.getProducts(params)

    if (res && res.items) {
      products.value = res.items
      total.value = res.total || 0
      hasMore.value = (page * pageSize.value) < total.value
      searchAfter.value = null
      isFallback.value = true
      fallbackMessage.value = '已切换至 MySQL 兜底搜索'
    } else {
      products.value = []
      total.value = 0
      hasMore.value = false
      isFallback.value = true
      fallbackMessage.value = '搜索服务异常，未找到相关商品'
    }
  } catch (error) {
    console.error('MySQL 兜底搜索失败:', error)
    products.value = []
    total.value = 0
    hasMore.value = false
    isFallback.value = true
    fallbackMessage.value = '搜索服务暂不可用，请稍后重试'
    ElMessage.error('搜索服务暂不可用')
  }
}

// 构建 MySQL 兜底参数
const buildMySQLParams = (page) => {
  const params = {
    skip: (page - 1) * pageSize.value,
    limit: pageSize.value,
    status: 'approved',
  }

  // 关键词兜底：MySQL 按商品名模糊匹配
  if (searchKeyword.value) {
    params.keyword = searchKeyword.value
  }

  // 分类兜底由后端 _fallback_search 处理，前端这里不额外处理 category
  // 因为 /products 接口只支持 category_id，不支持 category 名称

  // 排序与 ES 保持一致
  params.sort_by = 'created_at'

  return params
}

// 加载更多产品（游标分页）
const loadMoreProducts = async () => {
  if (!hasMore.value || isLoadingMore.value) return

  isLoadingMore.value = true

  try {
    if (isFallback.value) {
      // 兜底模式使用普通分页
      const nextPage = currentPage.value + 1
      const params = buildMySQLParams(nextPage)
      const res = await productApi.getProducts(params)

      if (res && res.items) {
        products.value = [...products.value, ...res.items]
        total.value = res.total || 0
        hasMore.value = (nextPage * pageSize.value) < total.value
        currentPage.value = nextPage
      }
    } else {
      const params = buildSearchParams(-1) // -1 表示使用游标分页

      const response = await searchApi.searchProducts(params)

      if (response.code === 200) {
        products.value = [...products.value, ...response.data.results]
        total.value = response.data.total
        hasMore.value = response.data.has_more
        searchAfter.value = response.data.search_after
      } else {
        ElMessage.error(response.message || '加载更多失败')
      }
    }
  } catch (error) {
    console.error('加载更多失败:', error)
    ElMessage.error('加载更多失败')
  } finally {
    isLoadingMore.value = false
  }
}

// 构建搜索参数
const buildSearchParams = (page) => {
  let params = {
    size: pageSize.value,
  }

  // 分页参数
  if (page > 0) {
    params.page = page
  } else if (searchAfter.value) {
    params.search_after = JSON.stringify(searchAfter.value)
  }

  // 默认按相关度排序
  params.sort_by = '_score'
  params.sort_order = 'desc'

  // 关键词
  if (searchKeyword.value) {
    params.keyword = searchKeyword.value
  }

  // 来自首页分类导航的分类过滤
  if (categoryName.value) {
    params.category = categoryName.value
  }

  return params
}

// 收藏商品
const handleFavorite = (product) => {
  console.log('收藏商品:', product)
  // 实现收藏逻辑
}
</script>

<style scoped>
.search-page {
  padding: 20px 0;
}

.search-section {
  background: linear-gradient(135deg, #3B4F6B 0%, #5A7090 50%, #7A8FA8 100%);
  padding: 60px 0;
  margin-bottom: 30px;
  color: white;
  position: relative;
  overflow: hidden;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
}

.search-content {
  text-align: center;
}

.search-title {
  font-size: 2.5rem;
  margin-bottom: 10px;
  font-weight: bold;
}

.search-subtitle {
  font-size: 1.1rem;
  opacity: 0.9;
  margin-bottom: 30px;
}

.search-box-wrapper {
  position: relative;
  max-width: 600px;
  margin: 0 auto;
}

.search-box {
  position: relative;
}

.suggestions-dropdown {
  position: absolute;
  top: calc(100% + 5px);
  left: 0;
  right: 0;
  background: white;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  z-index: 1000;
  max-height: 300px;
  overflow-y: auto;
}

.suggestion-item {
  padding: 12px 16px;
  cursor: pointer;
  transition: background-color 0.2s;
  text-align: left;
}

.suggestion-item span {
  display: block;
  text-align: left;
}

.suggestion-item:hover {
  background-color: #f5f7fa;
}

.results-section {
  min-height: 400px;
}

.results-header {
  margin-bottom: 20px;
  padding: 0 4px;
}

.results-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: #333;
  margin: 0 0 8px 0;
}

.results-count {
  color: #666;
  font-size: 0.9rem;
  margin: 0;
}

.fallback-tag {
  display: inline-block;
  margin-left: 10px;
  padding: 2px 8px;
  background: #fdf6ec;
  color: #e6a23c;
  border: 1px solid #faecd8;
  border-radius: 4px;
  font-size: 0.8rem;
}

.loading-state {
  padding: 40px 0;
}

.empty-state {
  padding: 80px 0;
  text-align: center;
}

.product-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
  margin-bottom: 20px;
}

.product-card {
  background: white;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: transform 0.2s, box-shadow 0.2s;
  cursor: pointer;
}

.product-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}

.product-image {
  position: relative;
  height: 200px;
  overflow: hidden;
}

.product-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.image-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f5f7fa;
  color: #909399;
}

.product-overlay {
  position: absolute;
  top: 10px;
  right: 10px;
  opacity: 0;
  transition: opacity 0.2s;
}

.product-card:hover .product-overlay {
  opacity: 1;
}

.product-info {
  padding: 15px;
}

.product-name {
  font-size: 1rem;
  font-weight: bold;
  margin: 0 0 8px 0;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.product-desc {
  font-size: 0.875rem;
  color: #606266;
  margin-bottom: 10px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.product-price {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.price {
  font-size: 1.25rem;
  font-weight: bold;
  color: #f56c6c;
}

.original-price {
  font-size: 0.875rem;
  color: #909399;
  text-decoration: line-through;
}

.product-meta {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
  color: #909399;
}

.load-more-container {
  text-align: center;
  padding: 20px 0;
}
</style>
