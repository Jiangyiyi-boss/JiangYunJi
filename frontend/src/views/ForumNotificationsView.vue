<template>
  <MainLayout>
  <div class="notifications-page">
    <div class="container">
      <!-- 顶部 Tab -->
      <div class="notif-header">
        <div class="tab-nav">
          <div
            :class="['tab-item', { active: activeTab === 'all' }]"
            @click="switchTab('all')"
          >
            全部消息
          </div>
          <div
            :class="['tab-item', { active: activeTab === 'follow' }]"
            @click="switchTab('follow')"
          >
            新关注
          </div>
        </div>
      </div>

      <!-- 加载状态 -->
      <div v-if="loading" class="loading">
        <el-skeleton :rows="5" animated />
      </div>

      <!-- 空状态 -->
      <el-empty v-else-if="notifications.length === 0" :description="emptyText" />

      <!-- 通知列表 -->
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
            <div class="notif-text">
              <span class="actor-name">{{ notif.actor_nickname }}</span>
              <span class="action-text">{{ getActionText(notif) }}</span>
            </div>
            <div class="notif-time">{{ formatTime(notif.created_at) }}</div>
          </div>
          <el-button
            v-if="activeTab === 'follow' && notif.type === 'follow' && !notif.is_mutual_followed"
            type="primary"
            size="small"
            @click.stop="handleFollowBack(notif)"
          >
            回关
          </el-button>
          <span
            v-if="activeTab === 'follow' && notif.type === 'follow' && notif.is_mutual_followed"
            class="followed-text"
          >
            已互相关注
          </span>
        </div>
      </div>

      <!-- 加载更多 -->
      <div v-if="hasMore && !loading" class="load-more">
        <el-button @click="loadMore" :loading="loadingMore">加载更多</el-button>
      </div>
    </div>
  </div>
  </MainLayout>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { forumApi } from '@/api/modules'
import MainLayout from '@/components/MainLayout.vue'

const router = useRouter()

const activeTab = ref('all')
const notifications = ref([])
const loading = ref(false)
const loadingMore = ref(false)
const hasMore = ref(false)
const skip = ref(0)
const limit = ref(20)

const emptyText = computed(() => {
  switch (activeTab.value) {
    case 'all': return '暂无消息'
    case 'follow': return '暂无新关注'
    default: return '暂无消息'
  }
})

const switchTab = (tab) => {
  activeTab.value = tab
}

const loadNotifications = async (isMore = false) => {
  if (isMore) {
    loadingMore.value = true
  } else {
    loading.value = true
  }

  try {
    const params = {
      skip: isMore ? skip.value : 0,
      limit: limit.value,
    }
    // "全部消息" 不传 type，后端返回所有类型；"新关注" 仅筛选 follow
    if (activeTab.value === 'follow') {
      params.type = 'follow'
    }

    const res = await forumApi.getNotifications(params)

    const items = res.items || []
    if (isMore) {
      notifications.value = [...notifications.value, ...items]
    } else {
      notifications.value = items
    }

    skip.value += limit.value
    hasMore.value = items.length >= limit.value
  } catch (err) {
    console.error('加载通知失败:', err)
    ElMessage.error('加载通知失败')
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

const loadMore = () => loadNotifications(true)

const getActionText = (notif) => {
  switch (notif.type) {
    case 'like':
      return `赞了你的帖子${notif.post_title ? `「${notif.post_title}」` : ''}`
    case 'comment':
      return `评论了你的帖子${notif.post_title ? `「${notif.post_title}」` : ''}`
    case 'reply':
      return `回复了你的评论${notif.post_title ? `「${notif.post_title}」` : ''}`
    case 'favorite':
      return `收藏了你的帖子${notif.post_title ? `「${notif.post_title}」` : ''}`
    case 'follow':
      return '关注了你'
    default:
      return ''
  }
}

const handleClick = async (notif) => {
  // 标记已读
  if (!notif.is_read) {
    try {
      await forumApi.markNotificationRead(notif.id)
      notif.is_read = true
    } catch (_) {
      // ignore
    }
  }
  // 跳转
  if (notif.type === 'follow') {
    router.push(`/forum/user/${notif.actor_id}`)
  } else if (notif.post_id) {
    router.push(`/forum/${notif.post_id}`)
  }
}

const handleFollowBack = async (notif) => {
  try {
    const res = await forumApi.followUser(notif.actor_id)
    ElMessage.success('已关注')
    // 直接从 API 响应更新互关状态
    notif.is_mutual_followed = res.is_mutual_followed || false
    notif.is_read = true
  } catch (err) {
    ElMessage.error('操作失败')
  }
}

const formatTime = (time) => {
  if (!time && time !== 0) return ''
  // 处理时间戳（毫秒）或ISO字符串
  let timestamp
  if (typeof time === 'number') {
    timestamp = time
  } else if (typeof time === 'string') {
    // 尝试解析ISO字符串或数字字符串
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

watch(activeTab, () => {
  skip.value = 0
  notifications.value = []
  loadNotifications()
})

onMounted(() => {
  loadNotifications()
  // 打开消息页面时标记全部已读
  forumApi.markAllNotificationsRead().catch(() => {})
})
</script>

<style scoped>
.notifications-page {
  padding: 16px 0 40px;
  min-height: 100vh;
  background: #f5f5f5;
}

.container {
  max-width: 800px;
  margin: 0 auto;
  padding: 0 16px;
}

.notif-header {
  background: #fff;
  border-radius: 12px;
  padding: 12px 16px;
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.tab-nav {
  display: flex;
  gap: 0;
}

.tab-item {
  padding: 8px 16px;
  cursor: pointer;
  font-size: 15px;
  color: #666;
  border-radius: 8px;
  transition: all 0.2s;
}

.tab-item:hover {
  background: #f0f5ff;
}

.tab-item.active {
  color: #409eff;
  font-weight: 600;
  background: #ecf5ff;
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
  align-items: center;
  gap: 12px;
  cursor: pointer;
  transition: background 0.2s;
  border-bottom: 1px solid #f0f0f0;
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

.notif-text {
  font-size: 14px;
  line-height: 1.5;
}

.actor-name {
  color: #409eff;
  font-weight: 600;
  margin-right: 4px;
}

.action-text {
  color: #333;
}

.notif-time {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}

.followed-text {
  font-size: 13px;
  color: #409eff;
  font-weight: 500;
}

.load-more {
  text-align: center;
  padding: 16px 0;
}
</style>
