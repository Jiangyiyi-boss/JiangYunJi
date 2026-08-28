<template>
  <MainLayout>
    <div class="container">
      <h2 class="page-title">我的收藏</h2>
      <div class="card">
        <el-row :gutter="16">
          <el-col v-for="product in products" :key="product.id" :span="6">
            <div class="product-card" @click="$router.push(`/product/${product.id}`)">
              <div class="product-image">
                <el-image v-if="product.images?.length" :src="product.images[0]" fit="cover" style="width: 100%; height: 200px" />
                <div v-else class="image-placeholder"><el-icon :size="40"><Picture /></el-icon></div>
              </div>
              <div class="product-info">
                <h4>{{ product.name }}</h4>
                <span class="price">¥{{ product.price }}</span>
              </div>
            </div>
          </el-col>
        </el-row>
        <el-empty v-if="!products.length" description="暂无收藏" />
      </div>
    </div>
  </MainLayout>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import MainLayout from '@/components/MainLayout.vue'
import { productApi } from '@/api/modules'

const products = ref([])

onMounted(async () => {
  try {
    const res = await productApi.getFavorites({ skip: 0, limit: 20 })
    products.value = res.items
  } catch (err) {
    console.error(err)
  }
})
</script>

<style scoped>
.page-title { margin: 20px 0; }
.product-card { background: #fff; border-radius: 8px; overflow: hidden; cursor: pointer; margin-bottom: 16px; transition: transform 0.2s; }
.product-card:hover { transform: translateY(-4px); }
.image-placeholder { height: 200px; display: flex; align-items: center; justify-content: center; background: #f5f5f5; color: #ccc; }
.product-info { padding: 12px; }
.product-info h4 { font-size: 14px; margin: 0 0 8px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.price { color: #f56c6c; font-weight: bold; }
</style>
