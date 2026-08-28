<template>
  <MainLayout>
    <div class="product-detail-page">
      <div class="container" v-loading="loading">
        <div class="product-detail" v-if="product">
          <el-row :gutter="40">
            <el-col :xs="24" :md="12">
              <div class="product-gallery">
                <div class="gallery-main" @mouseenter="stopCarousel" @mouseleave="startCarousel">
                  <transition name="carousel-fade" mode="out-in">
                    <el-image v-if="product.images?.length" :key="currentImage" :src="product.images[currentImage]" fit="cover" class="gallery-image" />
                    <div v-else class="gallery-placeholder"><el-icon :size="60"><Picture /></el-icon></div>
                  </transition>
                  <div v-if="product.images?.length > 1" class="gallery-arrow gallery-arrow-left" @click="prevImage"><el-icon :size="22"><ArrowLeft /></el-icon></div>
                  <div v-if="product.images?.length > 1" class="gallery-arrow gallery-arrow-right" @click="nextImage"><el-icon :size="22"><ArrowRight /></el-icon></div>
                  <div class="gallery-dots" v-if="product.images?.length > 1"><span v-for="(_img, i) in product.images" :key="i" class="dot" :class="{ active: currentImage === i }" @click="currentImage = i"></span></div>
                </div>
                <div class="gallery-thumbs" v-if="product.images?.length > 1">
                  <div v-for="(img, i) in product.images" :key="i" class="thumb-item" :class="{ active: currentImage === i }" @click="currentImage = i"><el-image :src="img" fit="cover" /></div>
                </div>
              </div>
            </el-col>

            <el-col :xs="24" :md="12">
              <div class="product-info">
                <div class="info-header">
                  <span class="category-tag" v-if="product.category_name">{{ product.category_name }}</span>
                  <h1 class="product-title">{{ product.name }}</h1>
                </div>

                <div class="product-price-box">
                  <span class="current-price">¥{{ selectedSpec?.price || product.price }}</span>
                  <span v-if="product.specs?.length > 1 && !selectedSpec" class="qiyi">起</span>
                </div>

                <div class="shipping-bar" v-if="product.shipping_type || product.ship_time || product.ship_address">
                  <div class="shipping-item"><el-icon><Van /></el-icon><span v-if="product.shipping_type === 'free'" class="free-tag">包邮</span><span v-else>运费 ¥{{ product.shipping_fee }}</span></div>
                  <div class="shipping-item"><el-icon><Clock /></el-icon><span>{{ product.ship_time === '48h' ? '48小时内发货' : '7天预售' }}</span></div>
                  <div class="shipping-item" v-if="product.ship_address"><el-icon><Location /></el-icon><span>{{ product.ship_address }}</span></div>
                </div>

                <div class="sku-section" v-if="product.specs?.length">
                  <div class="sku-label">规格</div>
                  <div class="sku-options">
                    <div v-for="(spec, idx) in product.specs" :key="idx" class="sku-option" :class="{ active: selectedSkuIndex === idx, soldout: spec.stock === 0 }" @click="spec.stock > 0 && (selectedSkuIndex = idx)">
                      <img v-if="spec.image" :src="spec.image" class="sku-thumb" />
                      <span>{{ spec.name }}</span>
                      <span v-if="spec.stock === 0" class="soldout-mark">已售罄</span>
                    </div>
                  </div>
                  <div class="sku-info" v-if="selectedSpec">
                    <span>{{ selectedSpec.stock_display || '有货' }}</span>
                    <span v-if="selectedSpec.limit_per_user" class="sku-limit">· 限购 {{ selectedSpec.limit_per_user }} 件</span>
                  </div>
                </div>

                <div class="product-stats">
                  <div class="stat-item"><span class="stat-label">已售</span><span class="stat-value">{{ product.sales }}</span></div>
                  <div class="stat-item"><span class="stat-label">库存</span><span class="stat-value">{{ product.stock_display || '有货' }}</span></div>
                </div>

                <div class="product-desc"><h3 class="desc-title">商品详情</h3><p>{{ product.description }}</p></div>

                <div class="actions">
                  <div class="qty-selector"><span class="qty-label">数量</span><el-input-number v-model="qty" :min="1" :max="maxQty" size="large" /></div>
                  <div class="action-buttons">
                    <el-button type="primary" size="large" class="btn-cart" @click="handleAddToCart" :disabled="isSoldOut">加入购物车</el-button>
                    <el-button size="large" class="btn-buy" @click="handleBuyNow" :disabled="isSoldOut">立即购买</el-button>
                    <el-button size="large" class="btn-favorite" @click="handleFavorite"><el-icon><Star /></el-icon>收藏</el-button>
                  </div>
                </div>
              </div>
            </el-col>
          </el-row>
        </div>
      </div>
    </div>
  </MainLayout>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import MainLayout from '@/components/MainLayout.vue'
