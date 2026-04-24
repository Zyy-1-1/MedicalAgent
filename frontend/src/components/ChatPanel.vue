<template>
  <el-card shadow="hover" style="height: 100%; display: flex; flex-direction: column">
    <template #header>
      <span><el-icon><ChatDotRound /></el-icon> AI 医疗助手</span>
    </template>
    <div
      ref="chatBody"
      style="flex: 1; overflow-y: auto; padding: 12px; background: #fafafa; border-radius: 8px; margin-bottom: 12px; min-height: 300px"
    >
      <div v-if="messages.length === 0" style="text-align: center; color: #c0c4cc; padding-top: 80px">
        <el-icon :size="48"><ChatSquare /></el-icon>
        <p>请描述您的症状，获取 AI 初步评估。</p>
        <p style="font-size: 12px">本系统不构成医疗建议，请务必咨询专业医生。</p>
      </div>
      <div
        v-for="(msg, i) in messages"
        :key="i"
        style="margin-bottom: 16px"
      >
        <div v-if="msg.role === 'user'" style="display: flex; justify-content: flex-end">
          <div style="max-width: 75%; background: #409eff; color: white; padding: 10px 14px; border-radius: 12px 12px 4px 12px; word-wrap: break-word">
            {{ msg.content }}
          </div>
        </div>
        <div v-else style="display: flex; justify-content: flex-start">
          <div
            style="max-width: 80%; background: white; padding: 10px 14px; border-radius: 12px 12px 12px 4px; word-wrap: break-word; border: 1px solid #ebeef5"
            v-html="renderMarkdown(msg.content)"
          ></div>
        </div>
      </div>
      <div v-if="thinking" style="color: #909399; font-style: italic; padding: 8px">
        AI 思考中...
      </div>
    </div>

    <div style="display: flex; gap: 8px">
      <el-input
        v-model="inputText"
        placeholder="请描述您的症状..."
        @keydown.enter.exact="sendMessage"
        :disabled="!sessionId || thinking"
      />
      <el-button type="primary" @click="sendMessage" :disabled="!sessionId || thinking || !inputText.trim()">
        发送
      </el-button>
      <el-button type="success" @click="startDiagnosis" :disabled="!sessionId || thinking || !inputText.trim()">
        智能诊断
      </el-button>
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

function scrollToBottom() {
  nextTick(() => {
    if (chatBody.value) {
      chatBody.value.scrollTop = chatBody.value.scrollHeight
    }
  })
}

function renderMarkdown(text) {
  if (!text) return ''
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/\n\n/g, '</p><p>')
    .replace(/\n/g, '<br/>')
    .replace(/## (.+)/g, '<h3 style="margin:8px 0 4px">$1</h3>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/^- (.+)/gm, '<li>$1</li>')
    .replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>')
    .replace(/⚠️/g, '<span style="color:#e6a23c">⚠️</span>')
    .replace(/---/g, '<hr/>')
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

  messages.value.push({ role: 'user', content: `[诊断请求] ${text}` })
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
