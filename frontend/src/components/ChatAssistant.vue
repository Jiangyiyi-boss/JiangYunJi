<template>
  <div class="chat-assistant">
    <!-- 聊天面板 (由导航栏按钮控制显示) -->
    <transition name="chat-slide">
      <div v-if="visible" class="chat-panel">
        <div class="chat-header">
          <div class="chat-header-info">
            <span class="chat-avatar">匠</span>
            <div>
              <div class="chat-title">小匠 · 非遗知识助手</div>
              <div class="chat-subtitle">问我任何非遗问题吧</div>
            </div>
          </div>
          <div class="chat-header-actions">
            <el-button text circle size="small" @click="newConversation" title="新对话">
              <el-icon><Plus /></el-icon>
            </el-button>
            <el-button text circle size="small" @click="toggleChat" title="关闭">
              <el-icon><Close /></el-icon>
            </el-button>
          </div>
        </div>

        <div class="chat-body" ref="chatBody">
          <!-- 空状态 -->
          <div v-if="messages.length === 0" class="chat-empty">
            <el-icon :size="40"><Sunny /></el-icon>
            <p>你好！我是小匠 👋</p>
            <p class="chat-empty-hint">你可以问我非遗文化、技艺传承、手工艺知识等问题</p>
            <div class="quick-questions">
              <el-button
                v-for="q in quickQuestions"
                :key="q"
                size="small"
                round
                @click="sendQuick(q)"
              >{{ q }}</el-button>
            </div>
          </div>

          <!-- 消息列表 -->
          <div
            v-for="(msg, i) in messages"
            :key="i"
            class="chat-msg"
            :class="msg.role"
          >
            <div class="msg-avatar">
              <span v-if="msg.role === 'assistant'" class="avatar-icon ai">匠</span>
              <el-avatar v-else :size="28" :src="userAvatar">{{ userName?.[0] }}</el-avatar>
            </div>
            <div class="msg-bubble" v-text="msg.content" />
          </div>

          <!-- 加载状态 -->
          <div v-if="loading" class="chat-msg assistant">
            <div class="msg-avatar">
              <span class="avatar-icon ai">匠</span>
            </div>
            <div class="msg-bubble typing">
              <span class="dot" />
              <span class="dot" />
              <span class="dot" />
            </div>
          </div>
        </div>

        <div class="chat-footer">
          <el-input
            v-model="inputText"
            placeholder="输入你的问题..."
            maxlength="500"
            :disabled="loading"
            @keydown.enter="sendMessage"
          >
            <template #suffix>
              <el-button
                type="primary"
                :icon="Promotion"
                circle
                size="small"
                :disabled="!inputText.trim() || loading"
                @click="sendMessage"
              />
            </template>
          </el-input>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, nextTick, computed } from 'vue'
import { useUserStore } from '@/stores/user'
import { chatApi } from '@/api/modules'
import { ElMessage } from 'element-plus'
import { Close, Plus, Sunny, Promotion } from '@element-plus/icons-vue'

const userStore = useUserStore()
const userName = computed(() => userStore.user?.nickname || '')
const userAvatar = computed(() => userStore.user?.avatar || '')

const visible = ref(false)
const loading = ref(false)

defineExpose({ visible })
const inputText = ref('')
const messages = ref([])
const chatBody = ref(null)

// 会话 ID: 内存版记忆按它区分上下文, 「新对话」重新生成即开启全新会话
const conversationId = ref('')
const genConversationId = () =>
  `c_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 10)}`
conversationId.value = genConversationId()

const quickQuestions = [
  '什么是青花瓷？',
  '中国四大名绣有哪些？',
  '紫砂壶为什么好？',
  '非遗有哪些分类？',
  '剪纸的历史有多久？',
]

const toggleChat = () => {
  visible.value = !visible.value
  if (visible.value) {
    nextTick(() => scrollToBottom())
  }
}

const newConversation = () => {
  // 新会话 = 新 ID, 后端内存记忆即切换到全新上下文
  messages.value = []
  conversationId.value = genConversationId()
}

const sendQuick = (q) => {
  inputText.value = q
  sendMessage()
}

