<template>
  <MainLayout>
    <!-- 匠人雅集子导航栏 -->
    <div class="forum-header">
      <div class="container header-inner">
        <div class="tab-nav">
          <router-link
            v-for="tab in tabs"
            :key="tab.key"
            :to="tab.path"
            :class="['tab-item', { active: activeTab === tab.key }]"
          >
            {{ tab.label }}
          </router-link>
        </div>
        <div class="header-actions">
          <div class="action-btn notif-btn" @click.stop="toggleNotifDropdown">
            <el-badge :value="unreadCount" :hidden="unreadCount === 0" :max="99">
              <el-icon :size="20"><Bell /></el-icon>
            </el-badge>
          </div>
          <div class="action-btn profile-btn" @click="handleMyProfile">
            <el-avatar :size="32" :src="userStore.user?.avatar">{{ userStore.user?.nickname?.[0] || '我' }}</el-avatar>
          </div>
          <!-- 通知下拉框 -->
          <div v-if="showNotifDropdown" class="notif-dropdown" @click.stop>
            <div class="notif-tabs">
              <div
                :class="['notif-tab', { active: notifTab === 'all' }]"
                @click="notifTab = 'all'"
              >
                全部消息
              </div>
              <div
                :class="['notif-tab', { active: notifTab === 'follow' }]"
                @click="notifTab = 'follow'"
              >
                新关注
              </div>
            </div>
            <div v-if="notifLoading" class="notif-dropdown-loading">
              <el-skeleton :rows="3" animated />
            </div>
            <div v-else-if="filteredNotifs.length === 0" class="notif-dropdown-empty">
              暂无消息
            </div>
            <div v-else class="notif-dropdown-list">
              <div
                v-for="notif in filteredNotifs"
                :key="notif.id"
                class="notif-dropdown-item"
                @click="handleNotifClick(notif)"
              >
                <el-avatar :size="40" :src="notif.actor_avatar" class="notif-avatar">
                  {{ notif.actor_nickname?.[0] || 'U' }}
                </el-avatar>
                <div class="notif-info">
                  <div class="notif-text">
                    <span class="actor-name">{{ notif.actor_nickname }}</span>
                    <span class="action-text">{{ getNotifActionText(notif) }}</span>
                  </div>
                  <div class="notif-time">{{ formatNotifTime(notif.created_at) }}</div>
                </div>
              </div>
            </div>
            <div class="notif-dropdown-footer">
              <router-link to="/forum/notifications" @click="showNotifDropdown = false">查看全部消息</router-link>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="container">
      <div class="card" v-loading="loading">
        <div v-if="post">
          <!-- 帖子内容 -->
          <div class="post-header">
            <div class="author-info" @click="goToAuthor(post.user_id)">
              <el-avatar :size="40" :src="post.author_avatar">
                {{ post.author_nickname?.[0] || 'U' }}
              </el-avatar>
              <div class="author-detail">
                <span class="author-name">{{ post.author_nickname }}</span>
                <span class="post-time">{{ formatTime(post.created_at) }}</span>
              </div>
            </div>
          </div>

          <h2 class="post-title">{{ post.title }}</h2>
          <div class="post-content">{{ post.content }}</div>

          <!-- 图片 -->
          <div v-if="post.images?.length" class="post-images" :class="`grid-${Math.min(post.images.length, 9)}`">
            <el-image
              v-for="(img, idx) in post.images.slice(0, 9)"
              :key="idx"
              :src="img"
              fit="cover"
              class="post-image"
              :preview-src-list="post.images.slice(0, 9)"
              :initial-index="idx"
            />
          </div>

          <!-- 关联商品 -->
          <div v-if="post.linked_products?.length" class="linked-product-section">
            <div v-for="(lp, idx) in post.linked_products" :key="idx" class="linked-product-card" @click="goToLinkedProduct(lp)">
              <div class="linked-product-img-wrap">
                <img :src="getLinkedProductField(lp, 'image')" class="linked-product-img" @error="e => e.target.style.display = 'none'" />
              </div>
              <div class="linked-product-info">
                <div class="linked-product-name">{{ getLinkedProductField(lp, 'name') || `商品 #${getLinkedProductId(lp)}` }}</div>
                <div class="linked-product-price" v-if="getLinkedProductField(lp, 'price')">¥{{ getLinkedProductField(lp, 'price') }}</div>
              </div>
              <el-icon class="linked-product-arrow"><ArrowRight /></el-icon>
            </div>
          </div>

          <!-- 帖子底部互动 -->
          <div class="post-actions">
            <div class="action-btn like-btn" :class="{ active: post.is_liked }" @click="handleLike">
              <span class="heart-icon">{{ post.is_liked ? '♥' : '♡' }}</span>
              <span>{{ post.like_count || '' }}</span>
            </div>
            <div class="action-btn">
              <el-icon><ChatDotRound /></el-icon>
              <span>{{ post.comment_count || '' }}</span>
            </div>
            <div class="action-btn" :class="{ active: post.is_favorited }" @click="handleFavorite">
              <el-icon><StarFilled v-if="post.is_favorited" /><Star v-else /></el-icon>
              <span>收藏</span>
            </div>
          </div>

          <!-- 评论区 -->
          <div class="comment-section">
            <h3>评论 ({{ post.comment_count }})</h3>

            <!-- 发表评论 -->
            <div class="comment-input">
              <el-input
                v-model="commentText"
                type="textarea"
                :rows="3"
                :placeholder="replyTo ? `回复 @${replyTo.author_nickname}` : '写下你的评论...'"
              />
              <div class="comment-actions">
                <el-button v-if="replyTo" text size="small" @click="cancelReply">取消回复</el-button>
                <el-button type="primary" @click="handleComment" :loading="commenting">
                  {{ replyTo ? '回复' : '发表' }}
                </el-button>
              </div>
            </div>

            <!-- 评论列表 -->
            <div v-if="commentTree.length === 0" class="empty-comments">
              <el-empty description="暂无评论，快来抢沙发吧" />
            </div>
            <div v-else class="comment-list">
              <div v-for="c in commentTree" :key="c.id" class="comment-item">
                <!-- 一级评论 -->
                <div class="comment-main">
                  <div class="comment-author" @click="goToAuthor(c.user_id)">
                    <el-avatar :size="32" :src="c.author_avatar">
                      {{ c.author_nickname?.[0] || 'U' }}
                    </el-avatar>
                    <span class="comment-name">{{ c.author_nickname }}</span>
                  </div>
                  <div class="comment-body">
                    <p class="comment-text">{{ c.content }}</p>
                    <div class="comment-footer">
                      <span class="comment-time">{{ formatTime(c.created_at) }}</span>
                      <div class="comment-actions-right">
                        <span class="comment-action" @click="handleReply(c)">
                          <el-icon><ChatDotRound /></el-icon>
                          回复
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- 二级回复列表 -->
                <div v-if="c.children?.length" class="reply-section">
                  <div
                    v-for="r in (expandedComments[c.id] ? c.children : c.children.slice(0, 3))"
                    :key="r.id"
                    class="reply-item"
                  >
                    <div class="reply-author" @click="goToAuthor(r.user_id)">
                      <el-avatar :size="24" :src="r.author_avatar">
                        {{ r.author_nickname?.[0] || 'U' }}
                      </el-avatar>
                      <span class="reply-name">{{ r.author_nickname }}</span>
                    </div>
                    <div class="reply-body">
                      <div class="reply-to-line" v-if="r.parent_author">
                        <span class="reply-to-text">回复</span>
                        <span class="reply-parent-name" @click.stop="goToAuthor(r.parent_user_id)">@{{ r.parent_author }}</span>
                      </div>
                      <p class="reply-text">{{ r.content }}</p>
                      <div class="reply-footer">
                        <span class="reply-time">{{ formatTime(r.created_at) }}</span>
                        <div class="reply-actions-right">
                          <span class="reply-action" @click="handleReply(r)">
                            <el-icon><ChatDotRound /></el-icon>
                            回复
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                  <!-- 展开/收起按钮 -->
                  <div
                    v-if="c.children.length > 3"
                    class="expand-btn"
                    @click="toggleExpand(c.id)"
                  >
                    {{ expandedComments[c.id] ? '收起回复' : `查看全部 ${c.children.length} 条回复` }}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </MainLayout>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Star, StarFilled, ChatDotRound, Bell, ArrowRight } from '@element-plus/icons-vue'
