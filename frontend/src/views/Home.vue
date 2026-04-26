<template>
  <div class="home-layout">
    <!-- Left: Patient Info & Controls -->
    <div class="sidebar-left">
      <PatientForm v-model="patientInfo" />

      <el-card shadow="never" class="session-card">
        <template #header>
          <div class="card-header">
            <el-icon><Connection /></el-icon>
            <span>会话管理</span>
          </div>
        </template>
        <div class="session-body">
          <div v-if="!sessionId" class="session-empty">
            <el-button type="primary" @click="initSession" :loading="loading" class="start-btn">
              {{ loading ? '创建中...' : '创建会话' }}
            </el-button>
            <p class="session-hint">开始前请先创建会话</p>
          </div>
          <div v-else class="session-active">
            <div class="session-status">
              <span class="status-dot"></span>
              <span>已连接</span>
            </div>
            <div class="session-id-box">
              <span class="id-label">会话ID</span>
              <code class="id-value">{{ sessionId }}</code>
            </div>
            <el-button type="danger" plain size="small" @click="resetSession" class="reset-btn">
              重新创建
            </el-button>
          </div>
        </div>
      </el-card>

      <!-- 快速提示 -->
      <el-card shadow="never" class="tip-card">
        <template #header>
          <div class="card-header">
            <el-icon><InfoFilled /></el-icon>
            <span>使用提示</span>
          </div>
        </template>
        <div class="tip-body">
          <ul>
            <li>填写患者信息可获得更精准的分析</li>
            <li>描述症状时尽量详细（部位、时间、程度）</li>
            <li>"智能诊断"将启动多智能体协作分析</li>
            <li>本系统不构成医疗建议</li>
          </ul>
        </div>
      </el-card>
    </div>

    <!-- Center: Chat Panel -->
    <div class="center-panel">
      <ChatPanel
        :session-id="sessionId"
        :patient-info="patientInfo"
        @diagnosis-result="handleDiagnosisResult"
      />
    </div>

    <!-- Right: Diagnosis Result -->
    <div class="sidebar-right">
      <DiagnosisResult :result="lastResult" />
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { createSession } from '../api/index.js'
import PatientForm from '../components/PatientForm.vue'
import ChatPanel from '../components/ChatPanel.vue'
import DiagnosisResult from '../components/DiagnosisResult.vue'

const sessionId = ref('')
const patientInfo = ref(null)
const lastResult = ref(null)
const loading = ref(false)

async function initSession() {
  loading.value = true
  try {
    const session = await createSession(patientInfo.value)
    sessionId.value = session.session_id
    ElMessage.success({ message: '会话创建成功', duration: 2000 })
  } catch (e) {
    ElMessage.error('会话创建失败: ' + e.message)
  } finally {
    loading.value = false
  }
}

function resetSession() {
  sessionId.value = ''
  lastResult.value = null
  ElMessage.info('会话已重置')
}

function handleDiagnosisResult(result) {
  lastResult.value = result
}
</script>

<style scoped>
.home-layout {
  display: flex;
  gap: 20px;
  align-items: flex-start;
}

/* ── 左侧栏 ── */
.sidebar-left {
  width: 300px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  flex-shrink: 0;
  position: sticky;
  top: 84px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
}

/* 会话卡片 */
.session-body {
  text-align: center;
}

.session-empty {
  padding: 8px 0;
}

.start-btn {
  width: 100%;
  padding: 12px 0;
  font-size: 15px;
  border-radius: 8px;
}

.session-hint {
  font-size: 12px;
  color: #9ca3af;
  margin: 10px 0 0;
}

.session-active {
  display: flex;
  flex-direction: column;
  gap: 10px;
  align-items: center;
}

.session-status {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #10b981;
  font-weight: 500;
}

.status-dot {
  width: 8px;
  height: 8px;
  background: #10b981;
  border-radius: 50%;
  display: inline-block;
  animation: pulse-dot 2s ease-in-out infinite;
}

@keyframes pulse-dot {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

.session-id-box {
  background: #f3f4f6;
  border-radius: 8px;
  padding: 10px 14px;
  width: 100%;
  text-align: left;
}

.id-label {
  font-size: 11px;
  color: #9ca3af;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.id-value {
  display: block;
  font-size: 13px;
  color: #374151;
  font-family: 'SF Mono', 'Fira Code', monospace;
  margin-top: 2px;
  word-break: break-all;
}

.reset-btn {
  width: 100%;
}

/* 提示卡片 */
.tip-card {
  background: linear-gradient(135deg, #f0fdf4 0%, #ecfdf5 100%);
  border-color: #bbf7d0 !important;
}

.tip-body ul {
  margin: 0;
  padding-left: 18px;
  font-size: 13px;
  line-height: 1.8;
  color: #374151;
}

/* ── 中间聊天区 ── */
.center-panel {
  flex: 1;
  min-width: 0;
}

/* ── 右侧诊断结果 ── */
.sidebar-right {
  width: 380px;
  flex-shrink: 0;
  position: sticky;
  top: 84px;
}

/* ── 响应式 ── */
@media (max-width: 1400px) {
  .sidebar-right { width: 340px; }
}

@media (max-width: 1200px) {
  .sidebar-right { width: 320px; }
}

@media (max-width: 1024px) {
  .home-layout { flex-wrap: wrap; }
  .sidebar-left { width: 100%; position: static; }
  .sidebar-right { width: 100%; position: static; }
}
</style>
