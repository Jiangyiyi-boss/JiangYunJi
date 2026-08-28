<template>
  <MainLayout>
  <div class="forum-page">
    <!-- 子导航栏 -->
    <div class="forum-header">
      <div class="container header-inner">
        <!-- 左侧 Tab -->
        <div class="tab-nav">
          <div
            v-for="tab in tabs"
            :key="tab.key"
            :class="['tab-item', { active: activeTab === tab.key }]"
            @click="handleTabClick(tab)"
          >
            {{ tab.label }}
          </div>
        </div>
        <!-- 右侧：消息通知 + 个人中心 -->
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

    <!-- 信息流 -->
    <div class="container">
      <div class="feed">
        <!-- 加载状态 -->
        <div v-if="loading" class="loading-state">
          <el-skeleton :rows="3" animated v-for="i in 3" :key="i" style="margin-bottom: 16px" />
        </div>

        <!-- 空状态 -->
        <el-empty v-else-if="posts.length === 0" description="暂无帖子" />

        <!-- 帖子列表 -->
        <div v-else class="post-list">
          <div v-for="post in posts" :key="post.id" class="post-card">
            <!-- 帖子头部：作者信息 -->
            <div class="post-header">
              <div class="author-info" @click="goToProfile(post.user_id)">
                <el-avatar :size="40" :src="post.author_avatar">{{ post.author_nickname?.[0] || 'U' }}</el-avatar>
                <div class="author-detail">
                  <div class="author-name-row">
                    <span class="author-name">{{ post.author_nickname }}</span>
                    <el-tag v-if="post.author_role === 'artisan'" size="small" type="warning" effect="dark" class="artisan-tag">
                      非遗匠人
                    </el-tag>
                  </div>
                  <span class="post-time">{{ formatTime(post.created_at) }}</span>
                </div>
              </div>
              <div class="post-actions-top">
                <!-- 关注按钮 -->
                <el-button
                  v-if="userStore.user && post.user_id !== userStore.user.id"
                  :type="post.is_followed ? 'default' : 'primary'"
                  size="small"
                  @click.stop="handleFollow(post)"
                >
                  {{ post.is_mutual_followed ? '已互相关注' : (post.is_followed ? '已关注' : '+ 关注') }}
                </el-button>
              </div>
            </div>

            <!-- 帖子内容 -->
            <div class="post-body" @click="$router.push(`/forum/${post.id}`)">
              <h3 v-if="post.title" class="post-title">{{ post.title }}</h3>
              <p class="post-content">{{ post.content }}</p>
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
                  @click.stop
                />
              </div>
              <!-- 视频 -->
              <div v-if="post.video_url" class="post-video">
                <video :src="post.video_url" controls class="video-player" />
              </div>
              <!-- 推广商品 -->
              <div v-if="post.linked_products?.length" class="linked-product-card" @click.stop="$router.push(`/product/${getProductId(post.linked_products[0])}`)">
                <div class="linked-product-img-wrap">
                  <img :src="getProductField(post.linked_products[0], 'image') || getProductImage(getProductId(post.linked_products[0]))" class="linked-product-img" />
                </div>
                <div class="linked-product-info">
                  <div class="linked-product-name">{{ getProductField(post.linked_products[0], 'name') || getProductName(getProductId(post.linked_products[0])) }}</div>
                  <div class="linked-product-price">¥{{ getProductField(post.linked_products[0], 'price') || getProductPrice(getProductId(post.linked_products[0])) }}</div>
                </div>
                <el-icon class="linked-product-arrow"><ArrowRight /></el-icon>
              </div>
            </div>

            <!-- 帖子底部：互动按钮 -->
            <div class="post-footer">
              <div class="interaction-btn" :class="{ active: post.is_liked }" @click="handleLike(post)">
                <el-icon><StarFilled v-if="post.is_liked" /><Star v-else /></el-icon>
                <span>{{ post.like_count || '' }}</span>
              </div>
              <div class="interaction-btn" @click="$router.push(`/forum/${post.id}`)">
                <el-icon><ChatDotRound /></el-icon>
                <span>{{ post.comment_count || '' }}</span>
              </div>
              <div class="interaction-btn" :class="{ active: post.is_favorited }" @click="handleFavorite(post)">
                <el-icon><Collection v-if="post.is_favorited" /><CollectionTag v-else /></el-icon>
                <span>收藏</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 加载更多 -->
        <div v-if="hasMore && !loading" class="load-more">
          <el-button @click="loadMore" :loading="loadingMore">加载更多</el-button>
        </div>
      </div>
    </div>

    <!-- 底部发帖按钮 -->
    <div class="bottom-nav">
      <div class="publish-btn" @click="handlePublish">
        <el-icon :size="28"><Plus /></el-icon>
      </div>
    </div>

    <!-- 发帖弹窗 -->
    <el-dialog v-model="showCreate" :title="editDraft ? '编辑草稿' : '发布帖子'" width="600px" :close-on-click-modal="false">
      <div class="create-form">
        <el-input v-model="createForm.title" placeholder="标题（选填）" maxlength="100" show-word-limit class="mb-16" />
        <el-input
          v-model="createForm.content"
          type="textarea"
          :rows="6"
          placeholder="分享你的想法...（支持 Emoji）"
          maxlength="2000"
          show-word-limit
          class="mb-16"
        />

        <!-- Emoji 选择器 -->
        <div class="emoji-bar">
          <span
            v-for="emoji in emojis"
            :key="emoji"
            class="emoji-chip"
            @click="insertEmoji(emoji)"
          >{{ emoji }}</span>
        </div>

        <!-- 图片上传 -->
        <div v-if="!createForm.video_url" class="upload-section">
          <div class="upload-label">图片（最多9张，单张≤10M）</div>
          <el-upload
            v-model:file-list="imageList"
            action="#"
            list-type="picture-card"
            :auto-upload="false"
            :limit="9"
            :on-exceed="handleImageExceed"
            accept="image/*"
          >
            <el-icon><Plus /></el-icon>
          </el-upload>
        </div>

        <!-- 视频上传 -->
        <div v-if="!createForm.images?.length" class="upload-section">
          <div class="upload-label">视频（最多1个，≤200M）</div>
          <el-upload
            v-model:file-list="videoList"
            action="#"
            :auto-upload="false"
            :limit="1"
            accept="video/*"
            :on-change="handleVideoChange"
          >
            <el-button type="primary" plain>选择视频</el-button>
          </el-upload>
        </div>

        <!-- 推广商品（仅商家） -->
        <div v-if="userStore.user?.role === 'artisan'" class="linked-section">
          <div class="upload-label">推广商品</div>
          <el-select v-model="createForm.linked_product_id" clearable placeholder="从店铺选择一件商品（选填）" style="width: 100%" @change="onLinkedProductChange">
            <el-option v-for="p in myProducts" :key="p.id" :label="p.name" :value="p.id">
              <div class="product-option">
                <el-image v-if="p.images?.length" :src="p.images[0]" fit="cover" class="product-option-img" />
                <span>{{ p.name }}</span>
                <span class="product-option-price">¥{{ p.price }}</span>
              </div>
            </el-option>
          </el-select>
        </div>
      </div>

      <template #footer>
        <el-button @click="showCreate = false">取消</el-button>
        <el-button @click="handleSaveDraft" v-if="!editDraft">存草稿</el-button>
        <el-button type="primary" @click="handlePublishPost" :loading="publishing">
          {{ editDraft ? '发布' : '发布' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
  </MainLayout>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Star, StarFilled, ChatDotRound, Collection, CollectionTag, Plus, Bell, ArrowRight } from '@element-plus/icons-vue'
import MainLayout from '@/components/MainLayout.vue'
import { forumApi, productApi, courseApi, artisanApi } from '@/api/modules'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

// Tab 配置
const tabs = [
  { key: 'all', label: '首页' },
  { key: 'hot', label: '热门' },
  { key: 'following', label: '关注' },
  { key: 'artisan', label: '匠人' },
]
const activeTab = ref('all')

// 帖子列表
const posts = ref([])
const loading = ref(false)
const loadingMore = ref(false)
const hasMore = ref(false)
const skip = ref(0)
const limit = ref(20)

// 发帖
const showCreate = ref(false)
const publishing = ref(false)
const editDraft = ref(null)
const createForm = ref({
  title: '',
  content: '',
  images: [],
  video_url: '',
  linked_product_id: null,
  linked_product_name: '',
})
const imageList = ref([])
const videoList = ref([])
const myProducts = ref([])

// Emoji
const emojis = ref([
  '😀', '😃', '😄', '', '😆', '😅', '', '😂',
  '😊', '😇', '🙂', '', '😉', '😌', '😍', '🥰',
  '😘', '😗', '😙', '😚', '😋', '😛', '😜', '🤪',
  '😝', '🤑', '🤗', '🤭', '', '🤔', '🤐', '🤨',
  '😐', '😑', '😶', '😏', '😒', '🙄', '😬', '🤥',
  '😌', '😔', '😪', '🤤', '😴', '😷', '🤒', '🤕',
  '🤢', '🤮', '🤧', '😵', '🤯', '', '🥳', '🥴',
  '😎', '', '🧐', '😕', '😟', '🙁', '☹️', '😮',
  '❤️', '🧡', '💛', '💚', '💙', '💜', '🖤', '🤍',
  '💯', '💢', '💥', '💫', '', '💨', '🕳️', '💣',
  '', '🌸', '', '🌻', '🌼', '🌷', '🌱', '',
  '👍', '', '👏', '', '🤝', '', '✌️', '🤞',
  '', '⭐', '🌟', '✨', '💫', '🎉', '🎊', '🎈',
])

const insertEmoji = (emoji) => {
  const textarea = document.querySelector('.create-form textarea')
  if (textarea) {
    const start = textarea.selectionStart
    const end = textarea.selectionEnd
    const text = createForm.value.content
    createForm.value.content = text.substring(0, start) + emoji + text.substring(end)
    // 设置光标位置
    setTimeout(() => {
      textarea.selectionStart = textarea.selectionEnd = start + emoji.length
      textarea.focus()
    }, 0)
  } else {
    createForm.value.content += emoji
  }
}


// 检查登录
const requireLogin = (action = '此操作') => {
  if (!userStore.user) {
    ElMessage.warning(`请先登录后再${action}`)
    router.push('/login')
    return false
    }
  return true
}

// Tab 切换
const handleTabClick = (tab) => {
  if (tab.key === 'following' && !requireLogin('查看关注')) return
  activeTab.value = tab.key
  skip.value = 0
  posts.value = []
  loadPosts()
}

// 加载帖子
const loadPosts = async (isMore = false) => {
  if (isMore) {
    loadingMore.value = true
  } else {
    loading.value = true
  }

  try {
    const params = {
      skip: isMore ? skip.value : 0,
      limit: limit.value,
      tab: activeTab.value,
    }

    const res = await forumApi.getPosts(params)
    const newPosts = res.items || []
    // 调试
    newPosts.forEach(p => { if (p.linked_products?.length) console.log('linked_products:', p.id, JSON.stringify(p.linked_products)) })

    if (isMore) {
      posts.value = [...posts.value, ...newPosts]
    } else {
      posts.value = newPosts
    }

    skip.value += limit.value
    hasMore.value = newPosts.length >= limit.value
  } catch (err) {
    console.error('加载帖子失败:', err)
    ElMessage.error('加载帖子失败')
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

const loadMore = () => loadPosts(true)

// 互动操作
const handleLike = async (post) => {
  if (!requireLogin('点赞')) return
  try {
    const res = await forumApi.likePost(post.id)
    post.is_liked = res.action === 'liked'
    post.like_count += post.is_liked ? 1 : -1
  } catch (err) {
    ElMessage.error('操作失败')
  }
}

const handleFavorite = async (post) => {
  if (!requireLogin('收藏')) return
  try {
    const res = await forumApi.favoritePost(post.id)
    post.is_favorited = res.action === 'favorited'
    ElMessage.success(post.is_favorited ? '已收藏' : '已取消收藏')
  } catch (err) {
    ElMessage.error('操作失败')
  }
}

const handleFollow = async (post) => {
  if (!requireLogin('关注')) return
  try {
    const res = await forumApi.followUser(post.user_id)
    post.is_followed = res.action === 'followed'
    post.is_mutual_followed = res.is_mutual_followed || false
    ElMessage.success(post.is_followed ? '已关注' : '已取消关注')
  } catch (err) {
    ElMessage.error('操作失败')
  }
}

// 发帖
const handlePublish = () => {
  if (!requireLogin('发帖')) return
  editDraft.value = null
  resetForm()
  showCreate.value = true
  // 商家加载商品列表
  if (userStore.user?.role === 'artisan') {
    loadMyProducts()
  }
}

const loadMyProducts = async () => {
  try {
    const artisan = await artisanApi.getMy()
    const res = await productApi.getProducts({ artisan_id: artisan.id, limit: 50 })
    myProducts.value = res.items || []
  } catch (err) {
    console.error('加载商品失败:', err)
  }
}

const onLinkedProductChange = (productId) => {
  if (productId) {
    const product = myProducts.value.find(p => p.id === productId)
    createForm.value.linked_product_name = product?.name || ''
  } else {
    createForm.value.linked_product_name = ''
  }
}

const getProductName = (productId) => {
  const product = myProducts.value.find(p => p.id === productId)
  return product?.name || `商品 #${productId}`
}

// 兼容新旧 linked_products 格式
const getProductId = (item) => typeof item === 'object' ? item.id : item
const getProductField = (item, field) => typeof item === 'object' ? (item[field] || '') : ''

const getProductImage = (productId) => {
  const product = myProducts.value.find(p => p.id === productId)
  if (!product) return ''
  return product.images?.[0] || product.image || product.cover_image || ''
}

const getProductPrice = (productId) => {
  const product = myProducts.value.find(p => p.id === productId)
  if (!product) return ''
  return parseFloat(product.price) || ''
}

const onProductImgError = (e) => {
  e.target.style.display = 'none'
}

const resetForm = () => {
  createForm.value = {
    title: '',
    content: '',
    images: [],
    video_url: '',
    linked_product_id: null,
    linked_product_name: '',
  }
  imageList.value = []
  videoList.value = []
}

const handleImageExceed = () => {
  ElMessage.warning('最多上传9张图片')
}

const handleVideoChange = (file) => {
  if (file.raw) {
    if (file.raw.size > 200 * 1024 * 1024) {
      ElMessage.warning('视频大小不能超过200M')
      videoList.value = []
      return
    }
    createForm.value.video_url = URL.createObjectURL(file.raw)
  }
}

const handlePublishPost = async () => {
  if (!createForm.value.content && !imageList.value.length && !videoList.value.length) {
    ElMessage.warning('请至少填写文字、图片或视频中的一项')
    return
  }

  publishing.value = true
  try {
    // 1. 上传图片
    const imageUrls = []
    for (const item of imageList.value) {
      if (item.raw) {
        const res = await courseApi.uploadImage(item.raw)
        imageUrls.push(res.url)
      } else if (item.url && !item.url.startsWith('blob:')) {
        imageUrls.push(item.url)
      }
    }

    // 2. 上传视频
    let videoUrl = createForm.value.video_url
    if (videoList.value.length && videoList.value[0].raw) {
      const res = await courseApi.uploadVideo(videoList.value[0].raw)
      videoUrl = res.url
    } else if (videoUrl && videoUrl.startsWith('blob:')) {
      videoUrl = ''
    }

    // 3. 提交帖子
    const linkedProducts = createForm.value.linked_product_id ? [{
      id: createForm.value.linked_product_id,
      name: createForm.value.linked_product_name,
      image: getProductImage(createForm.value.linked_product_id),
      price: getProductPrice(createForm.value.linked_product_id),
    }] : []
    const data = {
      title: createForm.value.title,
      content: createForm.value.content,
      images: imageUrls,
      video_url: videoUrl,
      linked_products: linkedProducts,
    }

    await forumApi.createPost(data)
    ElMessage.success('已提交，等待管理员审核')
    showCreate.value = false
    resetForm()
    skip.value = 0
    loadPosts()
  } catch (err) {
    ElMessage.error(err.detail || err.message || '发布失败')
  } finally {
    publishing.value = false
  }
}

const handleSaveDraft = async () => {
  if (!createForm.value.content && !imageList.value.length) {
    ElMessage.warning('草稿内容不能为空')
    return
  }

  publishing.value = true
  try {
    // 上传图片
    const imageUrls = []
    for (const item of imageList.value) {
      if (item.raw) {
        const res = await courseApi.uploadImage(item.raw)
        imageUrls.push(res.url)
      } else if (item.url && !item.url.startsWith('blob:')) {
        imageUrls.push(item.url)
      }
    }

    // 上传视频
    let videoUrl = createForm.value.video_url
    if (videoList.value.length && videoList.value[0].raw) {
      const res = await courseApi.uploadVideo(videoList.value[0].raw)
      videoUrl = res.url
    } else if (videoUrl && videoUrl.startsWith('blob:')) {
      videoUrl = ''
    }

    await forumApi.createPost({
      title: createForm.value.title,
      content: createForm.value.content,
      images: imageUrls,
      video_url: videoUrl,
      linked_products: createForm.value.linked_product_id ? [{
        id: createForm.value.linked_product_id,
        name: createForm.value.linked_product_name,
        image: getProductImage(createForm.value.linked_product_id),
        price: getProductPrice(createForm.value.linked_product_id),
      }] : [],
      is_draft: true,
    })
    ElMessage.success('草稿已保存')
    showCreate.value = false
    resetForm()
  } catch (err) {
    ElMessage.error('保存失败')
  } finally {
    publishing.value = false
  }
}

// 跳转
const goToProfile = (userId) => {
  if (userStore.user?.id === userId) {
    router.push('/forum/profile')
  } else {
    router.push(`/forum/user/${userId}`)
  }
}

const handleMyProfile = () => {
  if (!requireLogin('查看个人主页')) return
  router.push('/forum/profile')
}

// 格式化时间
const formatTime = (time) => {
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

// 通知
const unreadCount = ref(0)
let unreadTimer = null
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

onMounted(() => {
  loadPosts()
  loadUnreadCount()
  unreadTimer = setInterval(loadUnreadCount, 30000)
  document.addEventListener('click', closeNotifDropdown)
})

// 当从通知页面返回时，刷新未读数量
watch(() => route.fullPath, () => {
  // 任何路由变化都刷新（包括从 /forum/notifications 返回）
  loadUnreadCount()
})

onUnmounted(() => {
  if (unreadTimer) clearInterval(unreadTimer)
  document.removeEventListener('click', closeNotifDropdown)
})
</script>

<style scoped>
.forum-page {
  padding-bottom: 80px;
  min-height: 100vh;
  background: #f5f5f5;
}

.container {
  max-width: 800px;
  margin: 0 auto;
  padding: 0 16px;
}

/* 子导航栏 */
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

/* 帖子列表 */
.feed {
  padding: 16px 0;
}

.post-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.post-card {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
}

/* 帖子头部 */
.post-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.author-info {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
}

.author-detail {
  display: flex;
  flex-direction: column;
}

.author-name-row {
  display: flex;
  align-items: center;
  gap: 6px;
}

.author-name {
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

.artisan-tag {
  font-size: 10px !important;
  padding: 0 6px !important;
  height: 18px !important;
  line-height: 18px !important;
}

.post-time {
  font-size: 12px;
  color: #999;
}

.post-actions-top {
  display: flex;
  gap: 8px;
  align-items: center;
}

/* 帖子内容 */
.post-body {
  cursor: pointer;
}

.post-title {
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 8px;
  color: #333;
}

.post-content {
  font-size: 14px;
  line-height: 1.6;
  color: #444;
  margin: 0 0 12px;
  white-space: pre-wrap;
}

.post-images {
  display: grid;
  gap: 6px;
  margin-bottom: 12px;
}

.post-images.grid-1 { grid-template-columns: 1fr; max-width: 300px; }
.post-images.grid-2 { grid-template-columns: 1fr 1fr; }
.post-images.grid-3 { grid-template-columns: 1fr 1fr 1fr; }
.post-images.grid-4 { grid-template-columns: 1fr 1fr; }
.post-images.grid-5,
.post-images.grid-6 { grid-template-columns: 1fr 1fr 1fr; }
.post-images.grid-7,
.post-images.grid-8,
.post-images.grid-9 { grid-template-columns: 1fr 1fr 1fr; }

.post-image {
  width: 100%;
  aspect-ratio: 1;
  border-radius: 8px;
  cursor: pointer;
}

.post-video {
  margin-bottom: 12px;
  border-radius: 8px;
  overflow: hidden;
}

.video-player {
  width: 100%;
  max-height: 400px;
  background: #000;
}

/* 推广商品卡片 */
.linked-product-card {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 10px;
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

/* 商品选择下拉 */
.product-option {
  display: flex;
  align-items: center;
  gap: 8px;
}
.product-option-img {
  width: 32px;
  height: 32px;
  border-radius: 4px;
  flex-shrink: 0;
}
.product-option-price {
  margin-left: auto;
  color: #f56c6c;
  font-size: 12px;
  font-weight: 500;
}

/* 帖子底部互动 */
.post-footer {
  display: flex;
  gap: 24px;
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;
}

.interaction-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: #999;
  cursor: pointer;
  transition: color 0.2s;
}

.interaction-btn:hover {
  color: #409eff;
}

.interaction-btn.active {
  color: #409eff;
}

.interaction-btn .el-icon {
  font-size: 18px;
}

/* 加载更多 */
.load-more {
  text-align: center;
  padding: 20px 0;
}

/* 底部发帖按钮 */
.bottom-nav {
  position: fixed;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 200;
}

.publish-btn {
  width: 52px;
  height: 52px;
  background: linear-gradient(135deg, #409eff, #66b1ff);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.4);
  transition: transform 0.2s;
}

.publish-btn:hover {
  transform: scale(1.1);
}

/* 发帖表单 */
.create-form {
  padding: 8px 0;
}

.mb-16 {
  margin-bottom: 16px;
}

.upload-section {
  margin-bottom: 16px;
}

.upload-label {
  font-size: 13px;
  color: #666;
  margin-bottom: 8px;
}

.linked-section {
  margin-bottom: 16px;
}

/* Emoji 选择器 */
.emoji-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 2px;
  margin-bottom: 16px;
  max-height: 100px;
  overflow-y: auto;
}

.emoji-chip {
  font-size: 18px;
  cursor: pointer;
  padding: 3px 5px;
  border-radius: 4px;
  transition: background 0.15s;
  line-height: 1;
}

.emoji-chip:hover {
  background: #ecf5ff;
}

/* 加载状态 */
.loading-state {
  padding: 20px 0;
}

/* 响应式 */
@media (max-width: 768px) {
  .container {
    padding: 0 8px;
  }

  .post-card {
    border-radius: 8px;
    padding: 12px;
  }

  .post-images.grid-1 { max-width: 100%; }
}
</style>