import MainLayout from '@/components/MainLayout.vue'
import { forumApi } from '@/api/modules'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

// 匠人雅集子导航
const tabs = [
  { key: 'home', label: '首页', path: '/forum' },
  { key: 'hot', label: '热门', path: '/forum?tab=hot' },
  { key: 'following', label: '关注', path: '/forum?tab=following' },
  { key: 'artisan', label: '匠人', path: '/forum/artisans' },
]
const activeTab = ref('home')
const unreadCount = ref(0)

const handleMyProfile = () => {
  router.push('/forum/profile')
}

const post = ref(null)
const comments = ref([])
const commentText = ref('')
const replyTo = ref(null)
const commenting = ref(false)
const loading = ref(false)
const expandedComments = ref({})

// 将扁平评论组装为树形结构（所有回复都挂到一级评论下）
const commentTree = computed(() => {
  const map = {}
  const roots = []

  comments.value.forEach(c => {
    map[c.id] = { ...c, children: [] }
  })

  // 找到每个评论的根评论ID
  function getRootId(comment) {
    let current = comment
    while (current.parent_id && map[current.parent_id]) {
      current = map[current.parent_id]
    }
    return current.id
  }

  comments.value.forEach(c => {
    const node = map[c.id]
    if (c.parent_id && map[c.parent_id]) {
      // 找到父评论的作者
      const parent = map[c.parent_id]
      node.parent_author = parent.author_nickname
      node.parent_user_id = parent.user_id
      // 挂到根评论下
      const rootId = getRootId(c)
      map[rootId].children.push(node)
    } else {
      roots.push(node)
    }
  })

  return roots
})

