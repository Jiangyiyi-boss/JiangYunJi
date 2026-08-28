<template>
  <div class="learn-page">
    <!-- Top Header Bar -->
    <div class="learn-header">
      <div class="container">
        <el-button text @click="$router.push(`/course/${courseId}`)">
          <el-icon><ArrowLeft /></el-icon> 返回课程
        </el-button>
        <h2>{{ course?.title }}</h2>
        <span class="progress-text">学习进度 {{ course?.progress || 0 }}%</span>
        <router-link to="/notifications" class="msg-link">
          <el-badge :value="unreadCount" :hidden="unreadCount === 0" :max="99">
            <el-icon :size="18"><Bell /></el-icon>
          </el-badge>
        </router-link>
      </div>
    </div>

    <!-- ===== State 1: No lesson selected → full-width catalog ===== -->
    <div v-if="!activeLesson" class="container learn-body-single">
      <div class="catalog-full card">
        <h3 class="catalog-title">课程目录</h3>
        <div v-if="!chapters?.length" class="empty-tab">
          <el-empty description="暂无章节" />
        </div>
        <div v-else class="catalog-scroll-full">
          <div v-for="(ch, ci) in chapters" :key="ch.id" class="chapter-group">
            <div class="chapter-header">
              <span class="chapter-label">{{ toChineseChapter(ci + 1) }}</span>
              <span class="chapter-name">{{ ch.title }}</span>
              <span class="chapter-count">{{ ch.lessons?.length || 0 }}课时</span>
            </div>
            <div class="lesson-items">
              <div
                v-for="(le, li) in ch.lessons" :key="le.id"
                :class="['lesson-row', { locked: !isOwner && !enrolled && !isLessonFree(le) && course.price > 0 }]"
                @click="selectLesson(le)"
              >
                <div class="lesson-info">
                  <el-icon v-if="!isOwner && !enrolled && !isLessonFree(le) && course.price > 0" color="#ccc" :size="16"><Lock /></el-icon>
                  <el-icon v-else color="#999" :size="16"><VideoPlay /></el-icon>
                  <span class="lesson-number">{{ ci + 1 }}.{{ li + 1 }}</span>
                  <span class="lesson-name">{{ le.title }}</span>
                  <el-tag v-if="le.is_free" size="small" type="success">免费</el-tag>
                </div>
                <span class="lesson-meta">{{ le.duration }}分钟</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ===== State 2: Lesson selected → video + tabs ===== -->
    <div v-else class="container learn-body">
      <!-- Left: Video Player -->
      <div class="video-section card">
        <h3 class="video-title">{{ activeLesson.title }}</h3>
        <p v-if="activeLesson.description" class="lesson-desc">{{ activeLesson.description }}</p>
        <video
          v-if="activeLesson.video_url"
          :src="activeLesson.video_url"
          controls
          class="video-player"
          @ended="handleLessonComplete"
        />
        <div v-else class="no-video">
          <el-icon :size="48"><VideoCamera /></el-icon>
          <p>暂无视频内容</p>
        </div>
      </div>

      <!-- Right: Tabs Panel (目录 / 评论 / 笔记) -->
      <div class="tabs-section card">
        <el-tabs v-model="activeTab" @tab-change="onTabChange" class="tabs-full-height">
          <el-tab-pane label="课程目录" name="catalog">
            <div v-if="!chapters?.length" class="empty-tab">
              <el-empty description="暂无章节" />
            </div>
            <div v-else class="catalog-list">
              <div v-for="(ch, ci) in chapters" :key="ch.id" class="chapter-group">
                <div class="chapter-header">
                  <span class="chapter-label">{{ toChineseChapter(ci + 1) }}</span>
                  <span class="chapter-name">{{ ch.title }}</span>
                  <span class="chapter-count">{{ ch.lessons?.length || 0 }}课时</span>
                </div>
                <div class="lesson-items">
                  <div
                    v-for="(le, li) in ch.lessons" :key="le.id"
                    :class="['lesson-row', { active: activeLesson?.id === le.id, locked: !isOwner && !enrolled && !isLessonFree(le) && course.price > 0 }]"
                    @click="selectLesson(le)"
                  >
                    <div class="lesson-info">
                      <el-icon v-if="activeLesson?.id === le.id" color="#4f6ef7" :size="16"><VideoPlay /></el-icon>
                      <el-icon v-else-if="!isOwner && !enrolled && !isLessonFree(le) && course.price > 0" color="#ccc" :size="16"><Lock /></el-icon>
                      <el-icon v-else color="#999" :size="16"><VideoPlay /></el-icon>
                      <span class="lesson-number">{{ ci + 1 }}.{{ li + 1 }}</span>
                      <span class="lesson-name">{{ le.title }}</span>
                      <el-tag v-if="le.is_free" size="small" type="success">免费</el-tag>
                    </div>
                    <span class="lesson-meta">{{ le.duration }}分钟</span>
                  </div>
                </div>
              </div>
            </div>
          </el-tab-pane>

          <el-tab-pane label="课程评论" name="comments">
            <div class="tab-content-scroll">
              <div v-if="enrolled || isOwner" class="comment-input">
                <el-input v-model="newComment" type="textarea" :rows="3" placeholder="分享你的学习心得..." maxlength="500" show-word-limit />
                <el-button type="primary" @click="submitComment" :loading="submitting">发布评论</el-button>
              </div>
              <div v-else class="comment-hint">
                <el-alert type="info" :closable="false">请先加入或购买课程后参与评论</el-alert>
              </div>
              <div v-loading="commentsLoading" class="comment-list">
                <el-empty v-if="!commentTree.length && !commentsLoading" description="暂无评论，来发表第一条评论吧" />
                <div v-for="c in commentTree" :key="c.id" :id="`comment-${c.id}`" :class="['comment-item', { highlighted: highlightedCommentId === c.id }]">
                  <!-- 一级评论 -->
                  <div class="comment-main">
                    <div class="comment-author" @click="goToUser(c.user)">
                      <el-avatar :size="32" :src="c.user?.avatar">
                        {{ (c.user?.nickname || c.user?.username || 'U')[0] }}
                      </el-avatar>
                      <span class="comment-name">{{ c.user?.nickname || c.user?.username || '匿名用户' }}</span>
                      <span v-if="c.user?.id === course?.artisan_user_id" class="artisan-badge">匠人</span>
                    </div>
                    <div class="comment-body">
                      <p class="comment-text">{{ c.content }}</p>
                      <div class="comment-footer">
                        <span class="comment-time">{{ formatTime(c.created_at) }}</span>
                        <div class="comment-actions-right">
                          <el-button text size="small" @click="showReplyInput(c)">
                            <el-icon><ChatDotRound /></el-icon> 回复
                          </el-button>
                        </div>
                      </div>
                    </div>
                  </div>
                  <!-- 回复输入框 -->
                  <div v-if="replyingTo === c.id && (enrolled || isOwner)" class="reply-input-inline">
                    <el-input v-model="replyContent" type="textarea" :rows="2" :placeholder="`回复 ${c.user?.nickname || c.user?.username || '用户'}...`" maxlength="300" show-word-limit />
                    <div class="reply-actions">
                      <el-button size="small" @click="replyingTo = null">取消</el-button>
                      <el-button type="primary" size="small" @click="submitReply(c.id)" :loading="submitting">回复</el-button>
                    </div>
                  </div>
                  <!-- 二级回复列表 -->
                  <div v-if="c.children?.length" class="reply-section">
                    <div
                      v-for="r in (expandedComments[c.id] ? c.children : c.children.slice(0, 3))"
                      :key="r.id"
                      :id="`comment-${r.id}`"
                      :class="['reply-item', { highlighted: highlightedCommentId === r.id }]"
                    >
                      <div class="reply-author" @click="goToUser(r.user)">
                        <el-avatar :size="24" :src="r.user?.avatar">
                          {{ (r.user?.nickname || r.user?.username || 'U')[0] }}
                        </el-avatar>
                        <span class="reply-name">{{ r.user?.nickname || r.user?.username || '匿名用户' }}</span>
                      </div>
                      <div class="reply-body">
                        <div class="reply-to-line" v-if="r.parent_user">
                          <span class="reply-to-text">回复</span>
                          <span class="reply-parent-name" @click.stop="goToUser(r.parent_user)">@{{ r.parent_user?.nickname || r.parent_user?.username || '用户' }}</span>
                        </div>
                        <p class="reply-text">{{ r.content }}</p>
                        <div class="reply-footer">
                          <span class="reply-time">{{ formatTime(r.created_at) }}</span>
                          <div class="reply-actions-right">
                            <el-button text size="small" @click="showReplyInput(r)">
                              <el-icon><ChatDotRound /></el-icon> 回复
                            </el-button>
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
          </el-tab-pane>

          <el-tab-pane label="学习笔记" name="notes">
            <div class="tab-content-scroll">
              <div class="notes-header">
                <el-button type="primary" @click="showNoteForm = !showNoteForm">
                  <el-icon><Plus /></el-icon> {{ showNoteForm ? '取消' : '新建笔记' }}
                </el-button>
              </div>
              <div v-if="showNoteForm" class="note-form">
                <el-input v-model="noteForm.title" placeholder="笔记标题" maxlength="100" />
                <el-input v-model="noteForm.content" type="textarea" :rows="6" placeholder="记录学习要点..." maxlength="2000" show-word-limit />
                <div class="note-form-actions">
                  <el-button @click="resetNoteForm">重置</el-button>
                  <el-button type="primary" @click="submitNote" :loading="submitting">保存笔记</el-button>
                </div>
              </div>
              <div v-loading="notesLoading" class="notes-list">
                <el-empty v-if="!notes.length && !notesLoading" description="暂无笔记，开始记录学习心得吧" />
                <div v-for="n in notes" :key="n.id" class="note-item">
                  <div class="note-header">
                    <h4>{{ n.title }}</h4>
                    <div class="note-actions">
                      <el-button text size="small" @click="editNote(n)"><el-icon><Edit /></el-icon> 编辑</el-button>
                      <el-button text size="small" type="danger" @click="deleteNote(n.id)"><el-icon><Delete /></el-icon> 删除</el-button>
                    </div>
                  </div>
                  <p class="note-content">{{ n.content }}</p>
                  <span class="note-time">{{ formatTime(n.updated_at || n.created_at) }}</span>
                </div>
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { courseApi } from '@/api/modules'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, VideoCamera, VideoPlay, ChatDotRound, Plus, Edit, Delete, Bell, Lock } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { useCourseNotifications } from '@/composables/useNotifications'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const { unreadCount } = useCourseNotifications()
const courseId = parseInt(route.params.id)
const course = ref(null)
const chapters = ref([])
const activeLesson = ref(null)
const enrolled = ref(false)
const isOwner = ref(false)

