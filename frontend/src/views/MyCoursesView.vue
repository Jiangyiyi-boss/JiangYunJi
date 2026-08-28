<template>
  <MainLayout>
    <div class="container">
      <div class="page-header-card">
        <h2 class="page-title">我的课程</h2>
        <el-radio-group v-model="filterType" @change="loadCourses">
          <el-radio-button value="all">全部</el-radio-button>
          <el-radio-button value="free">免费课程</el-radio-button>
          <el-radio-button value="purchased">付费课程</el-radio-button>
        </el-radio-group>
      </div>

      <div v-loading="loading" class="course-grid">
        <el-empty v-if="!courses.length" :description="emptyText" />
        <div v-for="c in courses" :key="c.id" class="course-card" @click="goLearn(c.id)">
          <div class="cover">
            <el-image v-if="c.cover_image" :src="c.cover_image" fit="cover" class="cover-img" />
            <div v-else class="cover-placeholder"><el-icon :size="40"><VideoCamera /></el-icon></div>
            <div class="type-tag" :class="c.type">{{ c.type === 'free' ? '免费' : '已购' }}</div>
          </div>
          <div class="info">
            <h3>{{ c.title }}</h3>
            <p class="desc">{{ c.description || '暂无简介' }}</p>
            <div class="meta">
              <span>{{ c.lesson_count || 0 }} 课时</span>
              <span>进度 {{ c.progress }}%</span>
            </div>
            <div class="progress-bar">
              <el-progress :percentage="c.progress" :stroke-width="6" :show-text="false" />
            </div>
            <div class="actions" @click.stop>
              <el-button type="primary" size="small" @click="goLearn(c.id)">进入学习</el-button>
              <el-button v-if="c.type === 'free'" type="danger" size="small" plain @click="handleDrop(c)">退出课程</el-button>
            </div>
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
import { courseApi } from '@/api/modules'
import { ElMessage, ElMessageBox } from 'element-plus'
import { VideoCamera } from '@element-plus/icons-vue'

const router = useRouter()
const courses = ref([])
const loading = ref(false)
const filterType = ref('all')

const emptyText = computed(() => {
  if (filterType.value === 'free') return '暂无免费课程'
  if (filterType.value === 'purchased') return '暂无付费课程'
  return '还没有加入任何课程，去匠艺学堂看看吧'
})

const loadCourses = async () => {
  loading.value = true
  try {
    const res = await courseApi.getMyCourses({ course_type: filterType.value, limit: 50 })
    courses.value = res.items || []
  } catch (err) {
    ElMessage.error(err.detail || '加载失败')
  } finally {
    loading.value = false
  }
}

const goLearn = (id) => {
  router.push(`/course/${id}/learn`)
}

const handleDrop = async (course) => {
  try {
    await ElMessageBox.confirm(
      `确定要退出「${course.title}」吗？退出后将无法继续学习。`,
      '退出课程',
      { confirmButtonText: '确定退出', cancelButtonText: '取消', type: 'warning' }
    )
    await courseApi.dropCourse(course.id)
    ElMessage.success('已退出课程')
    loadCourses()
  } catch (err) {
    if (err !== 'cancel') {
      ElMessage.error(err.detail || '退出失败')
    }
  }
}

onMounted(() => {
  loadCourses()
})
</script>

<style scoped>
.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.page-header-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.page-title {
  font-size: 22px;
  font-weight: 600;
  color: #333;
  margin: 0;
}

.course-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
}

.course-card {
  background: #fff;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.course-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.cover {
  position: relative;
  height: 160px;
  background: #f5f5f5;
}

.cover-img {
  width: 100%;
  height: 100%;
}

.cover-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #ccc;
}

.type-tag {
  position: absolute;
  top: 8px;
  right: 8px;
  padding: 2px 10px;
  border-radius: 4px;
  font-size: 12px;
  color: #fff;
}

.type-tag.free {
  background: #67c23a;
}

.type-tag.purchased {
  background: #409eff;
}

.info {
  padding: 16px;
}

.info h3 {
  font-size: 16px;
  margin: 0 0 8px;
  color: #333;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.desc {
  font-size: 13px;
  color: #999;
  margin: 0 0 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.meta {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #999;
  margin-bottom: 12px;
}

.progress-bar {
  margin-bottom: 12px;
}

.actions {
  display: flex;
  gap: 8px;
}
</style>