import { productApi, orderApi, courseApi } from '@/api/modules'
import { Star, Picture, ArrowLeft, ArrowRight, Van, Clock, Location } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const product = ref(null)
const loading = ref(false)
const qty = ref(1)
const currentImage = ref(0)
const selectedSkuIndex = ref(-1)
let carouselTimer = null

const selectedSpec = computed(() => {
  if (selectedSkuIndex.value >= 0 && product.value?.specs?.length) return product.value.specs[selectedSkuIndex.value]
  return null
})
const isSoldOut = computed(() => {
  if (product.value?.specs?.length) {
    if (selectedSkuIndex.value < 0) return false
    return (selectedSpec.value?.stock || 0) === 0
  }
  return (product.value?.stock || 0) === 0
})

const maxQty = computed(() => {
  const stock = selectedSpec.value?.stock ?? product.value?.stock ?? 1
  const limit = selectedSpec.value?.limit_per_user || 0
  if (limit > 0) return Math.min(limit, stock)
  return stock
})

const startCarousel = () => { stopCarousel(); if (product.value?.images?.length > 1) carouselTimer = setInterval(() => { currentImage.value = (currentImage.value + 1) % product.value.images.length }, 3000) }
const stopCarousel = () => { if (carouselTimer) { clearInterval(carouselTimer); carouselTimer = null } }
const prevImage = () => { if (product.value?.images?.length > 1) currentImage.value = currentImage.value === 0 ? product.value.images.length - 1 : currentImage.value - 1 }
const nextImage = () => { if (product.value?.images?.length > 1) currentImage.value = (currentImage.value + 1) % product.value.images.length }

onMounted(async () => {
  loading.value = true
  try {
    product.value = await productApi.getProduct(route.params.id)
    // 检查商品是否下架
    if (product.value.status === 'offline') {
      ElMessage.error('商品已下架')
      router.back()
      return
    }
    try { await courseApi.recordProductBrowse(product.value.id) } catch (_) {}
    await new Promise(r => setTimeout(r, 100))
    startCarousel()
  } catch (err) {
    // axios interceptor 返回的是 error.response?.data（{detail: "..."}），不是完整的 axios error
    const detail = err.detail || err.message || ''
    if (detail.includes('不存在') || detail.includes('下架')) {
      ElMessage.error(detail)
    } else {
      ElMessage.error('加载商品失败')
    }
    router.back()
  }
  finally { loading.value = false }
})
onUnmounted(() => { stopCarousel() })

const requireLogin = () => {
  ElMessageBox.confirm('请先登录，登录后方可操作', '提示', {
    confirmButtonText: '去登录',
    cancelButtonText: '取消',
    type: 'warning',
  }).then(() => {
    router.push({ path: '/login', query: { redirect: router.currentRoute.value.fullPath } })
  }).catch(() => {})
}

