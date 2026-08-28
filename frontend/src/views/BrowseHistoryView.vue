<template>
  <MainLayout>
    <div class="container">
      <div class="page-header-card">
        <h2 class="page-title">浏览记录</h2>
        <el-button v-if="historyList.length" type="danger" size="small" plain @click="handleClearAll">
          <el-icon><Delete /></el-icon> 清空全部
        </el-button>
      </div>

      <div class="tabs-wrapper">
        <el-radio-group v-model="activeType" size="default" @change="loadHistory">
          <el-radio-button value="all">全部</el-radio-button>
          <el-radio-button value="product">商品</el-radio-button>
          <el-radio-button value="course">课程</el-radio-button>
          <el-radio-button value="post">帖子</el-radio-button>
        </el-radio-group>
      </div>

      <div v-loading="loading" class="history-list">
        <el-empty v-if="!historyList.length" :description="`暂无${typeText}浏览记录`" />

        <div v-for="item in historyList" :key="item.id" class="history-item" @click="goDetail(item)">
          <!-- 商品 -->
          <template v-if="item.type === 'product'">
            <div class="item-cover">
              <el-image v-if="item.product?.images?.length" :src="item.product.images[0]" fit="cover" class="cover-img" />
              <div v-else class="cover-placeholder"><el-icon :size="32"><Goods /></el-icon></div>
            </div>
            <div class="item-info">
              <h3>{{ item.product?.name || '未知商品' }}</h3>
              <span class="price">¥{{ item.product?.price || 0 }}</span>
            </div>
          </template>

          <!-- 课程 -->
          <template v-else-if="item.type === 'course'">
            <div class="item-cover">
              <el-image v-if="item.course?.cover_image" :src="item.course.cover_image" fit="cover" class="cover-img" />
              <div v-else class="cover-placeholder"><el-icon :size="32"><VideoCamera /></el-icon></div>
              <div class="play-overlay"><el-icon :size="28"><VideoPlay /></el-icon></div>
            </div>
            <div class="item-info">
              <h3>{{ item.course?.title || '未知课程' }}</h3>
              <p v-if="item.lesson" class="lesson-name"><el-icon><VideoPlay /></el-icon> {{ item.lesson.title }}</p>
              <span v-if="item.course?.price > 0" class="price">¥{{ item.course.price }}</span>
              <span v-else class="price free">免费</span>
            </div>
          </template>

          <!-- 帖子 -->
          <template v-else-if="item.type === 'post'">
            <div class="item-cover">
              <el-image v-if="item.post_image" :src="item.post_image" fit="cover" class="cover-img" />
              <div v-else class="cover-placeholder"><el-icon :size="32"><ChatDotRound /></el-icon></div>
            </div>
            <div class="item-info">
              <h3>{{ item.post_title || '未知帖子' }}</h3>
              <p v-if="item.post_content" class="post-content">{{ item.post_content }}</p>
              <span v-if="item.post_category" class="post-category">{{ categoryText(item.post_category) }}</span>
            </div>
          </template>

          <div class="item-right">
            <span class="time">{{ formatTime(item.browsed_at) }}</span>
            <el-button type="primary" size="small" @click.stop="goDetail(item)">
              {{ item.type === 'product' ? '查看商品' : item.type === 'course' ? '继续观看' : '查看帖子' }}
            </el-button>
            <el-button type="danger" text size="small" @click.stop="handleDelete(item)"><el-icon><Delete /></el-icon></el-button>
          </div>
        </div>
      </div>
    </div>
  </MainLayout>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import MainLayout from '@/components/MainLayout.vue'
import { courseApi, forumApi } from '@/api/modules'
import { ElMessage, ElMessageBox } from 'element-plus'
import { VideoCamera, VideoPlay, Delete, Goods, ChatDotRound } from '@element-plus/icons-vue'

const router = useRouter()
const historyList = ref([])
const loading = ref(false)
const activeType = ref('all')

const typeText = computed(() => {
  return { all: '', product: '商品', course: '课程', post: '帖子' }[activeType.value]
})

const categoryText = (cat) => {
  const map = { share: '分享', work: '作品', question: '问答', tutorial: '教程' }
  return map[cat] || cat || ''
}

