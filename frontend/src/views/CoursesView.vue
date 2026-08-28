<template>
  <MainLayout>
    <div class="container">
      <div class="page-header">
        <div class="search-bar">
          <div class="search-input-wrapper">
            <el-input v-model="keyword" placeholder="搜索课程..." clearable @clear="load" @keyup.enter="load" @input="handleKeywordInput" @focus="showSuggestions = true" @blur="hideSuggestionsDelayed" style="width:260px" size="large">
              <template #prefix><el-icon><Search /></el-icon></template>
            </el-input>
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
          <el-select v-model="priceType" placeholder="全部" clearable @change="load" size="large" style="width:120px">
            <el-option label="全部" value="" />
            <el-option label="免费" value="free" />
            <el-option label="付费" value="paid" />
          </el-select>
          <el-button type="primary" size="large" @click="load">搜索</el-button>
        </div>
        <div v-if="userStore.user" class="header-actions">
          <router-link to="/notifications" class="action-link notif-link">
            <el-badge :value="unreadCount" :hidden="unreadCount === 0" :max="99">
              <el-icon><Bell /></el-icon>
            </el-badge>
            <span>消息</span>
          </router-link>
          <router-link to="/my-courses" class="action-link">
            <el-icon><Reading /></el-icon> 我的课程
          </router-link>
          <router-link to="/browse-history" class="action-link">
            <el-icon><Clock /></el-icon> 浏览记录
          </router-link>
        </div>
      </div>

      <div v-loading="loading" class="course-grid">
        <el-empty v-if="!courses.length" description="暂无课程" />
        <div v-for="c in courses" :key="c.id" class="course-card" @click="goDetail(c.id)">
          <div class="cover">
            <el-image v-if="c.cover_image" :src="c.cover_image" fit="cover" class="cover-img" />
            <div v-else class="cover-placeholder"><el-icon :size="40"><VideoCamera /></el-icon></div>
            <div v-if="c.price > 0" class="price-tag">¥{{ c.price }}</div>
            <div v-else class="free-tag">免费</div>
          </div>
          <div class="info">
            <h3 v-html="highlightText(c.title)"></h3>
            <p class="desc" v-html="highlightText(c.description)"></p>
            <div class="meta">
              <span>{{ c.lesson_count || 0 }} 课时</span>
              <span>{{ c.enrolled_count || 0 }} 人已学</span>
            </div>
            <div class="actions" @click.stop>
              <template v-if="c.enrolled">
                <el-button type="success" size="small" @click="$router.push(`/course/${c.id}/learn`)">进入学习</el-button>
              </template>
              <template v-else-if="c.price > 0">
                <el-button type="primary" size="small" @click="buyCourse(c)">立即购买</el-button>
              </template>
              <template v-else>
                <el-button type="success" size="small" plain @click="joinFree(c)">立即报名</el-button>
              </template>
            </div>
          </div>
        </div>
      </div>
    </div>
  </MainLayout>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import MainLayout from '@/components/MainLayout.vue'
import { courseApi } from '@/api/modules'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Reading, Clock, Bell } from '@element-plus/icons-vue'
import { useCourseNotifications } from '@/composables/useNotifications'

const router = useRouter()
const { unreadCount } = useCourseNotifications()
const userStore = useUserStore()
const courses = ref([])
const keyword = ref('')
const priceType = ref('')
const loading = ref(false)
const showSuggestions = ref(false)
const suggestions = ref([])
const suggestionTimer = ref(null)

const load = async () => {
  loading.value = true
  try {
    const params = { limit: 50 }
    if (keyword.value) params.keyword = keyword.value
    if (priceType.value) params.price_type = priceType.value
    const res = await courseApi.getCourses(params)
    courses.value = (res.items || []).map(c => ({ ...c, enrolled: false }))
    // 只有登录用户才查询报名状态，避免游客触发 401 跳转
    if (userStore.token) {
      try {
        const myRes = await courseApi.getMyEnrollments({ limit: 200 })
        const myIds = new Set((myRes.items || []).map(e => e.course_id))
        courses.value.forEach(c => { if (myIds.has(c.id)) c.enrolled = true })
      } catch {}
    }
  } finally { loading.value = false }
}

