<template>
  <MainLayout>
    <div class="container">
      <div class="page-header-card">
        <div class="header-left">
          <el-button text @click="$router.push('/artisan/courses')">
            <el-icon><ArrowLeft /></el-icon> 返回列表
          </el-button>
          <h2 class="page-title">{{ isNew ? '创建课程' : '编辑课程' }}</h2>
        </div>
        <div class="header-right">
          <el-button @click="handleSaveDraft" :loading="saving">保存草稿</el-button>
          <el-button type="primary" @click="handleSubmitReview" :loading="submitting">提交审核</el-button>
        </div>
      </div>

      <div v-loading="loading">
        <!-- 课程统计 -->
        <div class="stats-bar" v-if="courseStats">
          <div class="stat-item">
            <span class="stat-value">{{ courseStats.enrolled_count || 0 }}</span>
            <span class="stat-label">报名人数</span>
          </div>
          <div class="stat-item">
            <span class="stat-value">{{ courseStats.review_count || 0 }}</span>
            <span class="stat-label">学员评价</span>
          </div>
          <div class="stat-item">
            <span class="stat-value">{{ courseStats.total_lessons || 0 }}</span>
            <span class="stat-label">总课时数</span>
          </div>
        </div>

        <!-- 基本信息 -->
        <div class="card">
          <h3 class="section-title">基本信息</h3>
          <el-form ref="basicFormRef" :model="form" :rules="basicRules" label-width="100px" label-position="right">
            <el-form-item label="课程标题" prop="title">
              <el-input v-model="form.title" placeholder="请输入课程标题" maxlength="50" show-word-limit @blur="validateField('title')" />
            </el-form-item>
            <el-form-item label="课程分类" prop="category">
              <el-select v-model="form.category" placeholder="请选择课程分类" clearable style="width: 100%">
                <el-option v-for="cat in categories" :key="cat" :label="cat" :value="cat" />
              </el-select>
            </el-form-item>

            <!-- 难度、时长、适合人群 -->
            <el-row :gutter="16">
              <el-col :span="8">
                <el-form-item label="课程难度" prop="difficulty">
                  <el-select v-model="form.difficulty" placeholder="选择难度" clearable style="width: 100%">
                    <el-option label="入门" value="beginner" />
                    <el-option label="初级" value="elementary" />
                    <el-option label="中级" value="intermediate" />
                    <el-option label="高级" value="advanced" />
                    <el-option label="大师" value="master" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="总课时数" prop="lesson_limit">
                  <el-input-number v-model="form.lesson_limit" :min="0" :max="200" placeholder="0=不限制" style="width: 100%" />
                  <div class="form-tip">0 表示不限制课时数量</div>
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="适合人群" prop="target_audience">
                  <el-select v-model="form.target_audience" placeholder="选择人群" clearable style="width: 100%">
                    <el-option label="零基础" value="beginner" />
                    <el-option label="爱好者" value="hobbyist" />
                    <el-option label="从业者" value="professional" />
                    <el-option label="全年龄段" value="all" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>

            <!-- 课程标签 -->
            <el-form-item label="课程标签">
              <el-select v-model="form.tags" multiple placeholder="选择标签（可多选）" style="width: 100%">
                <el-option v-for="tag in tagOptions" :key="tag" :label="tag" :value="tag" />
              </el-select>
            </el-form-item>

            <!-- 课程价格 -->
            <el-form-item label="课程价格" prop="price">
              <div class="price-type-group">
                <el-radio-group v-model="isPaid" @change="onPaidChange">
                  <el-radio-button :value="false">免费</el-radio-button>
                  <el-radio-button :value="true">付费</el-radio-button>
                </el-radio-group>
              </div>
              <div v-if="isPaid" class="price-input-group" style="margin-top: 12px">
                <el-input-number v-model="form.price" :min="0.01" :precision="2" controls-position="right" style="width: 200px" />
                <span class="price-unit">元</span>
              </div>
            </el-form-item>

            <!-- 试看课时数（仅付费课程） -->
            <el-form-item v-if="isPaid" label="免费试看">
              <el-input-number v-model="form.free_preview_count" :min="0" :max="99" :precision="0" style="width: 150px" />
              <span class="price-unit">课时</span>
              <div class="form-tip">设置可免费试看的课时数量，吸引用户购买</div>
            </el-form-item>

            <!-- 课程封面 -->
            <el-form-item label="课程封面" prop="cover_image">
              <div class="cover-upload-area">
                <div v-if="form.cover_image" class="cover-preview">
                  <el-image :src="form.cover_image" fit="cover" class="cover-img" />
                  <div class="cover-overlay">
                    <el-button size="small" circle @click="showCoverPreview = true">
                      <el-icon><ZoomIn /></el-icon>
                    </el-button>
                    <el-button size="small" circle type="danger" @click="removeCover">
                      <el-icon><Delete /></el-icon>
                    </el-button>
                  </div>
                </div>
                <el-upload
                  v-else
                  :action="imageUploadUrl"
                  :headers="uploadHeaders"
                  :on-success="handleCoverSuccess"
                  :before-upload="beforeImageUpload"
                  :on-progress="handleCoverProgress"
                  :show-file-list="false"
                  accept="image/jpeg,image/png,image/webp"
                  class="cover-uploader"
                >
                  <div class="upload-placeholder">
                    <el-icon :size="32" class="upload-icon"><Plus /></el-icon>
                    <span class="upload-text">点击上传封面</span>
                    <span class="upload-tip">支持 JPG/PNG/WebP，建议 750×420px，不超过 5MB</span>
                  </div>
                </el-upload>
                <div v-if="coverUploading" class="upload-progress-bar">
                  <el-progress :percentage="coverProgress" :stroke-width="4" />
                </div>
              </div>
            </el-form-item>

            <!-- 课程简介 -->
            <el-form-item label="课程简介" prop="description">
              <div style="display: flex; gap: 8px; align-items: flex-start; width: 100%;">
                <el-input v-model="form.description" type="textarea" :rows="4" placeholder="介绍课程内容和学习目标" maxlength="500" show-word-limit style="flex: 1" @blur="validateField('description')" />
                <el-button type="primary" :loading="generatingIntro" :disabled="!form.title" @click="handleGenerateIntro" style="flex-shrink: 0; margin-top: 2px;">
                  <el-icon v-if="!generatingIntro"><MagicStick /></el-icon>
                  {{ generatingIntro ? '生成中...' : '生成文案' }}
                </el-button>
              </div>
              <div class="form-tip">简要描述课程内容，帮助用户快速了解</div>
            </el-form-item>

            <!-- 非遗技艺介绍 -->
            <el-form-item label="技艺介绍">
              <div style="display: flex; gap: 8px; align-items: flex-start; width: 100%;">
                <el-input v-model="form.craft_intro" type="textarea" :rows="4" placeholder="介绍相关非遗技艺的历史、特点和文化价值" maxlength="1000" show-word-limit style="flex: 1" />
                <el-tooltip :content="!form.description ? '请先填写课程简介' : '根据课程简介生成技艺介绍'" placement="top">
                  <el-button type="primary" :loading="generatingCraft" :disabled="!form.description" @click="handleGenerateCraft" style="flex-shrink: 0; margin-top: 2px;">
                    <el-icon v-if="!generatingCraft"><MagicStick /></el-icon>
                    {{ generatingCraft ? '生成中...' : '生成文案' }}
                  </el-button>
                </el-tooltip>
              </div>
              <div class="form-tip">详细介绍非遗技艺背景，增强课程文化底蕴</div>
            </el-form-item>

            <!-- 购买须知（仅付费课程显示） -->
            <el-form-item v-if="isPaid" label="购买须知">
              <el-input v-model="form.purchase_notice" type="textarea" :rows="3" placeholder="请输入购买须知" maxlength="500" show-word-limit />
              <div class="form-tip">默认已包含基础购买须知，可根据需要修改</div>
            </el-form-item>
          </el-form>
        </div>

        <!-- 章节与课时 -->
        <div class="card" style="margin-top: 20px">
          <div class="section-header">
            <h3 class="section-title">
              章节与课时
              <span style="font-size:13px;font-weight:400;color:#999;margin-left:8px">
                {{ totalLessonCount }}{{ form.lesson_limit > 0 ? ` / ${form.lesson_limit}` : '' }} 节
              </span>
            </h3>
            <el-button type="primary" @click="handleAddChapter">
              <el-icon><Plus /></el-icon> 添加章节
            </el-button>
          </div>

          <div v-if="!chapters.length" class="empty-chapters">
            <el-icon :size="48" class="empty-icon"><FolderOpened /></el-icon>
            <p class="empty-text">暂无章节</p>
            <p class="empty-hint">点击「添加章节」开始创建课程内容</p>
            <el-button type="primary" @click="handleAddChapter">添加章节</el-button>
          </div>

          <div v-for="(chapter, ci) in chapters" :key="chapter._key" class="chapter-block" :class="{ 'chapter-dragging': draggingChapter === ci }">
            <div class="chapter-header">
              <div class="chapter-drag-handle" @mousedown="startDragChapter(ci)">
                <el-icon><Rank /></el-icon>
              </div>
              <span class="chapter-number">{{ toChineseChapter(ci + 1) }}</span>
              <el-input v-model="chapter.title" placeholder="请输入章节标题" maxlength="50" show-word-limit style="flex: 1; max-width: 400px" />
              <div class="chapter-actions">
                <el-button size="small" :disabled="ci === 0" @click="moveChapter(ci, -1)">
                  <el-icon><Top /></el-icon>
                </el-button>
                <el-button size="small" :disabled="ci === chapters.length - 1" @click="moveChapter(ci, 1)">
                  <el-icon><Bottom /></el-icon>
                </el-button>
                <el-button size="small" type="primary" @click="handleAddLesson(chapter)">
                  <el-icon><Plus /></el-icon> 添加课时
                </el-button>
                <el-popconfirm title="删除此章节及所有课时？" @confirm="removeChapter(ci)">
                  <template #reference>
                    <el-button size="small" type="danger">
                      <el-icon><Delete /></el-icon>
                    </el-button>
                  </template>
                </el-popconfirm>
              </div>
            </div>

            <el-table v-if="chapter.lessons.length" :data="chapter.lessons" size="small" style="margin-top: 8px" row-key="_key">
              <el-table-column label="排序" width="60" align="center">
                <template #default="{ $index }">{{ $index + 1 }}</template>
              </el-table-column>
              <el-table-column label="课时标题" min-width="180">
                <template #default="{ row }">
                  <el-input v-model="row.title" size="small" placeholder="课时标题" maxlength="50" show-word-limit />
                </template>
              </el-table-column>
              <el-table-column label="视频" width="200">
                <template #default="{ row }">
                  <template v-if="row.video_url">
                    <span class="video-uploaded">
                      <el-icon><VideoCamera /></el-icon> 已上传
                    </span>
                    <el-button size="small" text type="primary" @click="showVideoDialog(row)">预览</el-button>
                    <el-button size="small" text type="danger" @click="row.video_url = ''">删除</el-button>
                  </template>
                  <el-upload
                    v-else
                    :action="videoUploadUrl"
                    :headers="uploadHeaders"
                    :on-success="(res) => handleVideoSuccess(row, res)"
                    :before-upload="beforeVideoUpload"
                    :on-progress="(evt) => handleVideoProgress(row, evt)"
                    :show-file-list="false"
                    accept="video/mp4,video/webm,video/ogg"
                  >
                    <el-button size="small">
                      <el-icon><Upload /></el-icon> 上传视频
                    </el-button>
                  </el-upload>
                  <div v-if="row._uploading" class="video-progress">
                    <el-progress :percentage="row._progress || 0" :stroke-width="3" />
                  </div>
                </template>
              </el-table-column>
              <el-table-column label="试看" width="80" align="center">
                <template #default="{ row }">
                  <el-tooltip :content="row.is_free ? '免费试看' : '付费可见'" placement="top">
                    <el-switch
                      v-model="row.is_free"
                      size="small"
                      @change="onFreeToggle(row)"
                    />
                  </el-tooltip>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="80" align="center">
                <template #default="{ row, $index }">
                  <el-popconfirm title="删除此时课？" @confirm="removeLesson(chapter, $index)">
                    <template #reference>
                      <el-button size="small" type="danger" text>
                        <el-icon><Delete /></el-icon>
                      </el-button>
                    </template>
                  </el-popconfirm>
                </template>
              </el-table-column>
            </el-table>

            <div v-else class="empty-lessons">
              <el-icon :size="24"><VideoPlay /></el-icon>
              <span>暂无课时，点击「添加课时」开始</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 封面预览弹窗 -->
      <el-dialog v-model="showCoverPreview" title="封面预览" width="500px" :show-close="true">
        <el-image :src="form.cover_image" fit="contain" style="width: 100%; border-radius: 8px" />
      </el-dialog>

      <!-- 视频预览弹窗 -->
      <el-dialog v-model="previewVisible" title="视频预览" width="700px">
        <video v-if="previewUrl" :src="previewUrl" controls style="width: 100%; border-radius: 8px" />
      </el-dialog>
    </div>
  </MainLayout>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import MainLayout from '@/components/MainLayout.vue'