const handleAddToCart = async () => {
  if (!userStore.token) { requireLogin(); return }
  if (product.value?.specs?.length && selectedSkuIndex.value < 0) { ElMessage.warning('请先选择商品规格'); return }
  if (isSoldOut.value) { ElMessage.warning('该商品已售罄'); return }
  try {
    const d = { product_id: product.value.id, qty: qty.value }
    if (selectedSpec.value) { d.spec_name = selectedSpec.value.name; d.spec_price = selectedSpec.value.price; d.spec_sku = selectedSpec.value.sku || '' }
    await orderApi.addToCart(d)
    ElMessage.success('已加入购物车')
  } catch (err) { ElMessage.error(err.detail || '添加失败') }
}
const handleBuyNow = async () => {
  if (!userStore.token) { requireLogin(); return }
  if (product.value?.specs?.length && selectedSkuIndex.value < 0) { ElMessage.warning('请先选择商品规格'); return }
  if (isSoldOut.value) { ElMessage.warning('该商品已售罄'); return }
  router.push({ path: '/checkout', query: { items: JSON.stringify([{ product_id: product.value.id, name: product.value.name, price: selectedSpec.value ? selectedSpec.value.price : product.value.price, qty: qty.value, spec_name: selectedSpec.value?.name || '', image: product.value.images?.[0] || '' }]) } })
}
const handleFavorite = async () => {
  if (!userStore.token) { requireLogin(); return }
  try { const res = await productApi.favorite(product.value.id); ElMessage.success(res.action === 'added' ? '已收藏' : '已取消收藏') }
  catch (err) { ElMessage.error('操作失败') }
}
</script>

