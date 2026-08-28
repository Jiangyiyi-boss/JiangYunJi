<template>
  <MainLayout>
  <div class="user-profile-page">
    <!-- 顶部个人信息 -->
    <div class="profile-header">
      <div class="container">
        <div class="header-content">
          <el-avatar :size="80" :src="user?.avatar" class="avatar">
            {{ user?.nickname?.[0] || 'U' }}
          </el-avatar>
          <div class="info">
            <div class="name-row">
              <h2>{{ user?.nickname }}</h2>
              <el-tag v-if="user?.role === 'artisan'" size="small" type="warning" effect="dark">
                非遗匠人
              </el-tag>
            </div>
            <p class="bio">{{ user?.bio || '这个人很懒，什么都没写~' }}</p>
          </div>
          <div class="header-btns" v-if="!isSelf">
            <el-button
              v-if="isArtisan"
              type="primary"
              size="small"
              plain
              @click="goToShop"
            >
              进入店铺
            </el-button>
            <el-button
              :type="isFollowed ? 'default' : 'primary'"
              @click="handleFollow"
              :loading="following"
            >
              {{ isMutualFollowed ? '已互相关注' : (isFollowed ? '已关注' : '+ 关注') }}
            </el-button>
          </div>
        </div>
        <div class="stats">
          <div class="stat-item">
            <span class="stat-value">{{ userStats.likes }}</span>
            <span class="stat-label">获赞</span>
          </div>
          <div class="stat-item">
            <span class="stat-value">{{ userStats.followers }}</span>
            <span class="stat-label">粉丝</span>
          </div>
          <div class="stat-item">
            <span class="stat-value">{{ userStats.following }}</span>
            <span class="stat-label">关注</span>
          </div>
          <div class="stat-item" v-if="isArtisan">
            <span class="stat-value">{{ userStats.products }}</span>
            <span class="stat-label">商品</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 内容区 -->
    <div class="container">
      <div class="content">
        <!-- 标签切换 -->
        <div class="profile-tabs">
          <div
            :class="['tab', { active: activeTab === 'all' }]"
            @click="switchTab('all')"
          >全部帖子</div>
          <template v-if="isSelf">
            <div :class="['tab', { active: activeTab === 'favorites' }]" @click="switchTab('favorites')">收藏</div>
            <div :class="['tab', { active: activeTab === 'liked' }]" @click="switchTab('liked')">喜欢</div>
            <div :class="['tab', { active: activeTab === 'drafts' }]" @click="switchTab('drafts')">草稿</div>
          </template>
        </div>

        <div v-if="displayPosts.length === 0" class="empty">
          <el-empty :description="emptyText" />
        </div>
        <div v-else class="post-list">
          <div v-for="post in displayPosts" :key="post._id || post.id" class="post-card" @click="$router.push(`/forum/${post._id || post.id}`)">
            <div class="post-card-header">
              <div class="post-card-title">
                <h4>{{ post.title || post.content?.slice(0, 50) }}</h4>
                <el-tag v-if="isSelf && post.status === 'pending'" type="warning" size="small">待审核</el-tag>
                <el-tag v-else-if="isSelf && post.status === 'rejected'" type="danger" size="small">已拒绝</el-tag>
                <el-tag v-else-if="isSelf && post.status === 'draft'" type="info" size="small">草稿</el-tag>
              </div>
              <el-button
                v-if="isSelf"
                type="danger"
                size="small"
                plain
                @click.stop="handleDeletePost(post)"
              >
                删除
              </el-button>
            </div>
            <p v-if="post.title && post.content" class="post-text">{{ post.content?.slice(0, 100) }}</p>
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
            <div v-if="post.video_url" class="post-video">
              <video :src="post.video_url" controls class="video-player" @click.stop />
            </div>
            <!-- 推广商品 -->
            <div v-if="post.linked_products?.length" class="linked-product-card" @click.stop="$router.push(`/product/${getProductId(post.linked_products[0])}`)">
              <div class="linked-product-img-wrap">
                <img v-if="getProductField(post.linked_products[0], 'image')" :src="getProductField(post.linked_products[0], 'image')" class="linked-product-img" />
              </div>
              <div class="linked-product-info">
                <div class="linked-product-name">{{ getProductField(post.linked_products[0], 'name') || '推广商品' }}</div>
                <div class="linked-product-price">¥{{ getProductField(post.linked_products[0], 'price') }}</div>
              </div>
              <el-icon class="linked-product-arrow"><ArrowRight /></el-icon>
            </div>
            <span class="time">{{ formatTime(post.created_at) }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
  </MainLayout>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowRight } from '@element-plus/icons-vue'
import { forumApi, artisanApi, productApi } from '@/api/modules'
import { useUserStore } from '@/stores/user'
import MainLayout from '@/components/MainLayout.vue'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const userId = parseInt(route.params.id)
const user = ref(null)
const posts = ref([])
const favPosts = ref([])
const likedPosts = ref([])
const draftPosts = ref([])
const products = ref([])
const artisanInfo = ref(null)
const isFollowed = ref(false)
const isMutualFollowed = ref(false)
const following = ref(false)
const userStats = ref({ likes: 0, followers: 0, following: 0, products: 0 })
const activeTab = ref('all')