// Determine if a lesson is free to watch (lesson.is_free OR within free_preview_count)
const isLessonFree = (lesson) => {
  if (!lesson || !course.value) return false
  // 课时本身标记为免费
  if (lesson.is_free) return true
  // 课程设置了免费试看数量，前N个课时免费
  const previewCount = course.value.free_preview_count || 0
  if (previewCount > 0) {
    const allLessons = (chapters.value || []).reduce((acc, ch) => acc.concat(ch.lessons || []), [])
    const idx = allLessons.findIndex(l => l.id === lesson.id)
    if (idx >= 0 && idx < previewCount) return true
  }
  return false
}

// Tab state
const activeTab = ref('catalog')

// Comments state
const comments = ref([])
const commentsLoading = ref(false)
const newComment = ref('')
const replyingTo = ref(null)
const replyContent = ref('')
const submitting = ref(false)
const highlightedCommentId = ref(null)
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
      node.parent_user = parent.user
      // 挂到根评论下
      const rootId = getRootId(c)
      map[rootId].children.push(node)
    } else {
      roots.push(node)
    }
  })

  return roots
})

// Notes state
const notes = ref([])
const notesLoading = ref(false)
const showNoteForm = ref(false)
const editingNoteId = ref(null)
const noteForm = ref({ title: '', content: '' })

