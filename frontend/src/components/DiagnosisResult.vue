<template>
  <el-card shadow="never" class="result-card">
    <template #header>
      <div class="card-header">
        <el-icon><Document /></el-icon>
        <span>诊断结果</span>
        <el-tag v-if="result" size="small" type="success" effect="plain" class="result-badge">
          {{ timeAgo }}
        </el-tag>
      </div>
    </template>

    <!-- 空状态 -->
    <div v-if="!result" class="result-empty">
      <div class="empty-icon">
        <svg viewBox="0 0 24 24" width="56" height="56" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-1 9h-4v4h-2v-4H8v-2h4V6h2v4h4v2z"/>
          <circle cx="12" cy="16" r="0.5" fill="currentColor"/>
        </svg>
      </div>
      <h4>暂无诊断结果</h4>
      <p>请在聊天面板中描述症状<br/>并点击"智能诊断"按钮</p>
    </div>

    <!-- 诊断内容 -->
    <div v-else class="result-content">

      <!-- 分诊评估 -->
      <div v-if="result.triage" class="section triage-section" :class="urgencyClass(result.triage.urgency)">
        <div class="section-header">
          <el-icon><WarningFilled /></el-icon>
          <span>分诊评估</span>
          <el-tag :type="urgencyType(result.triage.urgency)" size="small" effect="dark" class="urgency-tag">
            {{ urgencyLabel(result.triage.urgency) }}
          </el-tag>
        </div>
        <div class="section-body">
          <p class="triage-action">{{ result.triage.recommended_action }}</p>
          <p v-if="result.triage.specialty" class="triage-specialty">
            <el-icon><Guide /></el-icon> 建议科室: {{ result.triage.specialty }}
          </p>
        </div>
      </div>

      <!-- 症状分析 -->
      <div v-if="result.symptom_analysis" class="section">
        <div class="section-header">
          <el-icon><DataAnalysis /></el-icon>
          <span>症状分析</span>
        </div>
        <div class="section-body">
          <div v-if="result.symptom_analysis.key_symptoms?.length" class="subsection">
            <label>关键症状</label>
            <div class="tag-group">
              <el-tag
                v-for="s in result.symptom_analysis.key_symptoms" :key="s"
                size="small" type="info" effect="plain"
                class="symptom-tag"
              >{{ s }}</el-tag>
            </div>
          </div>
          <div v-if="result.symptom_analysis.possible_conditions?.length" class="subsection">
            <label>可能的疾病</label>
            <div class="tag-group">
              <el-tag
                v-for="c in result.symptom_analysis.possible_conditions" :key="c"
                size="small" type="warning" effect="light"
                class="condition-tag"
              >{{ c }}</el-tag>
            </div>
          </div>
          <div v-if="result.symptom_analysis.requires_emergency" class="emergency-warning">
            <el-icon><WarningFilled /></el-icon> 检测到紧急症状指标，请立即就医！
          </div>
        </div>
      </div>

      <!-- 初步诊断 -->
      <div v-if="result.diagnosis" class="section diagnosis-section">
        <div class="section-header">
          <el-icon><Tickets /></el-icon>
          <span>初步诊断</span>
        </div>
        <div class="section-body">
          <div class="diagnosis-primary">
            <div class="diagnosis-name">{{ result.diagnosis.primary_diagnosis }}</div>
            <el-progress
              :percentage="confidencePercent(result.diagnosis.confidence)"
              :status="confidenceStatus(result.diagnosis.confidence)"
              :stroke-width="6"
              :text-inside="false"
              class="confidence-bar"
            />
            <span class="confidence-label">置信度: {{ confidenceLabel(result.diagnosis.confidence) }}</span>
          </div>
          <p class="reasoning-text">{{ result.diagnosis.reasoning }}</p>

          <div v-if="result.diagnosis.differential_diagnoses?.length" class="subsection">
            <label>鉴别诊断</label>
            <ul class="differential-list">
              <li v-for="d in result.diagnosis.differential_diagnoses" :key="d">{{ d }}</li>
            </ul>
          </div>
        </div>
      </div>

      <!-- 治疗建议 -->
      <div v-if="result.treatment" class="section">
        <div class="section-header">
          <el-icon><FirstAid /></el-icon>
          <span>治疗建议</span>
        </div>
        <div class="section-body">
          <div class="subsection">
            <label class="action-label">
              <el-icon size="14"><AlarmClock /></el-icon> 紧急措施
            </label>
            <ul class="action-list">
              <li v-for="a in result.treatment.immediate_actions" :key="a">{{ a }}</li>
            </ul>
          </div>

          <el-collapse v-model="activeCollapse" class="treatment-collapse">
            <el-collapse-item v-if="result.treatment.medications?.length" title="参考用药" name="meds">
              <div class="tag-group">
                <el-tag
                  v-for="m in result.treatment.medications" :key="m"
                  size="small" type="primary" effect="light"
                  class="med-tag"
                >{{ m }}</el-tag>
              </div>
            </el-collapse-item>
            <el-collapse-item v-if="result.treatment.lifestyle_recommendations?.length" title="生活方式建议" name="lifestyle">
              <ul class="action-list">
                <li v-for="r in result.treatment.lifestyle_recommendations" :key="r">{{ r }}</li>
              </ul>
            </el-collapse-item>
            <el-collapse-item title="随访建议" name="followup">
              <p class="followup-text">{{ result.treatment.follow_up }}</p>
            </el-collapse-item>
          </el-collapse>
        </div>
      </div>

      <!-- 知识参考 -->
      <div v-if="result.references?.length" class="section ref-section">
        <div class="section-header">
          <el-icon><Reading /></el-icon>
          <span>医学知识参考</span>
          <el-tag size="small" type="info" effect="plain">{{ result.references.length }} 条</el-tag>
        </div>
        <div class="section-body">
          <div
            v-for="ref in result.references" :key="ref.source"
            class="ref-item"
          >
            <div class="ref-header">
              <el-tag size="small" type="success" effect="light">{{ ref.source_cn || ref.source }}</el-tag>
              <span class="ref-relevance">相关度 {{ (ref.relevance * 100).toFixed(0) }}%</span>
            </div>
            <p class="ref-text">{{ ref.content?.substring(0, 150) }}{{ ref.content?.length > 150 ? '...' : '' }}</p>
          </div>
        </div>
      </div>

      <!-- GraphRAG 标识 -->
      <div v-if="result.references?.length" class="graphrag-badge">
        <svg viewBox="0 0 24 24" width="12" height="12" fill="currentColor">
          <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
        </svg>
        知识图谱检索
      </div>

      <!-- 免责声明 -->
      <el-alert
        type="warning"
        :closable="false"
        show-icon
        title="医疗免责声明"
        description="本系统生成的医疗信息仅供参考，不构成医疗建议。请务必咨询持牌医疗专业人士获取实际诊疗意见。"
        class="disclaimer-alert"
      />
    </div>
  </el-card>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  result: { type: Object, default: null },
})

