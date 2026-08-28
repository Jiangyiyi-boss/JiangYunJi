<template>
  <div>
    <h3 style="margin:0 0 16px">课程审核</h3>

    <!-- 状态筛选 -->
    <div class="filter-bar" style="margin-bottom:16px">
      <el-radio-group v-model="filterStatus" size="small" @change="load">
        <el-radio-button value="pending">待审核</el-radio-button>
        <el-radio-button value="published">已通过</el-radio-button>
        <el-radio-button value="rejected">已驳回</el-radio-button>
        <el-radio-button value="">全部</el-radio-button>
      </el-radio-group>
    </div>

    <div class="card" v-loading="loading">
      <el-empty v-if="!courses.length" description="暂无课程" />
      <el-table v-else :data="courses" style="width:100%">
        <el-table-column label="封面" width="70">
          <template #default="{row}">
            <el-image v-if="row.cover_image" :src="row.cover_image" fit="cover" style="width:48px;height:36px;border-radius:4px" />
            <span v-else style="color:#ccc">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="title" label="标题" min-width="160" show-overflow-tooltip />
        <el-table-column prop="artisan_name" label="匠人" width="100" />
        <el-table-column prop="category" label="分类" width="80" />
        <el-table-column label="价格" width="80">
          <template #default="{row}">¥{{ row.price }}</template>
        </el-table-column>
        <el-table-column label="审核状态" width="100">
          <template #default="{row}">
            <el-tag :type="statusTag(row.status)" size="small">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="驳回原因" min-width="120" show-overflow-tooltip>
          <template #default="{row}">{{ row.reject_reason || '-' }}</template>
        </el-table-column>
        <el-table-column prop="created_at" label="提交时间" width="110">
          <template #default="{row}">{{ row.created_at?.slice(0,10) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{row}">
            <el-button size="small" @click="showDetail(row)">详情</el-button>
            <template v-if="row.status === 'pending'">
              <el-button type="success" size="small" @click="handleApprove(row)">通过</el-button>
              <el-button type="danger" size="small" @click="openReject(row)">驳回</el-button>
            </template>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 详情弹窗 -->
    <el-dialog v-model="detailVisible" title="课程详情" width="700px">
      <div v-if="detail" v-loading="detailLoading">
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="标题" :span="2">{{ detail.title }}</el-descriptions-item>
          <el-descriptions-item label="分类">{{ detail.category }}</el-descriptions-item>
          <el-descriptions-item label="价格">¥{{ detail.price }}</el-descriptions-item>
          <el-descriptions-item label="难度">{{ difficultyLabel(detail.difficulty) }}</el-descriptions-item>
          <el-descriptions-item label="课时">{{ totalLessons }} 课时</el-descriptions-item>
          <el-descriptions-item label="目标人群">{{ audienceLabel(detail.target_audience) }}</el-descriptions-item>
          <el-descriptions-item v-if="detail.price > 0" label="免费试看">{{ detail.free_preview_count || 0 }}课时</el-descriptions-item>
          <el-descriptions-item label="标签" :span="2">{{ (detail.tags||[]).join('、') || '-' }}</el-descriptions-item>
          <el-descriptions-item label="匠人">{{ detail.artisan_name || '-' }}</el-descriptions-item>
          <el-descriptions-item label="提交时间">{{ detail.created_at?.slice(0,10) || '-' }}</el-descriptions-item>
          <el-descriptions-item label="简介" :span="2">{{ detail.description || '-' }}</el-descriptions-item>
          <el-descriptions-item label="技艺介绍" :span="2">{{ detail.craft_intro || '-' }}</el-descriptions-item>
          <el-descriptions-item label="购买须知" :span="2">{{ detail.purchase_notice || '-' }}</el-descriptions-item>
          <template v-if="detail.material_type && detail.material_type !== 'none'">
            <el-descriptions-item label="配套材料">{{ detail.material_type || '-' }}</el-descriptions-item>
            <el-descriptions-item label="材料价格">{{ detail.material_price > 0 ? '¥' + detail.material_price : '免费' }}</el-descriptions-item>
            <el-descriptions-item v-if="detail.material_desc" label="材料说明" :span="2">{{ detail.material_desc }}</el-descriptions-item>
          </template>
          <el-descriptions-item label="封面" :span="2">
            <el-image v-if="detail.cover_image" :src="detail.cover_image" fit="cover" style="max-width:200px;border-radius:4px" />
            <span v-else>-</span>
          </el-descriptions-item>
        </el-descriptions>

        <!-- 章节与课时 -->
        <h4 style="margin:16px 0 8px">课程大纲</h4>
        <div v-if="!detail.chapters?.length" style="color:#999">暂无章节</div>
          <div v-for="ch in detail.chapters" :key="ch.id" style="margin-bottom:12px">
            <div style="font-weight:600;margin-bottom:4px">{{ toChineseChapter((ch.sort_order ?? 0) + 1) }} {{ ch.title }}</div>
            <div v-if="!ch.lessons?.length" style="color:#ccc;font-size:13px;padding-left:12px">暂无课时</div>
            <div v-for="le in ch.lessons" :key="le.id" style="font-size:13px;padding-left:12px;color:#666;line-height:1.8;display:flex;align-items:center;gap:12px">
              <span style="flex:1">
                <span style="color:#4f6ef7;font-weight:500">{{ (ch.sort_order ?? 0) + 1 }}.{{ (le.sort_order ?? 0) + 1 }}</span> {{ le.title }}
                <el-tag v-if="le.is_free" size="small" type="success">免费</el-tag>
                <span style="color:#999"> · {{ formatDuration(le.duration) }}</span>
              </span>
              <el-button v-if="le.video_url" size="small" type="primary" text @click="openVideo(le.video_url)">
                <el-icon><VideoPlay /></el-icon> 预览
              </el-button>
              <span v-else style="color:#ccc;font-size:12px">未上传视频</span>
            </div>
          </div>
      </div>
    </el-dialog>

    <!-- 视频预览弹窗 -->
    <el-dialog v-model="videoVisible" title="课时视频预览" width="700px">
      <video v-if="videoUrl" :src="videoUrl" controls style="width:100%;border-radius:8px" />
      <div v-else style="text-align:center;color:#999;padding:40px">无视频</div>
    </el-dialog>

    <!-- 驳回弹窗 -->
    <el-dialog v-model="rejectVisible" title="驳回课程" width="450px">
      <el-form :model="rejectForm" :rules="rejectRules" ref="rejectFormRef">
        <el-form-item label="驳回原因" prop="reason">
          <el-input v-model="rejectForm.reason" type="textarea" :rows="3" placeholder="请填写驳回原因，商家将看到此信息" maxlength="500" show-word-limit />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="rejectVisible=false">取消</el-button>
        <el-button type="danger" :loading="rejecting" @click="handleReject">确认驳回</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { courseApi } from '@/api/modules'