import { courseApi, workflowApi } from '@/api/modules'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'
import {
  ArrowLeft, Plus, Delete, ZoomIn, FolderOpened, Rank,
  Top, Bottom, VideoCamera, Upload, VideoPlay, MagicStick
} from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const isNew = computed(() => !route.params.id || route.params.id === 'new')

const isPaid = ref(false)
const onPaidChange = (val) => {
  if (!val) {
    form.price = 0
    form.purchase_notice = ''
  } else {
    form.purchase_notice = form.purchase_notice || '1、本课程为付费内容，购买后永久观看\n2、支付完成后自动开通学习权限\n3、一经购买不退不换'
  }
}

const loading = ref(false)
const saving = ref(false)
const submitting = ref(false)
const categories = ['陶瓷', '刺绣', '木雕', '剪纸', '金属工艺', '布艺', '漆艺', '其他']
const tagOptions = ['非遗传承', '手工制作', '传统文化', '入门教程', '进阶提升', '大师课程', '亲子互动', '文化体验']

const form = reactive({
  title: '', description: '', category: '', price: 0, cover_image: '',
  difficulty: '', duration_hours: 0, lesson_limit: 0, target_audience: '', tags: [],
  free_preview_count: 0, craft_intro: '', purchase_notice: '',
})

const chapters = ref([])
let chapterCounter = 0
const courseStats = ref(null)

