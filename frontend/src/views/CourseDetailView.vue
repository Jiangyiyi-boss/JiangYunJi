<template>
  <MainLayout>
    <div class="container">
      <div v-if="loading" v-loading="true" style="min-height: 400px" />

      <template v-else-if="course">
        <!-- 课程头部 -->
        <div class="course-header">
          <el-image v-if="course.cover_image" :src="course.cover_image" fit="cover" class="cover-img" />
          <div v-else class="cover-placeholder">
            <el-icon :size="50"><VideoCamera /></el-icon>
          </div>

          <h1 class="course-title">{{ course.title }}</h1>
          <p class="course-artisan">讲师：{{ course.artisan_name }}</p>

          <div class="course-stats">
            <span>{{ course.chapter_count }} 章节 · {{ course.lesson_count }} 课时</span>
            <span v-if="course.difficulty" class="stat-difficulty">{{ diffLabel(course.difficulty) }}</span>
            <span v-if="course.duration_hours" class="stat-duration">{{ course.duration_hours }}小时</span>
            <span v-if="course.target_audience" class="stat-audience">{{ audienceLabel(course.target_audience) }}</span>
            <span>{{ course.enrolled_count }} 人已学</span>
          </div>

          <!-- 课程标签 -->
          <div class="course-tags" v-if="course.tags?.length">
            <el-tag v-for="tag in course.tags" :key="tag" size="small" type="info">{{ tag }}</el-tag>
          </div>

          <div class="course-actions">
            <template v-if="enrolled">
              <el-progress :percentage="enrolled.progress" :stroke-width="8" style="max-width: 300px" />
              <el-tag type="success" style="margin-left: 12px">已报名</el-tag>
            </template>
            <template v-else>
              <el-button v-if="course.price > 0" type="danger" size="large" @click="handlePurchase">立即购买 ¥{{ course.price }}</el-button>
              <el-button v-else type="primary" size="large" @click="handleEnroll">立即报名</el-button>
            </template>
          </div>

          <!-- 技术介绍 -->
          <div class="course-desc">
            <h3>课程介绍</h3>
            <p>{{ course.description }}</p>
          </div>

          <!-- 付费课程购买须知 -->
          <div v-if="course.price > 0 && !enrolled" class="purchase-notice">
            <h4>购买须知</h4>
            <p style="white-space: pre-line">{{ course.purchase_notice || '1、本课程为付费内容，购买后永久观看\n2、支付完成后自动开通学习权限\n3、一经购买不退不换' }}</p>
          </div>
        </div>

        <!-- 课程目录 -->
        <div class="course-outline">
          <h3>课程目录</h3>
          <div v-for="(chapter, ci) in course.chapters" :key="chapter.id" class="outline-chapter">
            <div class="chapter-title" @click="toggleChapter(chapter.id)">
              <el-icon><component :is="openChapters.has(chapter.id) ? 'ArrowDown' : 'ArrowRight'" /></el-icon>
              <span>第{{ toChineseNum(ci + 1) }}章 {{ chapter.title }}</span>
            </div>
            <div v-show="openChapters.has(chapter.id)" class="chapter-lessons">
              <div
                v-for="(lesson, li) in chapter.lessons"
                :key="lesson.id"
                class="outline-lesson"
                :class="{ locked: !enrolled && !lesson.is_free && course.price > 0 }"
                @click="selectLesson(lesson)"
              >
                <span class="lesson-num">{{ ci + 1 }}.{{ li + 1 }}</span>
                <span class="lesson-name">{{ lesson.title }}</span>
                <span v-if="lesson.is_free && course.price > 0" class="free-badge">试看</span>
                <span class="lesson-dur">{{ formatDuration(lesson.duration) }}</span>
              </div>
            </div>
          </div>
        </div>
      </template>
    </div>
  </MainLayout>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import MainLayout from '@/components/MainLayout.vue'
import { courseApi } from '@/api/modules'
import { ElMessage, ElMessageBox } from 'element-plus'
import { VideoCamera } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const course = ref(null)
const loading = ref(true)
const enrolled = ref(null)
const openChapters = ref(new Set())

const toChineseNum = (n) => {
  const map = ['', '一', '二', '三', '四', '五', '六', '七', '八', '九', '十',
    '十一', '十二', '十三', '十四', '十五', '十六', '十七', '十八', '十九', '二十']
  return map[n] || String(n)
}

const toggleChapter = (id) => {
  if (openChapters.value.has(id)) {
    openChapters.value.delete(id)
  } else {
    openChapters.value.add(id)
  }
  openChapters.value = new Set(openChapters.value)
}