const loadHistory = async () => {
  loading.value = true
  try {
    if (activeType.value === 'all') {
      const [productRes, courseRes, forumRes] = await Promise.all([
        courseApi.getBrowseHistory({ limit: 50, type: 'product' }).catch(() => ({ items: [] })),
        courseApi.getBrowseHistory({ limit: 50, type: 'course' }).catch(() => ({ items: [] })),
        forumApi.getForumBrowseHistory({ limit: 50 }).catch(() => ({ items: [] })),
      ])
      const products = (productRes.items || []).map(i => ({ ...i, type: 'product' }))
      const courses = (courseRes.items || []).map(i => ({ ...i, type: 'course' }))
      const posts = (forumRes.items || []).map(i => ({ ...i, type: 'post' }))
      historyList.value = [...products, ...courses, ...posts]
        .sort((a, b) => new Date(b.browsed_at) - new Date(a.browsed_at))
        .slice(0, 50)
    } else if (activeType.value === 'post') {
      const res = await forumApi.getForumBrowseHistory({ limit: 50 })
      historyList.value = (res.items || []).map(i => ({ ...i, type: 'post' }))
    } else {
      const res = await courseApi.getBrowseHistory({ limit: 50, type: activeType.value })
      historyList.value = (res.items || []).map(i => ({ ...i, type: activeType.value }))
    }
  } catch (err) {
    ElMessage.error(err.detail || '加载失败')
  } finally {
    loading.value = false
  }
}

const handleDelete = async (item) => {
  try {
    if (item.type === 'post') {
      await forumApi.deleteForumBrowse(item.id)
    } else {
      await courseApi.deleteBrowseHistory(item.id)
    }
    ElMessage.success('已删除')
    loadHistory()
  } catch (err) {
    ElMessage.error(err.detail || '删除失败')
  }
}

const handleClearAll = async () => {
  try {
    await ElMessageBox.confirm(`确定要清空全部${typeText.value}浏览记录吗？`, '清空记录', {
      confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning',
    })
    if (activeType.value === 'all') {
      await Promise.all([
        courseApi.clearBrowseHistory(),
        forumApi.clearForumBrowseHistory(),
      ])
    } else if (activeType.value === 'post') {
      await forumApi.clearForumBrowseHistory()
    } else {
      await courseApi.clearBrowseHistory()
    }
    ElMessage.success('已清空')
    loadHistory()
  } catch (err) {
    if (err !== 'cancel') ElMessage.error(err.detail || '清空失败')
  }
}

const goDetail = (item) => {
  if (item.type === 'product') {
    router.push(`/product/${item.product_id || item.product?.id}`)
  } else if (item.type === 'course') {
    if (item.lesson) {
      router.push(`/course/${item.course_id}/learn?lesson=${item.lesson.id}`)
    } else {
      router.push(`/course/${item.course_id}`)
    }
  } else if (item.type === 'post') {
    router.push(`/forum/${item.post_id}`)
  }
}

const formatTime = (timeStr) => {
  if (!timeStr) return ''
  const date = new Date(timeStr)
  const now = new Date()
  const diff = now - date
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)
  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes} 分钟前`
  if (hours < 24) return `${hours} 小时前`
  if (days < 7) return `${days} 天前`
  return date.toLocaleDateString('zh-CN')
}

onMounted(() => {
  loadHistory()
})
</script>

<style scoped>
.container { max-width: 900px; margin: 0 auto; padding: 20px; }
.page-header-card { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.page-title { font-size: 22px; font-weight: 600; color: #333; margin: 0; }

.tabs-wrapper { margin-bottom: 16px; }

.history-list { display: flex; flex-direction: column; gap: 12px; }
.history-item {
  display: flex; align-items: center; gap: 16px; padding: 16px;
  background: #fff; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,.06);
  transition: box-shadow 0.2s; cursor: pointer;
}
.history-item:hover { box-shadow: 0 4px 16px rgba(0,0,0,.1); }
.item-cover {
  width: 120px; height: 80px; border-radius: 8px; overflow: hidden;
  flex-shrink: 0; background: #f5f5f5; position: relative;
}
.play-overlay {
  position: absolute; top: 0; left: 0; width: 100%; height: 100%;
  display: flex; align-items: center; justify-content: center;
  background: rgba(0,0,0,.3); color: #fff; opacity: 0; transition: opacity 0.2s;
}
.item-cover:hover .play-overlay { opacity: 1; }
.cover-img { width: 100%; height: 100%; border-radius: 6px; object-fit: cover; }
.cover-placeholder {
  width: 120px; height: 80px; display: flex; align-items: center;
  justify-content: center; background: #f5f5f5; border-radius: 6px; color: #ccc; flex-shrink: 0;
}
.item-info { flex: 1; min-width: 0; }
.item-info h3 { font-size: 15px; margin: 0 0 6px; color: #333; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.lesson-name { font-size: 13px; color: #409eff; margin: 0 0 8px; display: flex; align-items: center; gap: 4px; }
.post-content { font-size: 13px; color: #999; margin: 0 0 6px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.post-category { font-size: 12px; color: #909399; background: #f4f4f5; padding: 2px 8px; border-radius: 4px; }
.price { color: #f56c6c; font-weight: 600; font-size: 14px; }
.price.free { color: #67c23a; }
.item-right { display: flex; flex-direction: column; align-items: flex-end; gap: 8px; flex-shrink: 0; }
.time { font-size: 12px; color: #bbb; white-space: nowrap; }
</style>