const isSelf = computed(() => userStore.user?.id === userId)
const isArtisan = computed(() => user.value?.role === 'artisan')

const emptyText = computed(() => {
  const map = { all: '还没有发布帖子', favorites: '还没有收藏帖子', liked: '还没有喜欢帖子', drafts: '还没有草稿' }
  return map[activeTab.value] || '暂无内容'
})

const displayPosts = computed(() => {
  if (activeTab.value === 'favorites') return favPosts.value
  if (activeTab.value === 'liked') return likedPosts.value
  if (activeTab.value === 'drafts') return draftPosts.value
  return posts.value
})

const loadUser = async () => {
  // 看自己时直接用登录态数据（确保有头像）
  if (isSelf.value && userStore.user) {
    user.value = {
      id: userStore.user.id,
      nickname: userStore.user.nickname || userStore.user.username,
      avatar: userStore.user.avatar || '',
      role: userStore.user.role,
      bio: userStore.user.bio || '',
    }
    userStats.value.likes = 0
    userStats.value.followers = 0
    userStats.value.following = 0
    userStats.value.products = 0
  }
  try {
    const res = await forumApi.getPosts({ user_id: userId, limit: 1 })
    if (res.items?.length) {
      const firstPost = res.items[0]
      // 非自己时从帖子数据取；自己时保留登录态头像
      if (!isSelf.value) {
        user.value = {
          id: userId,
          nickname: firstPost.author_nickname,
          avatar: firstPost.author_avatar,
          role: firstPost.author_role,
          bio: '',
        }
      }
      isFollowed.value = firstPost.is_followed || false
      isMutualFollowed.value = firstPost.is_mutual_followed || false

      if (firstPost.author_role === 'artisan' && firstPost.author_artisan_id) {
        loadArtisanInfo(firstPost.author_artisan_id)
        loadProductCount(firstPost.author_artisan_id)
      }
    } else if (!isSelf.value) {
      // 没有帖子时，通过用户信息接口获取
      try {
        const profile = await forumApi.getUserProfile(userId)
        user.value = {
          id: userId,
          nickname: profile.nickname,
          avatar: profile.avatar,
          role: profile.role,
          bio: profile.bio || '',
        }
        if (profile.stats) {
          userStats.value = {
            likes: profile.stats.likes || 0,
            followers: profile.stats.followers || 0,
            following: profile.stats.following || 0,
            products: userStats.value.products
          }
        }
        if (profile.role === 'artisan' && profile.artisan_id) {
          loadArtisanInfo(profile.artisan_id)
          loadProductCount(profile.artisan_id)
        }
        // 获取关注状态
        const followRes = await forumApi.getFollowing(userStore.user?.id, { limit: 1000 })
        isFollowed.value = followRes.items?.some(f => f.following_id === userId) || false
      } catch (err) {
        console.error('获取用户信息失败:', err)
      }
    }
  } catch (err) {
    console.error(err)
  }
}

const loadArtisanInfo = async (artisanId) => {
  try {
    artisanInfo.value = await artisanApi.getArtisan(artisanId)
  } catch (err) {
    console.error(err)
  }
}

const loadProductCount = async (artisanId) => {
  try {
    const res = await productApi.getProducts({ artisan_id: artisanId, limit: 1 })
    userStats.value.products = res.total || 0
  } catch (err) {
    console.error(err)
  }
}

const loadPosts = async () => {
  try {
    // 显示已通过的帖子（草稿在"草稿"标签单独显示）
    const params = { user_id: userId, limit: 50, status: 'approved' }
    const res = await forumApi.getPosts(params)
    posts.value = res.items || []
    const total = posts.value.reduce((sum, p) => sum + (p.like_count || 0), 0)
    userStats.value.likes = total
  } catch (err) {
    console.error(err)
  }
}

const loadFollowers = async () => {
  try {
    const res = await forumApi.getFollowers(userId, { limit: 1 })
    userStats.value.followers = res.total || 0
  } catch (err) {
    console.error(err)
  }
}

const loadFollowing = async () => {
  try {
    const res = await forumApi.getFollowing(userId, { limit: 1 })
    userStats.value.following = res.total || 0
  } catch (err) {
    console.error(err)
  }
}

const handleFollow = async () => {
  if (!userStore.user) {
    ElMessage.warning('请先登录')
    router.push('/login')
    return
  }
  following.value = true
  try {
    const res = await forumApi.followUser(userId)
    isFollowed.value = res.action === 'followed'
    isMutualFollowed.value = res.is_mutual_followed || false
    ElMessage.success(isFollowed.value ? '已关注' : '已取消关注')
    userStats.value.followers += isFollowed.value ? 1 : -1
  } catch (err) {
    ElMessage.error('操作失败')
  } finally {
    following.value = false
  }
}

const goToShop = () => {
  const artisanId = artisanInfo.value?.id
  if (artisanId) {
    router.push(`/artisan/${artisanId}`)
  }
}

