<template>
  <MainLayout>
    <div class="container">
      <div class="page-header-card">
        <el-button type="primary" @click="handleCreate">
          <el-icon><Plus /></el-icon> 创建课程
        </el-button>
        <router-link to="/notifications" class="msg-link">
          <el-badge :value="unreadCount" :hidden="unreadCount === 0" :max="99">
            <el-icon :size="20"><Bell /></el-icon>
          </el-badge>
          <span class="msg-text">消息</span>
        </router-link>
      </div>

      <div v-loading="loading" class="course-grid">
        <div
          v-for="course in courses"
          :key="course.id"
          class="course-card"
          @click="$router.push(`/artisan/courses/${course.id}/edit`)"
        >
          <div class="course-cover">
            <el-image v-if="course.cover_image" :src="course.cover_image" fit="cover" class="cover-img" />
            <div v-else class="cover-placeholder">
              <el-icon :size="40"><VideoCamera /></el-icon>
            </div>
            <div class="course-status-badge" :class="course.status">
              {{ statusLabel(course.status) }}
            </div>
          </div>
          <div class="course-info">
            <h3 class="course-title">{{ course.title }}</h3>
            <p class="course-desc">{{ course.description || '暂无简介' }}</p>
            <!-- 驳回原因 -->
            <div v-if="course.status === 'rejected' && course.reject_reason" class="reject-reason">
              <el-icon><WarningFilled /></el-icon> {{ course.reject_reason }}
            </div>
            <div class="course-meta">
              <span class="meta-item">
                <el-icon><Document /></el-icon>
                {{ course.lesson_count || 0 }} 课时
              </span>
              <span class="meta-item">
                <el-icon><User /></el-icon>
                {{ course.enrolled_count || 0 }} 报名
              </span>
              <span v-if="course.comment_count" class="meta-item">
                <el-icon><ChatDotRound /></el-icon>
                {{ course.comment_count }} 评论
              </span>
            </div>

            <!-- 最新评论 -->
            <div v-if="course.latest_comments?.length" class="course-comments" @click.stop>
              <div
                v-for="com in course.latest_comments"
                :key="com.id"
                class="comment-preview"
                @click="goToComment(course.id, com.id, com.lesson_id)"
              >
                <span class="comment-user">{{ com.user_nickname }}</span>
                <span class="comment-text">{{ com.content }}</span>
              </div>
            </div>

            <div class="course-footer">
              <span class="course-price" v-if="course.price > 0">¥{{ course.price }}</span>
              <el-tag v-else type="success" size="small">免费</el-tag>
              <div class="course-actions" @click.stop>
                <el-button size="small" type="primary" @click="$router.push(`/artisan/courses/${course.id}/edit`)">编辑</el-button>
                <el-button
                  v-if="course.status === 'draft' || course.status === 'rejected'"
                  size="small"
                  type="success"
                  @click="handleSubmit(course)"
                >{{ course.status === 'rejected' ? '重新提交' : '提交审核' }}</el-button>
                <el-button size="small" type="info" v-if="course.status === 'published'" @click="showEnrollments(course)">报名学员</el-button>
                <el-popconfirm
                  v-if="(course.status === 'draft' || course.status === 'pending' || course.status === 'rejected' || course.status === 'published') && (!course.enrolled_count || course.enrolled_count === 0)"
                  title="确定删除此课程？"
                  @confirm="handleDelete(course.id)"
                >
                  <template #reference>
                    <el-button size="small" type="danger">删除</el-button>
                  </template>
                </el-popconfirm>
                <el-tooltip
                  v-else-if="course.enrolled_count > 0"
                  content="已有学员报名，无法删除"
                  placement="top"
                >
                  <el-button size="small" type="info" disabled>删除</el-button>
                </el-tooltip>
              </div>
            </div>
          </div>
        </div>

        <el-empty v-if="!loading && !courses.length" description="暂无课程，点击创建课程开始" />
      </div>

      <!-- ===== Enrollment Modal ===== -->
      <el-dialog v-model="enrollVisible" :title="`${selectedCourse?.title} - 报名学员`" width="750px" @close="selectedCourse = null">
        <el-table :data="enrollments" v-loading="enrollLoading" stripe max-height="400">
          <el-table-column prop="user_nickname" label="学员昵称" width="140" />
          <el-table-column label="报名方式" width="100">
            <template #default="{ row }">
              <el-tag :type="row.type === 'purchased' ? 'warning' : 'success'" size="small">
                {{ row.type === 'purchased' ? '付费' : '免费' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="学习进度" width="120">
            <template #default="{ row }">
              <el-progress :percentage="row.progress" :stroke-width="6" />
            </template>
          </el-table-column>
          <el-table-column prop="enrolled_at" label="报名时间" width="170" />
          <el-table-column label="订单号" min-width="200">
            <template #default="{ row }">
              <el-link v-if="row.order_no" type="primary" @click="router.push(`/artisan/orders?orderNo=${row.order_no}`)">
                {{ row.order_no }}
              </el-link>
              <span v-else>-</span>
            </template>
          </el-table-column>
        </el-table>
        <div style="margin-top:12px;text-align:right">
          <el-pagination
            v-model:current-page="enrollPage"
            :page-size="50"
            :total="enrollTotal"
            layout="total, prev, next"
            @current-change="loadEnrollments"
          />
        </div>
      </el-dialog>
    </div>
  </MainLayout>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import MainLayout from '@/components/MainLayout.vue'
import { courseApi } from '@/api/modules'
import { ElMessage } from 'element-plus'
import { WarningFilled, Bell, ChatDotRound } from '@element-plus/icons-vue'
import { useCourseNotifications } from '@/composables/useNotifications'

const router = useRouter()
const { unreadCount } = useCourseNotifications()
const courses = ref([])
const loading = ref(false)

const loadCourses = async () => {
  loading.value = true
  try {
    const res = await courseApi.getArtisanCourses({ skip: 0, limit: 50 })
    courses.value = res.items
  } catch (err) {
    ElMessage.error('加载课程列表失败')
  } finally {
    loading.value = false
  }
}

onMounted(loadCourses)

const statusLabel = (status) => {
  const map = { draft: '草稿', pending: '审核中', published: '已发布', rejected: '已驳回' }
  return map[status] || status
}

const handleCreate = () => {
  router.push('/artisan/courses/new')
}

const handleSubmit = async (row) => {
  try {
    await courseApi.updateCourse(row.id, { status: 'pending' })
    ElMessage.success(row.status === 'rejected' ? '已重新提交审核' : '已提交审核')
    loadCourses()
  } catch (err) {
    ElMessage.error('提交失败')
  }
}

const handleDelete = async (id) => {
  try {
    await courseApi.deleteCourse(id)
    ElMessage.success('已删除')
    loadCourses()
  } catch (err) {
    ElMessage.error(err.detail || '删除失败')
  }
}

const goToComment = (courseId, commentId, lessonId) => {
  let query = `tab=comments&comment_id=${commentId}`
  if (lessonId) {
    query += `&lesson=${lessonId}`
  }
  router.push(`/course/${courseId}?${query}`)
}

// ===== Enrollment Modal =====
const enrollVisible = ref(false)
const enrollments = ref([])
const enrollLoading = ref(false)
const enrollPage = ref(1)
const enrollTotal = ref(0)
const selectedCourse = ref(null)

const showEnrollments = async (course) => {
  selectedCourse.value = course
  enrollPage.value = 1
  enrollVisible.value = true
  await loadEnrollments()
}

const loadEnrollments = async () => {
  if (!selectedCourse.value) return
  enrollLoading.value = true
  try {
    const res = await courseApi.getCourseEnrollments(selectedCourse.value.id, {
      skip: (enrollPage.value - 1) * 50,
      limit: 50,
    })
    enrollments.value = res.items || []
    enrollTotal.value = res.total || 0
  } catch (err) {
    ElMessage.error('加载学员列表失败')
  } finally {
    enrollLoading.value = false
  }
}
</script>

<style scoped>
.page-header-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 20px 0;
}
.page-title { margin: 0; }

.msg-link {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #606266;
  text-decoration: none;
  font-size: 14px;
  transition: color 0.2s;
}
.msg-link:hover { color: #409eff; }
.msg-text { font-size: 14px; }

.course-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
}

.course-card {
  background: var(--color-surface);
  border-radius: var(--radius-md);
  overflow: hidden;
  cursor: pointer;
  transition: all var(--transition-base);
  border: 1px solid var(--color-border-light);
  animation: fadeInUp 0.4s ease forwards;
}

.course-card:hover {
  transform: translateY(-6px);
  box-shadow: var(--shadow-lg);
  border-color: transparent;
}

.course-cover {
  position: relative;
  width: 100%;
  padding-top: 56.25%; /* 16:9 */
  background: var(--color-bg-warm);
  overflow: hidden;
}

.cover-img {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  transition: transform var(--transition-base);
}

.course-card:hover .cover-img {
  transform: scale(1.05);
}

.cover-placeholder {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-light);
}