// 文案生成 (LangGraph 工作流: content_type=course_intro → 同时输出 result(文案) + tech_intro(技艺介绍))
const generatingIntro = ref(false)
const generatingCraft = ref(false)

const handleGenerateIntro = async () => {
  if (!form.title) {
    ElMessage.warning('请先输入课程标题')
    return
  }
  // 商家输入为必填: 已有简介则润色, 否则用课程标题作为关键词走生成
  const userInput = (form.description || '').trim() || form.title.trim()
  generatingIntro.value = true
  try {
    const res = await workflowApi.generateCopy(
      'course_intro',         // content_type
      form.title,             // title → 课程标题
      userInput,              // user_input → 商家输入(必填)
    )
    // 填充课程简介
    if (res.result) {
      form.description = res.result
      ElMessage.success('课程简介已生成')
    }
    // 同时填充技艺介绍 (工作流自动根据课程简介生成)
    if (res.tech_intro) {
      form.craft_intro = res.tech_intro
    }
    if (!res.result && !res.tech_intro) {
      ElMessage.warning('生成结果为空，请重试')
    }
  } catch (err) {
    ElMessage.error(err.detail || err.response?.data?.detail || '文案生成失败，请稍后重试')
  } finally {
    generatingIntro.value = false
  }
}

const handleGenerateCraft = async () => {
  if (!form.description) {
    ElMessage.warning('请先填写课程简介')
    return
  }
  generatingCraft.value = true
  try {
    // 传入已有的课程简介 → >20字走润色分支, 工作流同时输出技艺介绍
    const res = await workflowApi.generateCopy(
      'course_intro',         // content_type
      form.title,             // title → 课程标题
      form.description,       // user_input → 商家已填的简介(必填, >20字走润色)
    )
    // 只提取技艺介绍 (课程简介已有, 不覆盖)
    if (res.tech_intro) {
      form.craft_intro = res.tech_intro
      ElMessage.success('技艺介绍已生成')
    } else {
      ElMessage.warning('技艺介绍生成结果为空，请重试')
    }
  } catch (err) {
    ElMessage.error(err.detail || err.response?.data?.detail || '文案生成失败，请稍后重试')
  } finally {
    generatingCraft.value = false
  }
}