const activeCollapse = ref([])

const timeAgo = computed(() => {
  if (!props.result?.triage) return ''
  return '实时分析'
})

function urgencyType(level) {
  const map = { low: 'info', medium: 'warning', high: 'danger', emergency: 'danger' }
  return map[level] || 'info'
}

function urgencyLabel(level) {
  const map = { low: '低风险', medium: '中等风险', high: '高风险', emergency: '紧急' }
  return map[level] || level
}

function urgencyClass(level) {
  const map = { low: 'urgency-low', medium: 'urgency-medium', high: 'urgency-high', emergency: 'urgency-emergency' }
  return map[level] || ''
}

function confidenceLabel(level) {
  const map = { low: '低', moderate: '中等', high: '高' }
  return map[level] || level
}

function confidencePercent(level) {
  const map = { low: 35, moderate: 65, high: 90 }
  return map[level] || 50
}

function confidenceStatus(level) {
  const map = { low: 'exception', moderate: 'warning', high: 'success' }
  return map[level] || ''
}
</script>

<style scoped>
.result-card {
  height: calc(100vh - 108px);
  overflow-y: auto;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
}

.result-badge {
  margin-left: auto;
  font-size: 11px;
}

/* ── 空状态 ── */
.result-empty {
  text-align: center;
  padding: 60px 20px;
  color: #94a3b8;
}