import { ElMessage, ElMessageBox } from 'element-plus'
import { VideoPlay } from '@element-plus/icons-vue'

const courses = ref([])
const loading = ref(false)
const filterStatus = ref('pending')
const detailVisible = ref(false)
const detail = ref(null)
const detailLoading = ref(false)
const rejectVisible = ref(false)
const rejectForm = ref({ reason: '' })
const rejectFormRef = ref()
const rejectCourseId = ref(null)
const rejecting = ref(false)
const videoVisible = ref(false)
const videoUrl = ref('')

const CHINESE_NUMS = ['零', '一', '二', '三', '四', '五', '六', '七', '八', '九', '十',
  '十一', '十二', '十三', '十四', '十五', '十六', '十七', '十八', '十九', '二十']
const toChineseChapter = (num) => {
  if (!num || num < 1) return '第?章'
  if (num <= 20) return `第${CHINESE_NUMS[num]}章`
  return `第${num}章`
}

const formatDuration = (seconds) => {
  if (!seconds || seconds <= 0) return '-'
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  if (m === 0) return `${s}秒`
  if (s === 0) return `${m}分钟`
  return `${m}分${s}秒`
}

// 总课时数：优先使用商家设置的上限，否则按实际课时数统计
const totalLessons = computed(() => {
  if (detail.value?.lesson_limit > 0) return detail.value.lesson_limit
  if (!detail.value?.chapters) return 0
  return detail.value.chapters.reduce((sum, ch) => sum + (ch.lessons?.length || 0), 0)
})

const difficultyLabel = (d) => ({ beginner: '入门', elementary: '初级', intermediate: '中级', advanced: '高级', master: '大师' }[d] || d || '-')
const audienceLabel = (a) => ({ beginner: '零基础', hobbyist: '爱好者', professional: '从业者', all: '全年龄段' }[a] || a || '-')

const statusTag = (s) => ({ pending:'warning', published:'success', rejected:'danger', draft:'info' }[s]||'')
const statusLabel = (s) => ({ pending:'待审核', published:'已通过', rejected:'已驳回', draft:'草稿' }[s]||s)

const rejectRules = { reason: [{ required: true, message: '请填写驳回原因', trigger: 'blur' }] }

const load = async () => {
  loading.value = true
  try {
    const params = { limit: 100 }
    if (filterStatus.value) params.status = filterStatus.value
    const res = await courseApi.getAdminCourses(params)
    courses.value = res.items || []
  } catch(err) { console.error(err) }
  finally { loading.value = false }
}

const showDetail = async (row) => {
  detailVisible.value = true
  detailLoading.value = true
  try {
    detail.value = await courseApi.getAdminCourseDetail(row.id)
  } catch(err) { console.error(err) }
  finally { detailLoading.value = false }
}

const openVideo = (url) => {
  videoUrl.value = url
  videoVisible.value = true
}

const handleApprove = async (row) => {
  try {
    await ElMessageBox.confirm(`确定通过「${row.title}」？`, '审核通过', { type:'success' })
    await courseApi.approveCourse(row.id)
    ElMessage.success('已通过')
    load()
  } catch(err) { if (err!=='cancel') ElMessage.error('操作失败') }
}

const openReject = (row) => {
  rejectCourseId.value = row.id
  rejectForm.value.reason = ''
  rejectVisible.value = true
}

const handleReject = async () => {
  try { await rejectFormRef.value.validate() } catch { return }
  rejecting.value = true
  try {
    await courseApi.rejectCourse(rejectCourseId.value, rejectForm.value.reason)
    ElMessage.success('已驳回')
    rejectVisible.value = false
    load()
  } catch(err) { ElMessage.error(err.detail||'操作失败') }
  finally { rejecting.value = false }
}

onMounted(load)
</script>