// 通知下拉框
const showNotifDropdown = ref(false)
const recentNotifs = ref([])
const notifLoading = ref(false)
const notifTab = ref('all') // 'all' | 'follow'

const filteredNotifs = computed(() => {
  if (notifTab.value === 'follow') {
    return recentNotifs.value.filter(n => n.type === 'follow')
  }
  return recentNotifs.value
})

const loadUnreadCount = async () => {
  if (!userStore.user) return
  try {
    const res = await forumApi.getUnreadCount()
    unreadCount.value = res.count || 0
  } catch (err) {
    // ignore
  }
}

const loadRecentNotifs = async () => {
  if (!userStore.user) return
  notifLoading.value = true
  try {
    const res = await forumApi.getNotifications({ limit: 5 })
    recentNotifs.value = res.items || res || []
  } catch (err) {
    // ignore
  } finally {
    notifLoading.value = false
  }
}

const toggleNotifDropdown = async () => {
  showNotifDropdown.value = !showNotifDropdown.value
  if (showNotifDropdown.value) {
    await loadRecentNotifs()
  }
}

const getNotifActionText = (notif) => {
  switch (notif.type) {
    case 'like': return `赞了你的帖子${notif.post_title ? `「${notif.post_title}」` : ''}`
    case 'comment': return `评论了你的帖子${notif.post_title ? `「${notif.post_title}」` : ''}`
    case 'reply': return `回复了你的评论${notif.post_title ? `「${notif.post_title}」` : ''}`
    case 'favorite': return `收藏了你的帖子${notif.post_title ? `「${notif.post_title}」` : ''}`
    case 'follow': return '关注了你'
    default: return ''
  }
}

const formatNotifTime = (time) => {
  if (!time) return ''
  const date = new Date(time)
  const now = new Date()
  const diff = now - date
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  if (diff < 604800000) return `${Math.floor(diff / 86400000)}天前`
  return date.toLocaleDateString()
}

const handleNotifClick = async (notif) => {
  // 标记已读
  if (!notif.is_read) {
    try {
      await forumApi.markNotificationRead(notif.id)
      notif.is_read = true
      unreadCount.value = Math.max(0, unreadCount.value - 1)
    } catch (_) {}
  }
  showNotifDropdown.value = false
  // 跳转
  if (notif.type === 'follow') {
    router.push(`/forum/user/${notif.actor_id}`)
  } else if (notif.post_id) {
    router.push(`/forum/${notif.post_id}`)
  }
}