// 免费试看：整个课程只能开启一个课时
const onFreeToggle = (toggled) => {
  if (toggled.is_free) {
    chapters.value.forEach(ch => {
      ch.lessons.forEach(l => {
        if (l._key !== toggled._key) l.is_free = false
      })
    })
  }
}

const CHINESE_NUMS = ['零', '一', '二', '三', '四', '五', '六', '七', '八', '九', '十',
  '十一', '十二', '十三', '十四', '十五', '十六', '十七', '十八', '十九', '二十']
const toChineseChapter = (num) => {
  if (!num || num < 1) return '第?章'
  if (num <= 20) return `第${CHINESE_NUMS[num]}章`
  return `第${num}章`
}

const previewVisible = ref(false)
const previewUrl = ref('')
const showCoverPreview = ref(false)

// 封面上传
const coverUploading = ref(false)
const coverProgress = ref(0)

const videoUploadUrl = '/api/upload/video'
const imageUploadUrl = '/api/upload/image'
const uploadHeaders = computed(() => ({
  Authorization: `Bearer ${userStore.token}`,
}))

// 表单校验规则
const basicFormRef = ref()
const basicRules = {
  title: [
    { required: true, message: '请输入课程标题', trigger: 'blur' },
    { min: 2, max: 50, message: '标题长度 2-50 个字符', trigger: 'blur' },
  ],
  category: [
    { required: true, message: '请选择课程分类', trigger: 'change' },
  ],
  price: [
    { required: true, message: '请设置课程价格', trigger: 'blur' },
  ],
  cover_image: [
    { required: true, message: '请上传课程封面', trigger: 'change' },
  ],
  description: [
    { required: true, message: '请输入课程简介', trigger: 'blur' },
    { min: 10, max: 500, message: '简介长度 10-500 个字符', trigger: 'blur' },
  ],
}