const selectLesson = (lesson) => {
  // 付费课程未购买时，只能看免费试看课时；免费课程所有课时可直接观看
  if (!isOwner.value && !enrolled.value && !isLessonFree(lesson) && course.value.price > 0) {
    ElMessage.warning('请先购买课程后观看完整内容')
    return
  }
  activeLesson.value = lesson
  router.replace({ query: { lesson: lesson.id } })
}

const onTabChange = (tab) => {
  if (tab === 'comments' && !comments.value.length) {
    loadComments()
  }
  if (tab === 'notes' && !notes.value.length) {
    loadNotes()
  }
}

// Load comments
const loadComments = async () => {
  commentsLoading.value = true
  try {
    const res = await courseApi.getComments(courseId)
    comments.value = res.items || []
    // Scroll to highlighted comment if navigated from notification
    if (highlightedCommentId.value) {
      await nextTick()
      const el = document.getElementById(`comment-${highlightedCommentId.value}`)
      if (el) {
        el.scrollIntoView({ behavior: 'smooth', block: 'center' })
      }
    }
  } catch (err) {
    ElMessage.error(err.detail || '加载评论失败')
  } finally {
    commentsLoading.value = false
  }
}

// Submit comment
const submitComment = async () => {
  if (!newComment.value.trim()) {
    ElMessage.warning('请输入评论内容')
    return
  }
  submitting.value = true
  try {
    await courseApi.createComment(courseId, {
      content: newComment.value.trim(),
      lesson_id: activeLesson.value?.id || null,
    })
    ElMessage.success('评论发布成功')
    newComment.value = ''
    loadComments()
  } catch (err) {
    ElMessage.error(err.detail || '发布失败')
  } finally {
    submitting.value = false
  }
}