.empty-icon {
  color: #cbd5e1;
  margin-bottom: 12px;
}

.result-empty h4 {
  color: #64748b;
  margin: 0 0 8px;
  font-size: 15px;
}

.result-empty p {
  font-size: 13px;
  margin: 0;
  line-height: 1.6;
}

/* ── 内容区 ── */
.result-content {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.section {
  background: #f8fafc;
  border-radius: 10px;
  padding: 14px;
  border: 1px solid #f1f5f9;
  animation: fadeInUp 0.4s ease;
}

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

.section-header {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 10px;
}

.section-body {
  font-size: 13px;
  color: #374151;
}

.subsection {
  margin-top: 8px;
}

.subsection label {
  display: block;
  font-size: 12px;
  font-weight: 500;
  color: #6b7280;
  margin-bottom: 4px;
}

.tag-group {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.symptom-tag, .condition-tag, .med-tag {
  border-radius: 6px !important;
}

/* ── 分诊 ── */
.triage-section {
  border-left: 4px solid;
}

.urgency-low { border-left-color: #3b82f6; }
.urgency-medium { border-left-color: #f59e0b; }
.urgency-high { border-left-color: #f97316; }
.urgency-emergency { border-left-color: #ef4444; }

.urgency-tag {
  margin-left: auto;
}

.triage-action {
  margin: 0;
  line-height: 1.5;
}

.triage-specialty {
  display: flex;
  align-items: center;
  gap: 4px;
  margin: 6px 0 0;
  color: #6b7280;
  font-size: 12px;
}

/* ── 紧急警告 ── */
.emergency-warning {
  margin-top: 10px;
  padding: 8px 12px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 8px;
  color: #dc2626;
  font-size: 12px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 6px;
}

/* ── 诊断区 ── */
.diagnosis-section {
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
  border-color: #bae6fd;
}

.diagnosis-primary {
  margin-bottom: 10px;
}

.diagnosis-name {
  font-size: 16px;
  font-weight: 700;
  color: #0369a1;
  margin-bottom: 6px;
}

.confidence-bar {
  margin-bottom: 2px;
}

.confidence-label {
  font-size: 11px;
  color: #64748b;
}

.reasoning-text {
  line-height: 1.7;
  margin: 0;
  color: #475569;
}

.differential-list {
  margin: 4px 0 0;
  padding-left: 18px;
  color: #475569;
}

.differential-list li {
  margin-bottom: 2px;
}

/* ── 治疗 ── */
.action-label {
  display: flex !important;
  align-items: center;
  gap: 4px;
}

.action-list {
  margin: 4px 0 0;
  padding-left: 18px;
  line-height: 1.7;
}

.followup-text {
  margin: 4px 0 0;
  line-height: 1.5;
}

.treatment-collapse :deep(.el-collapse-item__header) {
  font-size: 13px;
  font-weight: 500;
  padding-left: 4px;
}

.treatment-collapse :deep(.el-collapse-item__content) {
  padding-bottom: 8px;
}

/* ── 参考区 ── */
.ref-section {
  background: #f8fafc;
}

.ref-item {
  padding: 8px;
  background: white;
  border-radius: 8px;
  border: 1px solid #f1f5f9;
  margin-top: 6px;
}

.ref-item:first-child {
  margin-top: 0;
}

.ref-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.ref-relevance {
  font-size: 11px;
  color: #94a3b8;
  margin-left: auto;
}

.ref-text {
  margin: 6px 0 0;
  font-size: 12px;
  color: #64748b;
  line-height: 1.5;
}

.graphrag-badge {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  font-size: 11px;
  color: #94a3b8;
  padding: 6px;
}

/* ── 免责 ── */
.disclaimer-alert {
  margin-top: 4px;
}

.disclaimer-alert :deep(.el-alert__title) {
  font-size: 13px;
}

.disclaimer-alert :deep(.el-alert__description) {
  font-size: 12px;
}
</style>
