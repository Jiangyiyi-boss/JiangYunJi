<template>
  <MainLayout>
    <div class="checkout-container">
      <h2 class="page-title">确认订单</h2>

      <div class="checkout-content">
        <!-- 左侧：课程信息 -->
        <div class="checkout-main">
          <div class="section-card">
            <div class="section-header">
              <h3><el-icon><Reading /></el-icon> 课程信息</h3>
            </div>

            <div class="course-info">
              <img v-if="course.cover_image" :src="course.cover_image" class="course-cover" />
              <div v-else class="cover-placeholder">
                <el-icon :size="40"><VideoCamera /></el-icon>
              </div>
              <div class="course-detail">
                <h3 class="course-name">{{ course.title }}</h3>
                <p class="course-artisan">讲师：{{ course.artisan_name }}</p>
                <div class="course-meta">
                  <span>{{ course.chapter_count }} 章节 · {{ course.lesson_count }} 课时</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 右侧：价格明细 -->
        <div class="checkout-sidebar">
          <div class="price-card">
            <h3>价格明细</h3>

            <div class="price-row">
              <span>课程价格</span>
              <span>¥{{ course.price }}</span>
            </div>

            <el-divider />

            <div class="price-total">
              <span>合计</span>
              <span class="total-amount">¥{{ course.price }}</span>
            </div>

            <el-button
              type="danger"
              size="large"
              class="confirm-btn"
              :loading="submitting"
              @click="handleConfirmOrder"
            >
              确认购买
            </el-button>

            <div class="tips">
              <el-icon><InfoFilled /></el-icon>
              <span>请在10分钟内完成支付，超时订单将自动取消</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </MainLayout>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Reading, VideoCamera, InfoFilled } from '@element-plus/icons-vue'
import MainLayout from '@/components/MainLayout.vue'
import { courseApi, orderApi } from '@/api/modules'

const route = useRoute()
const router = useRouter()

const course = ref({})
const submitting = ref(false)

onMounted(async () => {
  try {
    course.value = await courseApi.getCourse(route.params.courseId)
    if (!course.value) {
      ElMessage.error('课程不存在')
      router.push('/courses')
    }
  } catch (err) {
    ElMessage.error('加载课程失败')
    router.push('/courses')
  }
})

const handleConfirmOrder = async () => {
  submitting.value = true
  try {
    // 创建课程订单
    const order = await orderApi.createCourseOrder(course.value.id)
    ElMessage.success('订单创建成功')
    // 跳转到支付页面
    router.push(`/pay/${order.id}`)
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '创建订单失败')
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.checkout-container {
  max-width: 1000px;
  margin: 0 auto;
  padding: 20px;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: 24px;
}

.checkout-content {
  display: grid;
  grid-template-columns: 1fr 360px;
  gap: 24px;
}

/* 左侧主内容 */
.checkout-main {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.section-card {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text);
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
}

/* 课程信息 */
.course-info {
  display: flex;
  gap: 16px;
}

.course-cover {
  width: 200px;
  height: 130px;
  object-fit: cover;
  border-radius: 8px;
  flex-shrink: 0;
}

.cover-placeholder {
  width: 200px;
  height: 130px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: #fff;
  border-radius: 8px;
  flex-shrink: 0;
}

.course-detail {
  flex: 1;
}

.course-name {
  font-size: 18px;
  font-weight: 600;
  margin: 0 0 8px;
  color: #333;
}

.course-artisan {
  font-size: 14px;
  color: #666;
  margin: 0 0 8px;
}

.course-meta {
  font-size: 13px;
  color: #999;
}

/* 右侧侧边栏 */
.checkout-sidebar {
  position: sticky;
  top: 20px;
  height: fit-content;
}

.price-card {
  background: white;
  border-radius: 8px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.price-card h3 {
  font-size: 18px;
  font-weight: 600;
  margin: 0 0 16px;
}

.price-row {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  font-size: 14px;
  color: #666;
}

.price-total {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  font-size: 16px;
  font-weight: 600;
}

.total-amount {
  font-size: 24px;
  color: #ff4d4f;
}

.confirm-btn {
  width: 100%;
  margin-top: 16px;
  font-size: 16px;
  font-weight: 600;
}

.tips {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 12px;
  padding: 12px;
  background: #fff7e6;
  border-radius: 8px;
  color: #fa8c16;
  font-size: 12px;
}

@media (max-width: 768px) {
  .checkout-content {
    grid-template-columns: 1fr;
  }

  .checkout-sidebar {
    position: static;
  }

  .course-info {
    flex-direction: column;
  }

  .course-cover, .cover-placeholder {
    width: 100%;
    height: 180px;
  }
}
</style>