<style scoped>
.product-detail-page { padding: var(--space-xl) 0; min-height: 100vh; }
.product-detail { animation: fadeInUp 0.5s ease; }
.product-gallery { position: sticky; top: 84px; }
.gallery-main { position: relative; border-radius: var(--radius-lg); overflow: hidden; background: var(--color-bg-warm); box-shadow: var(--shadow-md); }
.gallery-image { width: 100%; height: 450px; display: block; }
.gallery-placeholder { height: 450px; display: flex; align-items: center; justify-content: center; color: var(--color-text-light); }
.gallery-arrow { position: absolute; top: 50%; transform: translateY(-50%); width: 40px; height: 40px; background: rgba(255,255,255,0.85); border-radius: 50%; display: flex; align-items: center; justify-content: center; cursor: pointer; opacity: 0; transition: opacity 0.25s; z-index: 2; color: var(--color-text); box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
.gallery-main:hover .gallery-arrow { opacity: 1; }
.gallery-arrow:hover { background: #fff; }
.gallery-arrow-left { left: 12px; } .gallery-arrow-right { right: 12px; }
.gallery-dots { position: absolute; bottom: 16px; left: 50%; transform: translateX(-50%); display: flex; gap: 8px; z-index: 2; }
.dot { width: 8px; height: 8px; border-radius: 50%; background: rgba(255,255,255,0.5); cursor: pointer; transition: all 0.25s; }
.dot:hover { background: rgba(255,255,255,0.8); }
.dot.active { width: 24px; border-radius: 4px; background: #fff; }
.gallery-thumbs { display: flex; gap: 10px; margin-top: 12px; }
.thumb-item { width: 72px; height: 72px; border-radius: var(--radius-sm); overflow: hidden; cursor: pointer; border: 2px solid transparent; transition: all var(--transition-fast); }
.thumb-item:hover, .thumb-item.active { border-color: var(--color-primary); }
.product-info { padding: var(--space-md) 0; }
.info-header { margin-bottom: var(--space-lg); }
.category-tag { display: inline-block; background: var(--color-bg-warm); color: var(--color-text-secondary); padding: 4px 12px; border-radius: var(--radius-sm); font-size: 12px; margin-bottom: var(--space-sm); }
.product-title { font-size: 26px; font-weight: 600; margin: 0; color: var(--color-text); line-height: 1.4; }
.product-price-box { display: flex; align-items: baseline; gap: 8px; margin-bottom: var(--space-md); padding: var(--space-md); background: var(--color-bg-warm); border-radius: var(--radius-md); }
.current-price { font-size: 32px; color: var(--color-accent); font-weight: 700; }
.qiyi { font-size: 14px; color: var(--color-accent); margin-left: 2px; }

.shipping-bar { display: flex; align-items: center; gap: 20px; margin-bottom: var(--space-md); padding: 10px 14px; background: #f7f8fa; border-radius: 6px; font-size: 13px; color: #666; }
.shipping-item { display: flex; align-items: center; gap: 4px; }
.free-tag { color: #fa541c; font-weight: 600; background: #fff2e8; padding: 2px 8px; border-radius: 3px; font-size: 12px; }

.sku-section { margin-bottom: var(--space-lg); padding: var(--space-md); background: var(--color-bg-warm); border-radius: var(--radius-md); }
.sku-label { font-size: 14px; font-weight: 600; color: var(--color-text); margin-bottom: var(--space-sm); }
.sku-options { display: flex; flex-wrap: wrap; gap: 8px; }
.sku-option { display: inline-flex; align-items: center; gap: 6px; padding: 6px 16px; border: 1px solid var(--color-border); border-radius: var(--radius-sm); cursor: pointer; font-size: 14px; transition: all var(--transition-fast); background: var(--color-surface); }
.sku-option:hover { border-color: var(--color-primary); }
.sku-option.active { border-color: var(--color-primary); background: var(--color-primary); color: #fff; }
.sku-option.soldout { opacity: 0.45; cursor: not-allowed; border-color: #eee; color: #ccc; }
.sku-thumb { width: 24px; height: 24px; border-radius: 3px; object-fit: cover; }
.soldout-mark { font-size: 11px; color: #ccc; }
.sku-info { display: flex; gap: 16px; margin-top: var(--space-sm); font-size: 13px; color: var(--color-text-secondary); }
.sku-limit { color: #e6a23c; font-weight: 500; }

.product-stats { display: flex; gap: var(--space-xl); margin-bottom: var(--space-lg); padding-bottom: var(--space-lg); border-bottom: 1px solid var(--color-border-light); }
.stat-item { display: flex; flex-direction: column; gap: 4px; }
.stat-label { font-size: 12px; color: var(--color-text-secondary); }
.stat-value { font-size: 18px; font-weight: 600; color: var(--color-text); }

.product-desc { margin-bottom: var(--space-xl); }
.desc-title { font-size: 16px; font-weight: 600; margin: 0 0 var(--space-sm); color: var(--color-text); }
.product-desc p { color: var(--color-text-secondary); line-height: 1.8; margin: 0; }

.actions { display: flex; flex-direction: column; gap: var(--space-md); }
.qty-selector { display: flex; align-items: center; gap: var(--space-md); }
.qty-label { font-size: 14px; color: var(--color-text-secondary); }
.action-buttons { display: flex; gap: var(--space-sm); }
.btn-cart { flex: 1; }
.btn-buy { flex: 1; background: var(--color-accent) !important; border-color: var(--color-accent) !important; }
.btn-buy:hover { background: var(--color-accent-light) !important; border-color: var(--color-accent-light) !important; }
.btn-favorite { display: flex; align-items: center; gap: 6px; }

@keyframes fadeInUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
.carousel-fade-enter-active, .carousel-fade-leave-active { transition: opacity 0.4s ease; }
.carousel-fade-enter-from, .carousel-fade-leave-to { opacity: 0; }

@media (max-width: 768px) {
  .product-detail-page { padding: var(--space-md) 0; }
  .gallery-image, .gallery-placeholder { height: 300px; }
  .product-gallery { position: static; margin-bottom: var(--space-lg); }
  .product-title { font-size: 20px; }
  .current-price { font-size: 26px; }
  .action-buttons { flex-direction: column; }
  .gallery-thumbs { display: none; }
}
</style>