// 点击外部关闭下拉框
const closeNotifDropdown = (e) => {
  if (!e.target.closest('.notif-btn') && !e.target.closest('.notif-dropdown')) {
    showNotifDropdown.value = false
  }
}

onMounted(async () => {
  loading.value = true
  try {
    post.value = await forumApi.getPost(route.params.id)
    comments.value = await forumApi.getComments(route.params.id)
    if (userStore.user) {
      forumApi.recordForumBrowse(route.params.id).catch(() => {})
    }
    // 从通知点击进入帖子时，标记全部已读以清除红点
    forumApi.markAllNotificationsRead().catch(() => {})
    loadUnreadCount()
  } catch (err) {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
  document.addEventListener('click', closeNotifDropdown)
})

onUnmounted(() => {
  document.removeEventListener('click', closeNotifDropdown)
})

const formatTime = (time) => {
  if (!time) return ''
  const date = new Date(time)
  const now = new Date()
  const diff = now - date
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  return date.toLocaleDateString()
}

const goToAuthor = (userId) => {
  if (userStore.user?.id === userId) {
    router.push('/forum/profile')
  } else {
    router.push(`/forum/user/${userId}`)
  }
}

const handleLike = async () => {
  if (!userStore.user) {
    ElMessage.warning('请先登录')
    return
  }
  try {
    const res = await forumApi.likePost(post.value.id)
    post.value.is_liked = res.action === 'liked'
    post.value.like_count = (post.value.like_count || 0) + (post.value.is_liked ? 1 : -1)
  } catch (err) {
    ElMessage.error('操作失败')
  }
}

const handleFavorite = async () => {
  if (!userStore.user) {
    ElMessage.warning('请先登录')
    return
  }
  try {
    const res = await forumApi.favoritePost(post.value.id)
    post.value.is_favorited = res.action === 'favorited'
    ElMessage.success(post.value.is_favorited ? '已收藏' : '已取消收藏')
  } catch (err) {
    ElMessage.error('操作失败')
  }
}

const handleComment = async () => {
  if (!commentText.value.trim()) {
    ElMessage.warning('请输入评论内容')
    return
  }
  if (!userStore.user) {
    ElMessage.warning('请先登录')
    return
  }

  commenting.value = true
  try {
    const data = { content: commentText.value }
    const isReply = !!replyTo.value
    if (replyTo.value) {
      data.parent_id = replyTo.value.id
    }
    await forumApi.createComment(post.value.id, data)
    commentText.value = ''
    replyTo.value = null
    comments.value = await forumApi.getComments(route.params.id)
    post.value = await forumApi.getPost(route.params.id)
    ElMessage.success(isReply ? '回复成功' : '评论成功')
  } catch (err) {
    ElMessage.error(err.detail || err.message || '操作失败')
  } finally {
    commenting.value = false
  }
}

const handleReply = (comment) => {
  if (!userStore.user) {
    ElMessage.warning('请先登录')
    return
  }
  replyTo.value = comment
  commentText.value = ''
}

const cancelReply = () => {
  replyTo.value = null
  commentText.value = ''
}

const toggleExpand = (commentId) => {
  expandedComments.value[commentId] = !expandedComments.value[commentId]
}

// 关联商品
const getLinkedProductId = (item) => typeof item === 'object' ? item.id : item
const getLinkedProductField = (item, field) => typeof item === 'object' ? (item[field] || '') : ''
const goToLinkedProduct = (lp) => {
  const productId = getLinkedProductId(lp)
  router.push(`/product/${productId}`)
}
</script>

<style scoped>
/* 匠人雅集子导航栏 */
.forum-header {
  background: #fff;
  border-bottom: 1px solid #eee;
  position: sticky;
  top: 68px;
  z-index: 99;
}

.header-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.tab-nav {
  display: flex;
  gap: 0;
  flex: 1;
}

.tab-item {
  text-align: center;
  padding: 14px 12px;
  font-size: 15px;
  color: #666;
  cursor: pointer;
  position: relative;
  transition: color 0.2s;
  white-space: nowrap;
  text-decoration: none;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.notif-btn {
  color: #666;
  padding: 4px;
  border-radius: 8px;
  transition: background 0.2s;
}

.notif-btn:hover {
  background: #f0f5ff;
  color: #409eff;
}

/* 通知下拉框 */
.notif-dropdown {
  position: absolute;
  top: 100%;
  right: 60px;
  margin-top: 8px;
  width: 420px;
  max-height: 480px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.12);
  z-index: 200;
  overflow: hidden;
}

.notif-tabs {
  display: flex;
  gap: 0;
  padding: 12px 16px;
  border-bottom: 1px solid #f0f0f0;
}

.notif-tab {
  padding: 8px 16px;
  font-size: 14px;
  color: #666;
  cursor: pointer;
  border-radius: 6px;
  transition: all 0.2s;
}

.notif-tab.active {
  color: #409eff;
  font-weight: 600;
  background: #f0f5ff;
}

.notif-tab:hover:not(.active) {
  background: #f5f5f5;
}

.notif-dropdown-loading {
  padding: 16px;
}

.notif-dropdown-empty {
  padding: 32px 16px;
  text-align: center;
  color: #999;
  font-size: 14px;
}

.notif-dropdown-list {
  max-height: 340px;
  overflow-y: auto;
}

.notif-dropdown-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 14px 16px;
  cursor: pointer;
  transition: background 0.15s;
  border-bottom: 1px solid #f5f5f5;
}