const sendMessage = async () => {
  const text = inputText.value.trim()
  if (!text || loading.value) return

  messages.value.push({ role: 'user', content: text })
  inputText.value = ''
  loading.value = true
  await nextTick()
  scrollToBottom()

  try {
    const response = await chatApi.sendMessage(text, conversationId.value)
    if (!response.ok) {
      const err = await response.json().catch(() => ({}))
      throw new Error(err.detail || `请求失败 (${response.status})`)
    }

    // 读取 SSE 流
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    let aiMsg = { role: 'assistant', content: '' }
    messages.value.push(aiMsg)

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop()  // 未完成的行放回 buffer

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        const dataStr = line.slice(6)
        if (dataStr === '[DONE]') continue

        try {
          const event = JSON.parse(dataStr)
          if (event.event === 'message') {
            aiMsg.content += event.answer || ''
          }
          if (event.event === 'error') {
            aiMsg.content = event.message || '服务异常'
          }
        } catch {
          // 解析失败的行跳过
        }
      }
      scrollToBottom()
    }
  } catch (err) {
    ElMessage.error(err.message || 'AI 响应失败，请稍后重试')
    // 移除空的 assistant 消息
    const last = messages.value[messages.value.length - 1]
    if (last && last.role === 'assistant' && !last.content) {
      messages.value.pop()
    }
  } finally {
    loading.value = false
  }
}

const scrollToBottom = () => {
  nextTick(() => {
    if (chatBody.value) {
      chatBody.value.scrollTop = chatBody.value.scrollHeight
    }
  })
}
</script>

<style scoped>
.chat-assistant {
  position: fixed;
  right: 24px;
  bottom: 24px;
  z-index: 999;
}

/* ── 面板 ── */
.chat-panel {
  position: fixed;
  right: 24px;
  bottom: 24px;
  width: 380px;
  height: 520px;
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 8px 40px rgba(0,0,0,0.12);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* ── 头部 ── */
.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  border-bottom: 1px solid #f0f0f0;
  background: #fafbfc;
}

.chat-header-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.chat-avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  background: var(--color-primary, #3b4f6b);
  color: #fff;
  border-radius: 10px;
  font-weight: 600;
  font-size: 16px;
}

.chat-title {
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

.chat-subtitle {
  font-size: 11px;
  color: #999;
}

.chat-header-actions {
  display: flex;
  gap: 4px;
}

/* ── 消息区 ── */
.chat-body {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  background: #f8f9fb;
}

.chat-body::-webkit-scrollbar {
  width: 4px;
}

.chat-body::-webkit-scrollbar-thumb {
  background: #ddd;
  border-radius: 2px;
}

.chat-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #999;
  gap: 8px;
  text-align: center;
  padding: 20px;
}

.chat-empty .el-icon {
  color: #c0c4cc;
}

.chat-empty p {
  margin: 0;
  font-size: 15px;
  color: #666;
}

.chat-empty-hint {
  font-size: 12px !important;
  color: #aaa !important;
}

.quick-questions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
  margin-top: 12px;
}

.quick-questions .el-button {
  font-size: 12px;
}

/* ── 消息气泡 ── */
.chat-msg {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}

.chat-msg.user {
  flex-direction: row-reverse;
}

.msg-avatar {
  flex-shrink: 0;
}

.avatar-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
}

.avatar-icon.ai {
  background: #fef0f0;
  color: #e6a23c;
}

.msg-bubble {
  max-width: 260px;
  padding: 10px 14px;
  border-radius: 14px;
  font-size: 13px;
  line-height: 1.6;
  word-break: break-word;
}

.chat-msg.user .msg-bubble {
  background: var(--color-primary, #3b4f6b);
  color: #fff;
  border-bottom-right-radius: 4px;
}

.chat-msg.assistant .msg-bubble {
  background: #fff;
  color: #333;
  border: 1px solid #eee;
  border-bottom-left-radius: 4px;
  white-space: pre-wrap;
}

/* ── 打字动画 ── */
.msg-bubble.typing {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 14px 18px;
}

.dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #bbb;
  animation: bounce 1.4s infinite ease-in-out both;
}

.dot:nth-child(1) { animation-delay: -0.32s; }
.dot:nth-child(2) { animation-delay: -0.16s; }
.dot:nth-child(3) { animation-delay: 0; }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

/* ── 输入区 ── */
.chat-footer {
  padding: 12px 16px;
  border-top: 1px solid #f0f0f0;
  background: #fff;
}

/* ── 过渡动画 ── */
.chat-slide-enter-active {
  transition: all 0.3s ease;
}

.chat-slide-leave-active {
  transition: all 0.2s ease;
}

.chat-slide-enter-from,
.chat-slide-leave-to {
  opacity: 0;
  transform: translateY(16px) scale(0.95);
}

/* ── 响应式 ── */
@media (max-width: 480px) {
  .chat-panel {
    width: calc(100vw - 32px);
    right: -8px;
    height: 480px;
  }

  .chat-fab {
    padding: 10px 16px;
  }

  .fab-label {
    display: none;
  }
}
</style>