// Show reply input
const showReplyInput = (comment) => {
  if (!enrolled.value && !isOwner.value) {
    ElMessage.warning('请先加入或购买课程后参与回复')
    return
  }
  replyingTo.value = comment.id
  replyContent.value = ''
}

// Submit reply
const submitReply = async (parentId) => {
  if (!replyContent.value.trim()) {
    ElMessage.warning('请输入回复内容')
    return
  }
  submitting.value = true
  try {
    await courseApi.createComment(courseId, {
      content: replyContent.value.trim(),
      parent_id: parentId,
      lesson_id: activeLesson.value?.id || null,
    })
    ElMessage.success('回复成功')
    replyContent.value = ''
    replyingTo.value = null
    loadComments()
  } catch (err) {
    ElMessage.error(err.detail || '回复失败')
  } finally {
    submitting.value = false
  }
}

// Go to user profile
const goToUser = (user) => {
  if (!user?.id) return
  if (userStore.user?.id === user.id) {
    router.push('/profile')
  } else {
    router.push(`/user/${user.id}`)
  }
}

// Toggle expand/collapse replies
const toggleExpand = (commentId) => {
  expandedComments.value[commentId] = !expandedComments.value[commentId]
}

// Load notes
const loadNotes = async () => {
  notesLoading.value = true
  try {
    const res = await courseApi.getNotes(courseId)
    notes.value = res.items || []
  } catch (err) {
    ElMessage.error(err.detail || '加载笔记失败')
  } finally {
    notesLoading.value = false
  }
}

// Submit note
const submitNote = async () => {
  if (!noteForm.value.title.trim()) {
    ElMessage.warning('请输入笔记标题')
    return
  }
  if (!noteForm.value.content.trim()) {
    ElMessage.warning('请输入笔记内容')
    return
  }
  submitting.value = true
  try {
    if (editingNoteId.value) {
      await courseApi.updateNote(editingNoteId.value, noteForm.value)
      ElMessage.success('笔记更新成功')
    } else {
      await courseApi.createNote(courseId, noteForm.value)
      ElMessage.success('笔记保存成功')
    }
    resetNoteForm()
    loadNotes()
  } catch (err) {
    ElMessage.error(err.detail || '保存失败')
  } finally {
    submitting.value = false
  }
}

// Edit note
const editNote = (note) => {
  editingNoteId.value = note.id
  noteForm.value = { title: note.title, content: note.content }
  showNoteForm.value = true
}