.notif-dropdown-item:last-child {
  border-bottom: none;
}

.notif-dropdown-item:hover {
  background: #f8f9fa;
}

.notif-avatar {
  flex-shrink: 0;
}

.notif-info {
  flex: 1;
  min-width: 0;
}

.notif-text {
  font-size: 14px;
  line-height: 1.5;
  color: #333;
}

.notif-text .actor-name {
  font-weight: 600;
  color: #409eff;
}

.notif-text .action-text {
  color: #666;
}

.notif-time {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}

.notif-dropdown-footer {
  padding: 12px 16px;
  border-top: 1px solid #f0f0f0;
  text-align: center;
}

.notif-dropdown-footer a {
  font-size: 13px;
  color: #409eff;
  text-decoration: none;
}

.notif-dropdown-footer a:hover {
  text-decoration: underline;
}

.profile-btn {
  border-radius: 50%;
  transition: transform 0.2s;
}

.profile-btn:hover {
  transform: scale(1.08);
}

.tab-item.active {
  color: #409eff;
  font-weight: 600;
}

.tab-item.active::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 24px;
  height: 3px;
  background: #409eff;
  border-radius: 2px;
}

.post-header {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
}

.author-info {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
}

.author-detail {
  display: flex;
  flex-direction: column;
}

.author-name {
  font-weight: 600;
  font-size: 15px;
}

.post-time {
  font-size: 12px;
  color: #999;
}

.post-title {
  font-size: 20px;
  margin-bottom: 12px;
}

.post-content {
  line-height: 1.8;
  margin-bottom: 16px;
  white-space: pre-wrap;
  font-size: 15px;
}

.post-images {
  display: grid;
  gap: 8px;
  margin-bottom: 16px;
}

.post-images.grid-1 {
  grid-template-columns: 1fr;
  max-width: 400px;
}

.post-images.grid-2 {
  grid-template-columns: repeat(2, 1fr);
}

.post-images.grid-3 {
  grid-template-columns: repeat(3, 1fr);
}

.post-image {
  width: 100%;
  aspect-ratio: 1;
  border-radius: 8px;
  cursor: pointer;
}

.post-actions {
  display: flex;
  gap: 24px;
  padding: 12px 0;
  border-top: 1px solid #eee;
  border-bottom: 1px solid #eee;
  margin-bottom: 24px;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  color: #666;
  font-size: 14px;
  transition: color 0.2s;
}