// 实时失焦校验
const validateField = (field) => {
  basicFormRef.value?.validateField(field)
}

// 敏感词过滤（简单实现）
const sensitiveWords = ['违法', '暴力', '色情', '赌博', '毒品', '政治敏感']
const checkSensitiveWords = (text) => {
  if (!text) return true
  for (const word of sensitiveWords) {
    if (text.includes(word)) return false
  }
  return true
}

onMounted(async () => {
  if (isNew.value) {
    loading.value = false
    return
  }
  loading.value = true
  try {
    const course = await courseApi.getCourse(route.params.id)
    form.title = course.title || ''
    form.description = course.description || ''
    form.category = course.category || ''
    form.price = parseFloat(course.price) || 0
    isPaid.value = (parseFloat(course.price) || 0) > 0
    form.cover_image = course.cover_image || ''
    form.difficulty = course.difficulty || ''
    form.duration_hours = course.duration_hours || 0
    form.lesson_limit = course.lesson_limit || 0
    form.target_audience = course.target_audience || ''
    form.tags = (() => {
      const raw = course.tags
      if (!raw) return []
      if (Array.isArray(raw)) return raw
      if (typeof raw === 'string') {
        try { const p = JSON.parse(raw); return Array.isArray(p) ? p : []; } catch (_) { return []; }
      }
      return []
    })()
    form.free_preview_count = course.free_preview_count || 0
    form.craft_intro = course.craft_intro || ''
    // 付费课程：购买须知默认"一经购买不退不换"；免费课程：清空
    form.purchase_notice = course.purchase_notice || (isPaid.value ? '1、本课程为付费内容，购买后永久观看\n2、支付完成后自动开通学习权限\n3、一经购买不退不换' : '')

    chapters.value = (course.chapters || []).map(ch => ({
      ...ch,
      _key: chapterCounter++,
      lessons: (ch.lessons || []).map(l => ({ ...l, _key: chapterCounter++ })),
    }))

    // 统计信息
    courseStats.value = {
      enrolled_count: course.enrolled_count || 0,
      review_count: course.review_count || 0,
      total_lessons: chapters.value.reduce((sum, ch) => sum + (ch.lessons?.length || 0), 0),
    }
  } catch (err) {
    ElMessage.error('加载课程失败')
  } finally {
    loading.value = false
  }
})