// Delete note
const deleteNote = async (id) => {
  try {
    await ElMessageBox.confirm('确定要删除这条笔记吗？', '删除笔记', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await courseApi.deleteNote(id)
    ElMessage.success('笔记已删除')
    loadNotes()
  } catch (err) {
    if (err !== 'cancel') {
      ElMessage.error(err.detail || '删除失败')
    }
  }
}

// Reset note form
const resetNoteForm = () => {
  editingNoteId.value = null
  noteForm.value = { title: '', content: '' }
  showNoteForm.value = false
}

// Handle lesson complete - auto play next
const handleLessonComplete = async () => {
  if (!activeLesson.value || !enrolled.value) return
  try {
    await courseApi.updateProgress(courseId, {
      lesson_id: activeLesson.value.id,
      completed: true,
    })
  } catch (_) {
    // Non-critical
  }
  // Auto-play next lesson
  const allLessons = chapters.value.flatMap(ch => ch.lessons)
  const currentIdx = allLessons.findIndex(l => l.id === activeLesson.value.id)
  if (currentIdx < allLessons.length - 1) {
    selectLesson(allLessons[currentIdx + 1])
  }
}

// Convert number to Chinese chapter label (1→一, 2→二, etc.)
const CHINESE_NUMS = ['零', '一', '二', '三', '四', '五', '六', '七', '八', '九', '十',
  '十一', '十二', '十三', '十四', '十五', '十六', '十七', '十八', '十九', '二十']
const toChineseChapter = (num) => {
  if (!num || num < 1) return '第?章'
  if (num <= 20) return `第${CHINESE_NUMS[num]}章`
  return `第${num}章` // fallback for > 20
}

// Format time
const formatTime = (timeStr) => {
  if (!timeStr) return ''
  const date = new Date(timeStr)
  const now = new Date()
  const diff = now - date
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)

  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes} 分钟前`
  if (hours < 24) return `${hours} 小时前`
  if (days < 7) return `${days} 天前`
  return date.toLocaleDateString('zh-CN')
}

onMounted(async () => {
  try {
    const res = await courseApi.learnCourse(courseId)
    course.value = res
    chapters.value = res.chapters || []
    isOwner.value = res.is_owner || false
    enrolled.value = res.enrolled || false

    // Select lesson from query param (use selectLesson for access check)
    const lessonId = route.query.lesson
    if (lessonId) {
      for (const ch of chapters.value) {
        const lesson = ch.lessons?.find(l => l.id === parseInt(lessonId))
        if (lesson) {
          selectLesson(lesson)
          break
        }
      }
    }
    // Default to first accessible lesson (free lesson for non-enrolled users on paid courses)
    if (!activeLesson.value) {
      for (const ch of chapters.value) {
        if (ch.lessons?.length) {
          if (!isOwner.value && !enrolled.value && course.value.price > 0) {
            // 付费课程未购买用户：自动选择第一个免费试看课时
            const freeLesson = ch.lessons.find(l => isLessonFree(l))
            if (freeLesson) {
              selectLesson(freeLesson)
              break
            }
          } else {
            // 免费课程、已购买用户或课程所有者：选择第一个课时
            selectLesson(ch.lessons[0])
            break
          }
        }
      }
    }

    // Preload comments (lazy-load notes on tab switch)
    if (route.query.tab === 'comments') {
      activeTab.value = 'comments'
      const targetCommentId = route.query.comment_id
      if (targetCommentId) {
        highlightedCommentId.value = parseInt(targetCommentId)
      }
    }
    loadComments()
  } catch (err) {
    ElMessage.error(err.detail || '无权访问，请先加入或购买课程')
  }
})

// Record browse history when lesson changes
watch(activeLesson, (lesson) => {
  if (lesson) {
    try { courseApi.recordBrowse(courseId, lesson.id) } catch (_) {}
  }
})
</script>

<style scoped>
.learn-page { min-height: 100vh; background: #f5f5f5; }

/* Header */
.learn-header { background: #fff; border-bottom: 1px solid #eee; padding: 12px 0; position: sticky; top: 0; z-index: 100; }
.learn-header .container { display: flex; align-items: center; gap: 16px; }
.learn-header h2 { font-size: 18px; margin: 0; flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.progress-text { font-size: 13px; color: #999; flex-shrink: 0; }
.msg-link { color: #666; transition: color 0.2s; display: flex; align-items: center; }
.msg-link:hover { color: #409eff; }

/* Body — single column (no lesson) */
.learn-body-single {
  padding-top: 20px; padding-bottom: 40px;
  max-width: 1000px; margin: 0 auto;
}

/* Body — left/right layout (watching lesson) */
.learn-body {
  display: flex; gap: 20px; align-items: flex-start;
  padding-top: 20px; padding-bottom: 40px;
  max-width: 1300px; margin: 0 auto;
}

/* Full-width catalog card */
.catalog-full { padding: 20px 24px; }
.catalog-title { margin: 0 0 16px; font-size: 18px; font-weight: 600; }
.catalog-scroll-full { max-height: 560px; overflow-y: auto; }

/* Card base */
.card { background: #fff; border-radius: 10px; }

/* ========== Left: Video Section ========== */
.video-section {
  flex: 0 0 62%; padding: 24px; min-height: 500px;
}
.video-title { margin: 0 0 8px; font-size: 18px; }
.lesson-desc { color: #666; font-size: 14px; margin: 0 0 16px; line-height: 1.6; }
.video-player { width: 100%; max-height: 460px; border-radius: 8px; background: #000; }
.no-video { padding: 100px 0; text-align: center; color: #ccc; }
.no-video p { margin-top: 12px; }

/* ========== Right: Tabs Panel ========== */
.tabs-section {
  flex: 0 0 calc(38% - 20px); padding: 16px 20px;
  /* Match video card height */
  align-self: stretch;
  display: flex; flex-direction: column;
  overflow: hidden;
}

.tabs-section :deep(.el-tabs) {
  display: flex; flex-direction: column;
  flex: 1; overflow: hidden;
}
.tabs-section :deep(.el-tabs__header) {
  margin-bottom: 12px; flex-shrink: 0;
}
.tabs-section :deep(.el-tabs__content) {
  flex: 1; overflow: hidden;
}
.tabs-section :deep(.el-tab-pane) {
  height: 100%; overflow: hidden;
}
.tabs-section :deep(.el-tabs__item) {
  font-size: 14px; font-weight: 500;
}

/* Scrollable area inside each tab */
.tab-content-scroll {
  height: 100%; overflow-y: auto; padding-right: 4px;
}
/* The catalog list also scrolls */
.catalog-list {
  overflow-y: auto;
  max-height: calc(100vh - 260px);
}

.empty-tab { padding: 40px 0; }

/* Catalog Tab */
.chapter-group { margin-bottom: 18px; }
.chapter-group:last-child { margin-bottom: 0; }

.chapter-header {
  display: flex; align-items: center; gap: 8px;
  padding: 8px 0; border-bottom: 1px solid #f0f0f0; margin-bottom: 2px;
}
.chapter-label {
  font-weight: 600; font-size: 12px; color: #4f6ef7;
  background: #ecf5ff; padding: 2px 8px; border-radius: 4px;
  flex-shrink: 0;
}
.chapter-name { font-weight: 600; font-size: 14px; color: #333; flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.chapter-count { font-size: 12px; color: #999; flex-shrink: 0; }

.lesson-row {
  display: flex; align-items: center; justify-content: space-between;
  padding: 9px 10px; cursor: pointer; border-radius: 6px;
  transition: background 0.15s;
}
.lesson-row:hover { background: #f5f7fa; }
.lesson-row.active { background: #ecf5ff; }
.lesson-row.locked { color: #ccc; cursor: not-allowed; }
.lesson-row.locked:hover { background: transparent; }

.lesson-info { display: flex; align-items: center; gap: 6px; flex: 1; overflow: hidden; }
.lesson-number { font-size: 13px; color: #4f6ef7; font-weight: 500; flex-shrink: 0; }
.lesson-name { font-size: 13px; color: #333; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.lesson-row.active .lesson-name { color: #4f6ef7; font-weight: 500; }
.lesson-meta { font-size: 12px; color: #999; flex-shrink: 0; margin-left: 10px; }

/* Comments */
.comment-input { margin-bottom: 20px; }
.comment-input .el-textarea { margin-bottom: 10px; }
.comment-hint { margin-bottom: 20px; }
.comment-list { display: flex; flex-direction: column; gap: 16px; }

.comment-item { padding: 12px; background: #fafafa; border-radius: 8px; }

/* 一级评论 */
.comment-main { display: flex; gap: 12px; }

.comment-author { display: flex; align-items: center; gap: 8px; cursor: pointer; flex-shrink: 0; }
.comment-name { font-weight: 600; font-size: 14px; }

.comment-body { flex: 1; min-width: 0; }
.comment-text { margin: 0 0 8px; font-size: 14px; line-height: 1.6; word-break: break-word; }

.comment-footer { display: flex; align-items: center; justify-content: space-between; font-size: 12px; color: #999; }
.comment-actions-right { display: flex; gap: 16px; }
.comment-time { color: #999; font-size: 12px; }

/* 回复输入框 */
.reply-input-inline { margin: 10px 0 10px 44px; padding: 10px; background: #f9f9f9; border-radius: 8px; }
.reply-actions { display: flex; gap: 6px; margin-top: 8px; justify-content: flex-end; }

/* 二级回复区域 */
.reply-section {
  margin-top: 12px; padding-top: 12px; border-top: 1px solid #eee;
  display: flex; flex-direction: column; gap: 8px;
}

.reply-item { display: flex; gap: 8px; padding: 8px 10px; margin-left: 44px; background: #f5f5f5; border-radius: 6px; }

.reply-author { display: flex; align-items: center; gap: 6px; cursor: pointer; flex-shrink: 0; }
.reply-name { font-weight: 600; font-size: 13px; color: #409eff; }
.reply-name:hover { text-decoration: underline; }

.reply-body { flex: 1; min-width: 0; }
.reply-to-line { margin-bottom: 2px; font-size: 12px; }
.reply-to-text { color: #999; }
.reply-parent-name { color: #409eff; font-weight: 600; cursor: pointer; }
.reply-parent-name:hover { text-decoration: underline; }

.reply-text { margin: 0 0 4px; font-size: 13px; line-height: 1.5; word-break: break-word; color: #333; }

.reply-footer { display: flex; align-items: center; justify-content: space-between; font-size: 11px; color: #999; }
.reply-actions-right { display: flex; gap: 12px; }
.reply-time { color: #999; font-size: 11px; }

/* 展开/收起按钮 */
.expand-btn {
  margin-left: 44px; padding: 6px 12px; font-size: 13px; color: #409eff;
  cursor: pointer; text-align: center; border-radius: 4px; transition: background 0.2s;
}
.expand-btn:hover { background: #e8f4ff; }

.artisan-badge {
  font-size: 10px; color: #e6a23c; background: #fdf6ec;
  border: 1px solid #faecd8; padding: 0 5px; border-radius: 3px;
  font-weight: 500; line-height: 16px; flex-shrink: 0;
}

/* Highlighted comment (navigated from notification) */
.comment-item.highlighted {
  background: #fff9e6; border-radius: 8px;
  animation: comment-highlight-fade 3s ease-out;
}
.reply-item.highlighted {
  background: #fff9e6; border-radius: 4px;
  animation: comment-highlight-fade 3s ease-out;
}
@keyframes comment-highlight-fade {
  0% { background-color: #ffe58f; }
  100% { background-color: transparent; }
}

/* Notes */
.notes-header { margin-bottom: 14px; }
.note-form { margin-bottom: 20px; padding: 14px; background: #f9f9f9; border-radius: 8px; }
.note-form .el-input { margin-bottom: 10px; }
.note-form-actions { display: flex; gap: 6px; justify-content: flex-end; }
.note-item { padding: 14px; margin-bottom: 10px; border: 1px solid #eee; border-radius: 8px; }
.note-item:hover { border-color: #d0d0d0; }
.note-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.note-header h4 { margin: 0; font-size: 14px; color: #333; }
.note-actions { display: flex; gap: 4px; }
.note-content { font-size: 13px; color: #666; line-height: 1.6; margin: 0 0 6px; white-space: pre-wrap; }
.note-time { font-size: 11px; color: #999; }
</style>
