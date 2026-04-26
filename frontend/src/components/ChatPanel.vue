<template>
  <el-card shadow="never" class="chat-card">
    <template #header>
      <div class="card-header">
        <div class="header-left">
          <div class="ai-avatar">
            <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/>
            </svg>
          </div>
          <div>
            <span class="header-title">AI 医疗助手</span>
            <span v-if="props.sessionId" class="header-status">在线</span>
          </div>
        </div>
        <el-tag v-if="thinking" type="warning" effect="light" size="small" class="thinking-tag">
          处理中...
        </el-tag>
      </div>
    </template>

    <!-- 聊天区域 -->
    <div ref="chatBody" class="chat-body">
      <!-- 空状态 -->
      <div v-if="messages.length === 0" class="chat-empty">
        <div class="empty-icon">
          <svg viewBox="0 0 24 24" width="64" height="64" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M21 11.5a8.38 8.38 0 01-.9 3.8 8.5 8.5 0 01-7.6 4.7 8.38 8.38 0 01-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 01-.9-3.8 8.5 8.5 0 014.7-7.6 8.38 8.38 0 013.8-.9h.5a8.48 8.48 0 018 8v.5z"/>
          </svg>
        </div>
        <h4>您好，我是 AI 医疗助手</h4>
        <p>请先创建会话，然后描述您的症状或健康问题。</p>
        <div class="empty-suggestions">
          <el-tag
            v-for="s in suggestions" :key="s"
            size="small"
            effect="plain"
            class="suggestion-tag"
            @click="fillSuggestion(s)"
          >{{ s }}</el-tag>
        </div>
      </div>

      <!-- 消息列表 -->
      <div
        v-for="(msg, i) in messages"
        :key="i"
        class="message-row"
        :class="msg.role === 'user' ? 'user-row' : 'assistant-row'"
      >
        <!-- AI 头像 -->
        <div v-if="msg.role === 'assistant'" class="msg-avatar ai-msg-avatar">
          <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/>
          </svg>
        </div>

        <div class="msg-content" :class="msg.role">
          <!-- 用户消息 -->
          <div v-if="msg.role === 'user'" class="bubble user-bubble">
            {{ msg.content }}
          </div>
          <!-- AI 消息（支持 Markdown） -->
          <div v-else class="bubble assistant-bubble" v-html="renderMarkdown(msg.content)"></div>
        </div>

        <!-- 用户头像 -->
        <div v-if="msg.role === 'user'" class="msg-avatar user-msg-avatar">
          <el-icon><UserFilled /></el-icon>
        </div>
      </div>

      <!-- 正在输入指示器 -->
      <div v-if="thinking" class="message-row assistant-row">
        <div class="msg-avatar ai-msg-avatar">
          <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2z"/>
          </svg>
        </div>
        <div class="msg-content assistant">
          <div class="thinking-indicator">
            <span class="dot"></span>
            <span class="dot"></span>
            <span class="dot"></span>
          </div>
        </div>
      </div>
    </div>

    <!-- 输入区域 -->
    <div class="chat-input-area">
      <div class="input-wrapper">
        <el-input
          v-model="inputText"
          placeholder="请描述您的症状..."
          @keydown.enter.exact="sendMessage"
          :disabled="!props.sessionId || thinking"
          size="large"
          class="chat-input"
        >
          <template #prefix>
            <el-icon><EditPen /></el-icon>
          </template>
        </el-input>
        <div class="input-actions">
          <el-button
            type="primary"
            @click="sendMessage"
            :disabled="!props.sessionId || thinking || !inputText.trim()"
            :icon="ChatDotRound"
            size="large"
            class="action-btn"
          >
            发送
          </el-button>
          <el-button
            type="success"
            @click="startDiagnosis"
            :disabled="!props.sessionId || thinking || !inputText.trim()"
            size="large"
            class="action-btn diagnosis-btn"
          >
            <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor" style="margin-right:4px">
              <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-1 9h-4v4h-2v-4H8v-2h4V6h2v4h4v2z"/>
            </svg>
            智能诊断
          </el-button>
        </div>
      </div>
    </div>
  </el-card>
</template>