// 封面上传
const handleCoverSuccess = (res) => {
  form.cover_image = res.url
  coverUploading.value = false
  coverProgress.value = 0
  ElMessage.success('封面上传成功')
  basicFormRef.value?.validateField('cover_image')
}

const handleCoverProgress = (evt) => {
  coverUploading.value = true
  coverProgress.value = Math.round(evt.percent)
}

const removeCover = () => {
  form.cover_image = ''
  ElMessage.info('已移除封面')
}

const beforeImageUpload = (file) => {
  const allowedTypes = ['image/jpeg', 'image/png', 'image/webp']
  if (!allowedTypes.includes(file.type)) {
    ElMessage.error('仅支持 JPG/PNG/WebP 格式')
    return false
  }
  if (file.size > 5 * 1024 * 1024) {
    ElMessage.error('图片大小不能超过 5MB')
    return false
  }
  return true
}

// 视频上传
const handleVideoSuccess = (row, res) => {
  row.video_url = res.url
  row._uploading = false
  row._progress = 0
  ElMessage.success('视频上传成功')
}

const handleVideoProgress = (row, evt) => {
  row._uploading = true
  row._progress = Math.round(evt.percent)
}

const beforeVideoUpload = (file) => {
  const allowedTypes = ['video/mp4', 'video/webm', 'video/ogg']
  if (!allowedTypes.includes(file.type)) {
    ElMessage.error('仅支持 MP4/WebM/OGG 格式')
    return false
  }
  if (file.size > 500 * 1024 * 1024) {
    ElMessage.error('视频不能超过 500MB')
    return false
  }
  return true
}

const showVideoDialog = (row) => {
  previewUrl.value = row.video_url
  previewVisible.value = true
}

// 章节操作
const handleAddChapter = () => {
  chapters.value.push({ _key: chapterCounter++, title: '', lessons: [] })
}

const removeChapter = (index) => { chapters.value.splice(index, 1) }

const moveChapter = (index, delta) => {
  const newIndex = index + delta
  if (newIndex < 0 || newIndex >= chapters.value.length) return
  const tmp = chapters.value[index]
  chapters.value[index] = chapters.value[newIndex]
  chapters.value[newIndex] = tmp
}