.course-status-badge {
  position: absolute;
  top: 10px;
  right: 10px;
  padding: 2px 10px;
  border-radius: var(--radius-sm);
  font-size: 12px;
  font-weight: 500;
  color: #fff;
}

.course-status-badge.published { background: #67c23a; }
.course-status-badge.draft { background: #909399; }
.course-status-badge.pending { background: #e6a23c; }
.course-status-badge.rejected { background: #f56c6c; }

.reject-reason {
  display: flex;
  align-items: center;
  gap: 6px;
  background: #fef0f0;
  color: #f56c6c;
  font-size: 12px;
  padding: 6px 10px;
  border-radius: 6px;
  margin-bottom: 8px;
}

.course-info {
  padding: var(--space-md);
}

.course-title {
  margin: 0 0 8px;
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text);
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.course-desc {
  margin: 0 0 12px;
  font-size: 13px;
  color: var(--color-text-secondary);
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.course-meta {
  display: flex;
  gap: 16px;
  margin-bottom: 12px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--color-text-secondary);
}

/* 最新评论 */
.course-comments {
  margin-bottom: 12px;
  padding: 10px;
  background: #fafafa;
  border-radius: 8px;
  border: 1px solid #f0f0f0;
}

.comment-preview {
  display: flex;
  gap: 6px;
  padding: 3px 0;
  font-size: 12px;
  line-height: 1.5;
  cursor: pointer;
  border-radius: 4px;
  transition: background 0.15s;
  overflow: hidden;
}

.comment-preview:hover {
  background: #f0f5ff;
}

.comment-preview + .comment-preview {
  border-top: 1px solid #f0f0f0;
  margin-top: 3px;
  padding-top: 6px;
}

.comment-user {
  color: #409eff;
  font-weight: 500;
  white-space: nowrap;
  flex-shrink: 0;
}

.comment-user::after {
  content: "：";
  color: #999;
}

.comment-text {
  color: #666;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.course-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 12px;
  border-top: 1px solid var(--color-border-light);
}

.course-price {
  font-size: 20px;
  font-weight: 700;
  color: var(--color-accent);
}

.course-actions {
  display: flex;
  gap: 8px;
}
</style>