onMounted(async () => {
  try {
    course.value = await courseApi.getCourse(route.params.id)
    if (course.value.chapters?.length) {
      openChapters.value = new Set([course.value.chapters[0].id])
    }
    // 只有登录用户才查询报名状态
    if (userStore.token) {
      try {
        enrolled.value = await courseApi.getEnrollment(route.params.id)
      } catch (_) {}
    }
  } catch (err) {
    ElMessage.error('加载课程失败')
  } finally {
    loading.value = false
  }
})

const requireLogin = () => {
  ElMessageBox.confirm('请先登录，登录后方可操作', '提示', {
    confirmButtonText: '去登录',
    cancelButtonText: '取消',
    type: 'warning',
  }).then(() => {
    router.push({ path: '/login', query: { redirect: router.currentRoute.value.fullPath } })
  }).catch(() => {})
}

const selectLesson = (lesson) => {
  if (!userStore.token) {
    requireLogin()
    return
  }
  if (!enrolled.value && !lesson.is_free && course.value.price > 0) {
    ElMessage.warning('请先报名课程')
    return
  }
  router.push(`/course/${course.value.id}/learn?lesson=${lesson.id}`)
}

const handleEnroll = async () => {
  if (!userStore.token) { requireLogin(); return }
  try {
    enrolled.value = await courseApi.enroll(course.value.id)
    ElMessage.success('报名成功！')
  } catch (err) { ElMessage.error(err.detail || '报名失败') }
}

const handlePurchase = () => {
  if (!userStore.token) { requireLogin(); return }
  router.push(`/course-checkout/${course.value.id}`)
}

const formatDuration = (seconds) => {
  if (!seconds) return ''
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = seconds % 60
  if (h > 0) return `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
  return `${m}:${String(s).padStart(2, '0')}`
}

const diffLabel = (d) => ({ beginner: '入门', elementary: '初级', intermediate: '中级', advanced: '高级', master: '大师' }[d] || d)
const audienceLabel = (a) => ({ beginner: '适合零基础', hobbyist: '适合爱好者', professional: '适合从业者', all: '全年龄段' }[a] || a)
</script>

<style scoped>
.container { max-width: 860px; margin: 0 auto; padding: 20px; }

.course-header { margin-bottom: 30px; }
.cover-img { width: 100%; height: 360px; border-radius: 12px; object-fit: cover; }
.cover-placeholder {
  height: 360px; display: flex; align-items: center; justify-content: center;
  background: linear-gradient(135deg, #667eea, #764ba2); color: #fff; border-radius: 12px;
}
.course-title { font-size: 26px; margin: 20px 0 8px; }
.course-artisan { color: #666; margin: 0 0 12px; font-size: 15px; }
.course-stats { display: flex; gap: 24px; color: #999; font-size: 14px; margin-bottom: 12px; flex-wrap: wrap; }
.stat-difficulty { color: #409eff; }
.stat-duration { color: #e6a23c; }
.price-text { color: #f56c6c; font-weight: bold; font-size: 20px; }
.free-text { color: #67c23a; font-weight: bold; font-size: 20px; }
.course-tags { display: flex; gap: 8px; margin-bottom: 16px; flex-wrap: wrap; }
.course-actions { margin-bottom: 24px; display: flex; align-items: center; }

.course-desc { padding: 20px; background: #fafafa; border-radius: 8px; margin-bottom: 20px; }
.course-desc h3 { margin: 0 0 12px; font-size: 16px; }
.course-desc p { margin: 0; color: #666; line-height: 1.8; font-size: 14px; }

.purchase-notice {
  padding: 16px 20px; background: #fff7e6; border-radius: 8px; border: 1px solid #ffd591;
}
.purchase-notice h4 { margin: 0 0 8px; font-size: 14px; color: #fa8c16; }
.purchase-notice ul { margin: 0; padding-left: 18px; font-size: 13px; color: #666; line-height: 1.8; }

/* 课程目录 */
.course-outline { margin-bottom: 40px; }
.course-outline h3 { font-size: 18px; margin: 0 0 16px; }
.outline-chapter { margin-bottom: 8px; }
.chapter-title {
  display: flex; align-items: center; gap: 8px;
  padding: 12px 16px; cursor: pointer; font-size: 15px; font-weight: 600;
  background: #f5f7fa; border-radius: 6px; color: #333;
}
.chapter-title:hover { background: #eef0f4; }
.chapter-lessons { padding: 4px 0 4px 16px; }
.outline-lesson {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 16px; cursor: pointer; border-radius: 4px; font-size: 14px;
  transition: background 0.15s;
}
.outline-lesson:hover { background: #f5f7fa; }
.outline-lesson.locked { color: #ccc; cursor: not-allowed; }
.lesson-num { color: #999; font-size: 13px; min-width: 28px; }
.lesson-name { flex: 1; }
.free-badge { font-size: 11px; color: #67c23a; background: #f0f9eb; padding: 1px 6px; border-radius: 3px; }
.lesson-dur { font-size: 12px; color: #bbb; }
</style>