const handleDeletePost = async (post) => {
  const postId = post._id || post.id
  try {
    await ElMessageBox.confirm('确定删除此帖子吗？删除后不可恢复。', '确认删除', { type: 'warning' })
    await forumApi.deletePost(postId)
    ElMessage.success('删除成功')
    // 从当前列表中移除
    posts.value = posts.value.filter(p => (p._id || p.id) !== postId)
    favPosts.value = favPosts.value.filter(p => (p._id || p.id) !== postId)
    likedPosts.value = likedPosts.value.filter(p => (p._id || p.id) !== postId)
    draftPosts.value = draftPosts.value.filter(p => (p._id || p.id) !== postId)
  } catch (err) {
    if (err !== 'cancel') ElMessage.error('删除失败')
  }
}

const switchTab = (tab) => {
  activeTab.value = tab
  if (tab === 'favorites' && !favPosts.value.length) loadFavorites()
  if (tab === 'liked' && !likedPosts.value.length) loadLiked()
  if (tab === 'drafts' && !draftPosts.value.length) loadDrafts()
}

const loadFavorites = async () => {
  try {
    const res = await forumApi.getFavorites()
    favPosts.value = res.items || []
  } catch (_) {}
}

const loadLiked = async () => {
  try {
    const res = await forumApi.getPosts({ liked_by: userId, limit: 50 })
    likedPosts.value = res.items || []
  } catch (_) {}
}

const loadDrafts = async () => {
  try {
    const res = await forumApi.getDrafts()
    draftPosts.value = res.items || []
  } catch (_) {}
}

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

// 兼容新旧 linked_products 格式：新格式是对象 {id, name, image, price}，旧格式是数字 ID
const getProductId = (item) => typeof item === 'object' ? item.id : item
const getProductField = (item, field) => typeof item === 'object' ? (item[field] || '') : ''

onMounted(() => {
  loadUser()
  loadPosts()
  loadFollowers()
  loadFollowing()
})
</script>

<style scoped>
.user-profile-page {
  padding-bottom: 40px;
  min-height: 100vh;
  background: #f5f5f5;
}

.container {
  max-width: 800px;
  margin: 0 auto;
  padding: 0 16px;
}

.profile-header {
  background: #fff;
  padding: 24px 0;
}

.header-content {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
}

.header-btns {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.name-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.name-row h2 {
  margin: 0;
  font-size: 20px;
}

.bio {
  margin: 8px 0 0;
  color: #666;
  font-size: 14px;
}

.stats {
  display: flex;
  gap: 32px;
}

.stat-item {
  text-align: center;
}

.stat-value {
  display: block;
  font-size: 20px;
  font-weight: 600;
  color: #333;
}

.stat-label {
  font-size: 13px;
  color: #999;
}

.content {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  margin-top: 16px;
}

.profile-tabs {
  display: flex;
  gap: 0;
  border-bottom: 2px solid #f0f0f0;
  margin-bottom: 16px;
}

.tab {
  padding: 10px 20px;
  font-size: 14px;
  color: #666;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  margin-bottom: -2px;
  transition: color 0.2s, border-color 0.2s;
}

.tab:hover { color: #3B4F6B; }

.tab.active {
  color: #3B4F6B;
  font-weight: 600;
  border-bottom-color: #3B4F6B;
}

.content h3 {
  margin: 0 0 16px;
  font-size: 16px;
  color: #333;
}

.post-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.post-card {
  padding: 12px;
  border-radius: 8px;
  background: #fafafa;
  cursor: pointer;
}

.post-card:hover { background: #f0f0f0; }

.post-card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8px;
}

.post-card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
}
.post-card-title h4 {
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.post-card-header h4 {
  flex: 1;
  min-width: 0;
}

.post-card h4 {
  margin: 0 0 4px;
  font-size: 14px;
  color: #333;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.post-card .time { font-size: 12px; color: #999; }

.post-text {
  margin: 4px 0 8px;
  font-size: 13px;
  color: #666;
  line-height: 1.5;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.post-images {
  display: grid;
  gap: 4px;
  margin: 8px 0;
}
.post-images.grid-1 { grid-template-columns: 1fr; max-width: 300px; }
.post-images.grid-2 { grid-template-columns: 1fr 1fr; }
.post-images.grid-3 { grid-template-columns: 1fr 1fr 1fr; }
.post-images.grid-4 { grid-template-columns: 1fr 1fr; }
.post-images.grid-5, .post-images.grid-6 { grid-template-columns: 1fr 1fr 1fr; }
.post-images.grid-7, .post-images.grid-8, .post-images.grid-9 { grid-template-columns: 1fr 1fr 1fr; }

.post-image {
  width: 100%;
  aspect-ratio: 1;
  border-radius: 6px;
  object-fit: cover;
  cursor: pointer;
}

.post-video {
  margin: 8px 0;
  border-radius: 8px;
  overflow: hidden;
}
.video-player {
  width: 100%;
  max-height: 300px;
  border-radius: 8px;
  background: #000;
}

.empty { padding: 40px 0; }

/* 推广商品卡片 */
.linked-product-card {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 10px;
  padding: 10px 12px;
  background: #f5f5f5;
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
  background: #e8e8e8;
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