// 拖拽排序
const draggingChapter = ref(-1)
const startDragChapter = (index) => {
  draggingChapter.value = index
  const onMove = (e) => {
    const blocks = document.querySelectorAll('.chapter-block')
    blocks.forEach((block, i) => {
      const rect = block.getBoundingClientRect()
      if (e.clientY > rect.top && e.clientY < rect.bottom && i !== draggingChapter.value) {
        const tmp = chapters.value[draggingChapter.value]
        chapters.value.splice(draggingChapter.value, 1)
        chapters.value.splice(i, 0, tmp)
        draggingChapter.value = i
      }
    })
  }
  const onUp = () => {
    draggingChapter.value = -1
    document.removeEventListener('mousemove', onMove)
    document.removeEventListener('mouseup', onUp)
  }
  document.addEventListener('mousemove', onMove)
  document.addEventListener('mouseup', onUp)
}

// 总课时数(计算值)
const totalLessonCount = computed(() =>
  chapters.value.reduce((sum, ch) => sum + (ch.lessons?.length || 0), 0)
)

// 课时操作
const handleAddLesson = (chapter) => {
  // 检查课时上限
  if (form.lesson_limit > 0 && totalLessonCount.value >= form.lesson_limit) {
    ElMessage.warning(`总课时数已达上限 (${form.lesson_limit} 节)`)
    return
  }
  chapter.lessons.push({
    _key: chapterCounter++, title: '', description: '',
    video_url: '', duration: 0, is_free: false,
    sort_order: chapter.lessons.length,
  })
}

const removeLesson = (chapter, index) => { chapter.lessons.splice(index, 1) }

// 保存课程数据
const buildCourseData = () => ({
  title: form.title,
  description: form.description,
  category: form.category,
  price: form.price,
  cover_image: form.cover_image,
  difficulty: form.difficulty,
  duration_hours: form.duration_hours,
  lesson_limit: form.lesson_limit,
  target_audience: form.target_audience,
  tags: form.tags,
  free_preview_count: form.free_preview_count,
  craft_intro: form.craft_intro,
  purchase_notice: form.purchase_notice,
})

