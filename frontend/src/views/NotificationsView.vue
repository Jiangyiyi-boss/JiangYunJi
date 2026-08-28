<template>
  <MainLayout>
    <div class="notifications-page">
      <div class="container">
        <div class="top-bar">
          <el-button text @click="$router.back()">
            <el-icon><ArrowLeft /></el-icon> 返回
          </el-button>
          <h1 class="page-title">评论消息</h1>
        </div>

        <!-- Loading -->
        <div v-if="loading" class="loading">
          <el-skeleton :rows="5" animated />
        </div>

        <!-- Empty -->
        <el-empty v-else-if="notifications.length === 0" description="暂无评论消息" />

        <!-- Notification List -->
        <div v-else class="notif-list">
          <div
            v-for="notif in notifications"
            :key="notif.id"
            :class="['notif-item', { unread: !notif.is_read }]"
            @click="handleClick(notif)"
          >
            <el-avatar :size="44" :src="notif.actor_avatar" class="actor-avatar">
              {{ notif.actor_nickname?.[0] || 'U' }}
            </el-avatar>
            <div class="notif-content">
              <div class="notif-title" v-if="notif.title">{{ notif.title }}</div>
              <div class="notif-body" v-if="notif.content">{{ notif.content }}</div>
              <div class="notif-time">{{ formatTime(notif.created_at) }}</div>
            </div>
            <span v-if="!notif.is_read" class="unread-dot"></span>
          </div>
        </div>

        <!-- Load More -->
        <div v-if="hasMore && !loading" class="load-more">
          <el-button @click="loadMore" :loading="loadingMore">加载更多</el-button>
        </div>
      </div>
    </div>
  </MainLayout>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { courseApi } from '@/api/modules'
import { ArrowLeft } from '@element-plus/icons-vue'
import MainLayout from '@/components/MainLayout.vue'

const router = useRouter()

const notifications = ref([])
const loading = ref(false)
const loadingMore = ref(false)
const hasMore = ref(false)
const skip = ref(0)
const limit = ref(20)

const loadNotifications = async (isMore = false) => {
  if (isMore) {
    loadingMore.value = true
  } else {
    loading.value = true
    skip.value = 0
  }

  try {
    const res = await courseApi.getNotifications({
      skip: isMore ? skip.value : 0,
      limit: limit.value,
    })

    const items = res.items || []
    if (isMore) {
      notifications.value = [...notifications.value, ...items]
    } else {
      notifications.value = items
    }

    skip.value += limit.value
    hasMore.value = items.length >= limit.value
  } catch (err) {
    ElMessage.error('加载消息失败')
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

const loadMore = () => loadNotifications(true)

const handleClick = async (notif) => {
  // Course-related notifications: go to course detail page with comments tab open
  // and scroll to the specific comment if comment_id is available
  if (notif.course_id) {
    let query = 'tab=comments'
    if (notif.comment_id) {
      query += `&comment_id=${notif.comment_id}`
    }
    router.push(`/course/${notif.course_id}?${query}`)
  } else if (notif.link) {
    router.push(notif.link)
  }
}

const formatTime = (time) => {
  if (!time && time !== 0) return ''
  let timestamp
  if (typeof time === 'number') {
    timestamp = time
  } else if (typeof time === 'string') {
    const parsed = Number(time)
    if (!isNaN(parsed)) {
      timestamp = parsed
    } else {
      const date = new Date(time)
      if (isNaN(date.getTime())) return ''
      timestamp = date.getTime()
    }
  } else {
    return ''
  }

  const now = Date.now()
  const diff = now - timestamp
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  if (diff < 604800000) return `${Math.floor(diff / 86400000)}天前`
  return new Date(timestamp).toLocaleDateString()
}

onMounted(() => {
  loadNotifications()
})
</script>

<style scoped>
.notifications-page {
  padding: 24px 0 40px;
  min-height: 100vh;
  background: #f5f5f5;
}

.container {
  max-width: 700px;
  margin: 0 auto;
  padding: 0 16px;
}

.top-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.page-title {
  font-size: 20px;
  font-weight: 600;
  margin: 0;
  color: #333;
  flex: 1;
}

.loading {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
}

.notif-list {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.notif-item {
  background: #fff;
  padding: 16px;
  display: flex;
  align-items: flex-start;
  gap: 12px;
  cursor: pointer;
  transition: background 0.2s;
  border-bottom: 1px solid #f0f0f0;
  position: relative;
}

.notif-item:first-child {
  border-radius: 12px 12px 0 0;
}

.notif-item:last-child {
  border-radius: 0 0 12px 12px;
  border-bottom: none;
}

.notif-item:only-child {
  border-radius: 12px;
}

.notif-item:hover {
  background: #fafafa;
}

.notif-item.unread {
  background: #f0f5ff;
}

.actor-avatar {
  flex-shrink: 0;
}

.notif-content {
  flex: 1;
  min-width: 0;
}

.notif-title {
  font-size: 14px;
  color: #333;
  font-weight: 500;
}

.notif-body {
  font-size: 13px;
  color: #666;
  margin-top: 4px;
  line-height: 1.5;
}

.notif-time {
  font-size: 12px;
  color: #999;
  margin-top: 6px;
}

.unread-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #f56c6c;
  flex-shrink: 0;
  margin-top: 4px;
}

.load-more {
  text-align: center;
  padding: 16px 0;
}
</style>
