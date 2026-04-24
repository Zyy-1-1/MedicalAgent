<template>
  <div style="display: flex; gap: 20px; height: calc(100vh - 100px); flex-wrap: wrap">
    <!-- Left: Patient Info & Controls -->
    <div style="width: 300px; display: flex; flex-direction: column; gap: 16px; flex-shrink: 0">
      <PatientForm v-model="patientInfo" />
      <el-card shadow="hover">
        <template #header><span>会话管理</span></template>
        <div v-if="!sessionId">
          <el-button type="primary" @click="initSession" :loading="loading">创建会话</el-button>
        </div>
        <div v-else>
          <el-tag type="success" size="small">已连接</el-tag>
          <p style="font-size: 12px; color: #909399; margin-top: 8px">会话ID: {{ sessionId }}</p>
        </div>
      </el-card>
    </div>

    <!-- Center: Chat Panel -->
    <div style="flex: 1; min-width: 400px">
      <ChatPanel
        :session-id="sessionId"
        :patient-info="patientInfo"
        @diagnosis-result="handleDiagnosisResult"
      />
    </div>

    <!-- Right: Diagnosis Result -->
    <div style="width: 380px; flex-shrink: 0">
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
    ElMessage.success('会话创建成功')
  } catch (e) {
    ElMessage.error('会话创建失败: ' + e.message)
  } finally {
    loading.value = false
  }
}

function handleDiagnosisResult(result) {
  lastResult.value = result
}
</script>