// 保存草稿
const handleSaveDraft = async () => {
  saving.value = true
  try {
    await saveCourseData('draft')
    ElMessage.success('草稿已保存')
    router.push('/artisan/courses')
  } catch (err) {
    ElMessage.error(err.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

// 提交审核
const handleSubmitReview = async () => {
  // 校验基本信息
  try {
    await basicFormRef.value.validate()
  } catch {
    ElMessage.warning('请完善必填信息')
    return
  }

  // 校验章节课时
  if (!chapters.value.length) {
    ElMessage.warning('请至少添加一个章节')
    return
  }
  const hasLesson = chapters.value.some(ch => ch.lessons.length > 0)
  if (!hasLesson) {
    ElMessage.warning('请至少添加一个课时')
    return
  }

  // 敏感词检查
  const allText = [form.title, form.description, form.craft_intro, form.purchase_notice].join('')
  if (!checkSensitiveWords(allText)) {
    ElMessage.warning('内容包含敏感词，请修改后重新提交')
    return
  }

  submitting.value = true
  try {
    await saveCourseData('pending')
    ElMessage.success('已提交审核，等待平台审核通过')
    router.push('/artisan/courses')
  } catch (err) {
    ElMessage.error(err.detail || '提交失败')
  } finally {
    submitting.value = false
  }
}

// 实际保存逻辑
const saveCourseData = async (status) => {
  let courseId = route.params.id

  if (isNew.value) {
    // 新建课程：先创建，再保存章节
    const newCourse = await courseApi.createCourse({
      ...buildCourseData(),
      status,
    })
    courseId = newCourse.id
    ElMessage.success('课程已创建')
  } else {
    // 编辑已有课程：更新基本信息
    await courseApi.updateCourse(courseId, {
      ...buildCourseData(),
      status,
    })
  }

  // 删除旧章节（仅编辑已有课程时）
  if (!isNew.value) {
    const existingCourse = await courseApi.getCourse(courseId)
    for (const ch of existingCourse.chapters || []) {
      await courseApi.deleteChapter(courseId, ch.id)
    }
  }

  // 创建新章节和课时
  for (let ci = 0; ci < chapters.value.length; ci++) {
    const ch = chapters.value[ci]
    const newChapter = await courseApi.addChapter(courseId, {
      title: ch.title || `第一章`,
      sort_order: ci,
    })
    for (let li = 0; li < ch.lessons.length; li++) {
      const lesson = ch.lessons[li]
      await courseApi.addLesson(courseId, newChapter.id, {
        title: lesson.title || `课时${li + 1}`,
        description: lesson.description || '',
        video_url: lesson.video_url || '',
        duration: lesson.duration || 0,
        sort_order: li,
        is_free: lesson.is_free || false,
      })
    }
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
.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}
.page-title { margin: 0; font-size: 20px; }
.header-right { display: flex; gap: 8px; }

/* 统计栏 */
.stats-bar {
  display: flex;
  gap: 24px;
  margin-bottom: 20px;
  padding: 16px 24px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}
.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: #3B4F6B;
}
.stat-label {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}

.section-title {
  margin: 0 0 20px;
  font-size: 16px;
  font-weight: 600;
  color: #333;
  padding-bottom: 12px;
  border-bottom: 1px solid #eee;
}

.form-tip {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}

.price-type-group {
  margin-bottom: 4px;
}

.price-input-group {
  display: flex;
  align-items: center;
}
.price-unit {
  margin-left: 8px;
  color: #666;
  font-size: 14px;
}

/* 封面上传 */
.cover-upload-area {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.cover-preview {
  position: relative;
  width: 300px;
  height: 168px;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #eee;
}
.cover-img {
  width: 100%;
  height: 100%;
}
.cover-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  opacity: 0;
  transition: opacity 0.2s;
}
.cover-preview:hover .cover-overlay {
  opacity: 1;
}
.upload-placeholder {
  width: 300px;
  height: 168px;
  border: 2px dashed #d9d9d9;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: border-color 0.2s;
}
.upload-placeholder:hover {
  border-color: #3B4F6B;
}
.upload-icon { color: #ccc; margin-bottom: 8px; }
.upload-text { font-size: 14px; color: #666; }
.upload-tip { font-size: 12px; color: #999; margin-top: 4px; }
.upload-progress-bar { width: 300px; }

/* 章节空状态 */
.empty-chapters {
  text-align: center;
  padding: 48px 0;
  color: #999;
}
.empty-icon { color: #ddd; margin-bottom: 12px; }
.empty-text { font-size: 16px; margin: 8px 0 4px; color: #666; }
.empty-hint { font-size: 13px; margin-bottom: 16px; }

/* 课时空状态 */
.empty-lessons {
  text-align: center;
  padding: 20px;
  color: #ccc;
  font-size: 13px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.chapter-block {
  background: #fafafa;
  border: 1px solid #eee;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  transition: box-shadow 0.2s;
}
.chapter-block.chapter-dragging {
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}
.chapter-header {
  display: flex;
  align-items: center;
  gap: 12px;
}
.chapter-drag-handle {
  cursor: grab;
  color: #ccc;
  padding: 4px;
  display: flex;
  align-items: center;
}
.chapter-drag-handle:active { cursor: grabbing; }
.chapter-number {
  font-size: 13px;
  color: #999;
  white-space: nowrap;
}
.chapter-actions {
  display: flex;
  gap: 4px;
  flex-shrink: 0;
}

.video-uploaded {
  color: #67c23a;
  font-size: 12px;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
.video-progress {
  margin-top: 4px;
}
</style>