const goDetail = (id) => router.push(`/course/${id}`)
const requireLogin = () => {
  ElMessageBox.confirm('请先登录，登录后方可操作', '提示', {
    confirmButtonText: '去登录',
    cancelButtonText: '取消',
    type: 'warning',
  }).then(() => router.push({ path: '/login', query: { redirect: router.currentRoute.value.fullPath } })).catch(() => {})
}
const joinFree = async (c) => {
  if (!userStore.token) { requireLogin(); return }
  try { await courseApi.enroll(c.id); ElMessage.success('报名成功'); c.enrolled = true }
  catch (err) { ElMessage.error(err.detail || '报名失败') }
}
const buyCourse = (c) => {
  if (!userStore.token) { requireLogin(); return }
  router.push(`/checkout?course_id=${c.id}`)
}

// 搜索建议（自动补全）
const handleKeywordInput = () => {
  if (keyword.value.length > 0) {
    if (suggestionTimer.value) clearTimeout(suggestionTimer.value)
    suggestionTimer.value = setTimeout(() => {
      loadSuggestions()
    }, 300)
  } else {
    suggestions.value = []
  }
}

const loadSuggestions = async () => {
  if (!keyword.value) return
  try {
    const response = await courseApi.suggestCourses({
      prefix: keyword.value,
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
  keyword.value = suggestion
  showSuggestions.value = false
  load()
}

const highlightSuggestion = (text) => {
  if (!keyword.value) return text
  const regex = new RegExp(`(${keyword.value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi')
  return text.replace(regex, '<strong style="color: #409eff;">$1</strong>')
}

const escapeHtml = (text) => {
  if (!text) return text
  return String(text)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;')
}

// 高亮搜索结果中的关键词（与商品搜索页一致）
const highlightText = (text) => {
  if (!keyword.value || !text) return escapeHtml(text)
  const escaped = escapeHtml(text)
  const safeKeyword = keyword.value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  const regex = new RegExp(`(${safeKeyword})`, 'gi')
  return escaped.replace(regex, '<strong style="color: #409eff;">$1</strong>')
}

const hideSuggestionsDelayed = () => {
  setTimeout(() => {
    showSuggestions.value = false
  }, 200)
}

onMounted(load)
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; margin: 20px 0; flex-wrap: wrap; gap: 12px; }
.page-title { margin: 0; }
.search-bar { display: flex; gap: 10px; align-items: center; }
.search-input-wrapper { position: relative; }
.suggestions-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  width: 260px;
  background: #fff;
  border: 1px solid #dcdfe6;
  border-radius: 0 0 8px 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 1000;
  max-height: 320px;
  overflow-y: auto;
}
.suggestion-item {
  padding: 10px 16px;
  cursor: pointer;
  font-size: 14px;
  color: #333;
  transition: background 0.15s;
  text-align: left;
}
.suggestion-item:hover {
  background: #f5f7fa;
}
.header-actions { display: flex; gap: 16px; align-items: center; }
.action-link {
  display: flex;
  align-items: center;
  gap: 4px;
  color: #4f6ef7;
  font-size: 14px;
  font-weight: 500;
  text-decoration: none;
  padding: 6px 12px;
  border-radius: 6px;
  transition: background 0.2s;
}
.action-link:hover {
  background: #ecf5ff;
}
.course-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 20px; margin-top: 20px; }
.course-card { background: #fff; border-radius: 12px; overflow: hidden; cursor: pointer; border: 1px solid #f0f0f0; transition: transform .2s, box-shadow .2s; }
.course-card:hover { transform: translateY(-4px); box-shadow: 0 8px 24px rgba(0,0,0,.1); }
.cover { position: relative; padding-top: 56%; background: #f5f5f5; overflow: hidden; }
.cover-img { position: absolute; top: 0; left: 0; width: 100%; height: 100%; }
.cover-placeholder { position: absolute; top: 0; left: 0; width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; color: #ccc; }
.price-tag, .free-tag { position: absolute; bottom: 8px; right: 8px; padding: 2px 10px; border-radius: 4px; font-size: 14px; font-weight: 700; color: #fff; }
.price-tag { background: #f56c6c; } .free-tag { background: #67c23a; }
.info { padding: 14px 16px; } .info h3 { font-size: 16px; font-weight: 600; margin: 0 0 6px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.desc { font-size: 13px; color: #999; margin: 0 0 10px; line-height: 1.4; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.meta { display: flex; gap: 16px; font-size: 12px; color: #bbb; margin-bottom: 10px; }
.actions { display: flex; gap: 8px; }
</style>