.action-btn:hover {
  color: var(--color-primary, #3b4f6b);
}

.action-btn.active {
  color: var(--color-primary, #3b4f6b);
}

.like-btn .heart-icon {
  font-size: 18px;
  line-height: 1;
}

.like-btn.active .heart-icon {
  color: #ff4d4f;
}

/* 评论区 */
.comment-section {
  margin-top: 24px;
}

.comment-section h3 {
  font-size: 16px;
  margin-bottom: 16px;
}

.comment-input {
  margin-bottom: 20px;
}

.comment-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 8px;
}

.empty-comments {
  padding: 20px 0;
}

.comment-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* 一级评论 */
.comment-item {
  padding: 12px;
  background: #fafafa;
  border-radius: 8px;
}

.comment-main {
  display: flex;
  gap: 12px;
}

.comment-author {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  flex-shrink: 0;
}

.comment-name {
  font-weight: 600;
  font-size: 14px;
}

.comment-body {
  flex: 1;
  min-width: 0;
}

.comment-text {
  margin: 0 0 8px;
  font-size: 14px;
  line-height: 1.6;
  word-break: break-word;
}

.comment-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 12px;
  color: #999;
}

.comment-actions-right {
  display: flex;
  gap: 16px;
}

.comment-action {
  display: flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
  color: #999;
  transition: color 0.2s;
}

.comment-action:hover {
  color: var(--color-primary, #3b4f6b);
}

.comment-action.active {
  color: var(--color-primary, #3b4f6b);
}

.comment-time {
  color: #999;
  font-size: 12px;
}

/* 二级回复区域 */
.reply-section {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #eee;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.reply-item {
  display: flex;
  gap: 8px;
  padding: 8px 10px;
  margin-left: 44px;
  background: #f5f5f5;
  border-radius: 6px;
}

.reply-author {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  flex-shrink: 0;
}

.reply-name {
  font-weight: 600;
  font-size: 13px;
  color: #409eff;
}

.reply-name:hover {
  text-decoration: underline;
}

.reply-body {
  flex: 1;
  min-width: 0;
}

.reply-to-line {
  margin-bottom: 2px;
  font-size: 12px;
}

.reply-to-text {
  color: #999;
}

.reply-parent-name {
  color: #409eff;
  font-weight: 600;
  cursor: pointer;
}

.reply-parent-name:hover {
  text-decoration: underline;
}

.reply-text {
  margin: 0 0 4px;
  font-size: 13px;
  line-height: 1.5;
  word-break: break-word;
  color: #333;
}

.reply-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 11px;
  color: #999;
}

.reply-actions-right {
  display: flex;
  gap: 12px;
}

.reply-action {
  display: flex;
  align-items: center;
  gap: 3px;
  cursor: pointer;
  color: #999;
  transition: color 0.2s;
}

.reply-action:hover {
  color: var(--color-primary, #3b4f6b);
}

.reply-action.active {
  color: var(--color-primary, #3b4f6b);
}

.reply-time {
  color: #999;
  font-size: 11px;
}

/* 展开/收起按钮 */
.expand-btn {
  margin-left: 44px;
  padding: 6px 12px;
  font-size: 13px;
  color: #409eff;
  cursor: pointer;
  text-align: center;
  border-radius: 4px;
  transition: background 0.2s;
}

.expand-btn:hover {
  background: #e8f4ff;
}

/* 关联商品卡片 */
.linked-product-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 16px;
}

.linked-product-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  background: #fafafa;
  border: 1px solid #eee;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.linked-product-card:hover {
  background: #f0f5ff;
  border-color: #c6d9ff;
}

.linked-product-img-wrap {
  width: 56px;
  height: 56px;
  border-radius: 6px;
  overflow: hidden;
  flex-shrink: 0;
  background: #f0f0f0;
}

.linked-product-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.linked-product-info {
  flex: 1;
  min-width: 0;
}

.linked-product-name {
  font-size: 14px;
  color: #333;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.linked-product-price {
  font-size: 16px;
  color: #f56c6c;
  font-weight: 600;
  margin-top: 4px;
}

.linked-product-arrow {
  color: #ccc;
  font-size: 16px;
  flex-shrink: 0;
}
</style>