<script setup>
import { ref, nextTick, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { sendChat, runDiagnosis } from '../api/index.js'

const props = defineProps({
  sessionId: { type: String, default: '' },
  patientInfo: { type: Object, default: null },
})

const emit = defineEmits(['diagnosisResult'])

const messages = ref([])
const inputText = ref('')
const thinking = ref(false)
const chatBody = ref(null)

const suggestions = ['头痛两天了', '发烧咳嗽有痰', '肚子疼拉肚子']

function fillSuggestion(text) {
  inputText.value = text
}

function scrollToBottom() {
  nextTick(() => {
    if (chatBody.value) {
      chatBody.value.scrollTo({ top: chatBody.value.scrollHeight, behavior: 'smooth' })
    }
  })
}

function renderMarkdown(text) {
  if (!text) return ''
  // 转义 HTML
  let html = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')

  // 分割成行处理
  const lines = html.split('\n')
  let inList = false
  const result = []

  for (let i = 0; i < lines.length; i++) {
    let line = lines[i]

    // 水平线
    if (/^---+\s*$/.test(line)) {
      if (inList) { result.push('</ul>'); inList = false }
      result.push('<hr class="md-hr"/>')
      continue
    }

    // 标题
    const hMatch = line.match(/^(#{1,3})\s+(.+)/)
    if (hMatch) {
      if (inList) { result.push('</ul>'); inList = false }
      const level = hMatch[1].length
      const sizes = { 1: '20px', 2: '17px', 3: '15px' }
      result.push(`<h${level} style="margin:10px 0 6px;font-size:${sizes[level] || '15px'};font-weight:600;color:#1f2937">${hMatch[2]}</h${level}>`)
      continue
    }

    // 无序列表
    const liMatch = line.match(/^[-*]\s+(.+)/)
    if (liMatch) {
      if (!inList) { result.push('<ul class="md-list">'); inList = true }
      result.push(`<li>${liMatch[1]}</li>`)
      continue
    }
    if (inList) { result.push('</ul>'); inList = false }

    // 空行 = 段落
    if (line.trim() === '') {
      result.push('</p><p class="md-p">')
      continue
    }

    // 普通行：行内格式化
    line = line
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(/`([^`]+)`/g, '<code class="md-inline-code">$1</code>')

    result.push(line + '<br/>')
  }
  if (inList) result.push('</ul>')

  return '<p class="md-p">' + result.join('') + '</p>'
}

async function sendMessage() {
  const text = inputText.value.trim()
  if (!text || !props.sessionId) return

  messages.value.push({ role: 'user', content: text })
  inputText.value = ''
  scrollToBottom()

  thinking.value = true
  try {
    const result = await sendChat(props.sessionId, text, props.patientInfo)
    messages.value.push({ role: 'assistant', content: result.reply })
    if (result.diagnosis) {
      emit('diagnosisResult', result)
    }
  } catch (e) {
    messages.value.push({ role: 'assistant', content: '抱歉，发生了错误，请重试。' })
    ElMessage.error('请求失败: ' + e.message)
  } finally {
    thinking.value = false
    scrollToBottom()
  }
}

async function startDiagnosis() {
  const text = inputText.value.trim()
  if (!text || !props.sessionId) return

  messages.value.push({ role: 'user', content: `🔍 诊断请求: ${text}` })
  inputText.value = ''
  scrollToBottom()

  thinking.value = true
  try {
    const result = await runDiagnosis(props.sessionId, text, '', '', props.patientInfo)
    messages.value.push({ role: 'assistant', content: result.reply || '诊断完成，请查看右侧详情。' })
    emit('diagnosisResult', result)
  } catch (e) {
    messages.value.push({ role: 'assistant', content: '诊断失败，请重试。' })
    ElMessage.error('诊断失败: ' + e.message)
  } finally {
    thinking.value = false
    scrollToBottom()
  }
}
</script>

<style scoped>
.chat-card {
  height: calc(100vh - 108px);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.ai-avatar {
  width: 34px;
  height: 34px;
  background: linear-gradient(135deg, #0d9488, #0891b2);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.header-title {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
}

.header-status {
  font-size: 11px;
  color: #10b981;
  margin-left: 6px;
}

.thinking-tag {
  animation: pulse-tag 1.5s ease-in-out infinite;
}

@keyframes pulse-tag {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

/* ── 聊天区域 ── */
.chat-body {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  background: #f8fafc;
  border-radius: 10px;
  margin-bottom: 14px;
  min-height: 200px;
  scroll-behavior: smooth;
}

/* 空状态 */
.chat-empty {
  text-align: center;
  padding: 48px 20px;
  color: #94a3b8;
}

.empty-icon {
  color: #cbd5e1;
  margin-bottom: 16px;
}

.chat-empty h4 {
  color: #475569;
  margin: 0 0 8px;
  font-size: 16px;
}

.chat-empty p {
  font-size: 13px;
  margin: 0 0 20px;
}

.empty-suggestions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
}

.suggestion-tag {
  cursor: pointer;
  transition: all 0.2s ease;
  border-radius: 16px !important;
  padding: 4px 12px;
}

.suggestion-tag:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

/* ── 消息行 ── */
.message-row {
  display: flex;
  margin-bottom: 16px;
  gap: 8px;
  animation: fadeInUp 0.3s ease;
}

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.user-row {
  justify-content: flex-end;
}

.assistant-row {
  justify-content: flex-start;
}

.msg-avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 14px;
}

.user-msg-avatar {
  background: #dbeafe;
  color: #3b82f6;
}

.ai-msg-avatar {
  background: linear-gradient(135deg, #0d9488, #0891b2);
  color: white;
}

.msg-content {
  max-width: 75%;
  min-width: 0;
}

.msg-content.user {
  display: flex;
  justify-content: flex-end;
}

/* ── 气泡 ── */
.bubble {
  padding: 10px 16px;
  word-wrap: break-word;
  line-height: 1.6;
  font-size: 14px;
}

.user-bubble {
  background: linear-gradient(135deg, #0d9488, #0891b2);
  color: white;
  border-radius: 18px 18px 4px 18px;
  box-shadow: 0 2px 8px rgba(13, 148, 136, 0.15);
}

.assistant-bubble {
  background: white;
  color: #1f2937;
  border-radius: 18px 18px 18px 4px;
  border: 1px solid #e5e7eb;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
}

/* 正在输入 */
.thinking-indicator {
  display: flex;
  gap: 4px;
  padding: 12px 16px;
  background: white;
  border-radius: 18px 18px 18px 4px;
  border: 1px solid #e5e7eb;
  align-items: center;
}

.dot {
  width: 8px;
  height: 8px;
  background: #0d9488;
  border-radius: 50%;
  animation: bounce 1.4s ease-in-out infinite;
}

.dot:nth-child(2) { animation-delay: 0.2s; }
.dot:nth-child(3) { animation-delay: 0.4s; }

@keyframes bounce {
  0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
  30% { transform: translateY(-6px); opacity: 1; }
}

/* ── 输入区域 ── */
.chat-input-area {
  flex-shrink: 0;
}

.input-wrapper {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.chat-input {
  flex: 1;
  min-width: 0;
}

.chat-input :deep(.el-input__wrapper) {
  border-radius: 10px;
  background: #f8fafc;
  box-shadow: 0 0 0 1px #e2e8f0 inset;
}

.chat-input :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 2px #0d9488 inset;
  background: white;
}

.input-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

.action-btn {
  border-radius: 10px !important;
  padding: 12px 20px !important;
  font-weight: 500;
}

.diagnosis-btn {
  background: linear-gradient(135deg, #059669, #10b981) !important;
  border: none !important;
}

.diagnosis-btn:hover {
  background: linear-gradient(135deg, #047857, #059669) !important;
}

.diagnosis-btn:disabled {
  background: #a7f3d0 !important;
  color: #6b7280 !important;
}

/* ── Markdown 样式 ── */
:deep(.md-p) {
  margin: 0;
  min-height: 1em;
}

:deep(.md-list) {
  margin: 6px 0;
  padding-left: 20px;
}

:deep(.md-list li) {
  margin-bottom: 4px;
}

:deep(.md-hr) {
  border: none;
  border-top: 1px solid #e5e7eb;
  margin: 12px 0;
}

:deep(.md-inline-code) {
  background: #f1f5f9;
  padding: 1px 6px;
  border-radius: 4px;
  font-size: 13px;
  font-family: 'SF Mono', 'Fira Code', monospace;
  color: #0d9488;
}
</style>
