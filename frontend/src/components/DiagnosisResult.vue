<template>
  <el-card shadow="hover" style="height: 100%; overflow-y: auto">
    <template #header>
      <span><el-icon><Document /></el-icon> 诊断结果</span>
    </template>

    <div v-if="!result" style="text-align: center; color: #c0c4cc; padding-top: 80px">
      <el-icon :size="48"><Stethoscope /></el-icon>
      <p>暂无诊断结果</p>
      <p style="font-size: 12px">请通过左侧聊天面板发起智能诊断。</p>
    </div>

    <div v-else style="display: flex; flex-direction: column; gap: 16px">
      <!-- Triage -->
      <el-alert
        v-if="result.triage"
        :title="'分诊评估: ' + urgencyLabel(result.triage.urgency)"
        :description="result.triage.recommended_action"
        :type="urgencyType(result.triage.urgency)"
        show-icon
        :closable="false"
      />

      <!-- Symptom Analysis -->
      <div v-if="result.symptom_analysis">
        <h4 style="margin: 0 0 8px">关键症状</h4>
        <div style="display: flex; flex-wrap: wrap; gap: 4px">
          <el-tag
            v-for="s in result.symptom_analysis.key_symptoms"
            :key="s"
            size="small"
            type="info"
          >{{ s }}</el-tag>
        </div>
        <div v-if="result.symptom_analysis.possible_conditions?.length" style="margin-top: 8px">
          <h4 style="margin: 0 0 4px">可能的疾病</h4>
          <el-tag
            v-for="c in result.symptom_analysis.possible_conditions"
            :key="c"
            size="small"
            type="warning"
            style="margin: 2px"
          >{{ c }}</el-tag>
        </div>
      </div>

      <!-- Diagnosis -->
      <div v-if="result.diagnosis" style="background: #f0f9ff; padding: 12px; border-radius: 8px; border-left: 3px solid #409eff">
        <h4 style="margin: 0 0 8px; color: #409eff">初步诊断</h4>
        <p style="font-size: 15px; font-weight: bold">{{ result.diagnosis.primary_diagnosis }}</p>
        <p style="font-size: 12px; color: #909399">置信度: {{ confidenceLabel(result.diagnosis.confidence) }}</p>
        <p style="font-size: 13px; color: #606266">{{ result.diagnosis.reasoning }}</p>

        <div v-if="result.diagnosis.differential_diagnoses?.length" style="margin-top: 8px">
          <h4 style="margin: 0 0 4px; font-size: 13px">鉴别诊断</h4>
          <ul style="margin: 0; padding-left: 20px; font-size: 13px">
            <li v-for="d in result.diagnosis.differential_diagnoses" :key="d">{{ d }}</li>
          </ul>
        </div>
      </div>

      <!-- Treatment -->
      <div v-if="result.treatment">
        <h4 style="margin: 0 0 8px">治疗建议</h4>
        <el-collapse>
          <el-collapse-item title="紧急措施" name="1">
            <ul style="margin: 0; padding-left: 20px">
              <li v-for="a in result.treatment.immediate_actions" :key="a">{{ a }}</li>
            </ul>
          </el-collapse-item>
          <el-collapse-item v-if="result.treatment.medications?.length" title="参考用药" name="2">
            <el-tag v-for="m in result.treatment.medications" :key="m" size="small" style="margin: 2px">{{ m }}</el-tag>
          </el-collapse-item>
          <el-collapse-item v-if="result.treatment.lifestyle_recommendations?.length" title="生活方式建议" name="3">
            <ul style="margin: 0; padding-left: 20px">
              <li v-for="r in result.treatment.lifestyle_recommendations" :key="r">{{ r }}</li>
            </ul>
          </el-collapse-item>
          <el-collapse-item title="随访建议" name="4">
            <p style="font-size: 13px">{{ result.treatment.follow_up }}</p>
          </el-collapse-item>
        </el-collapse>
      </div>

      <!-- References -->
      <div v-if="result.references?.length">
        <h4 style="margin: 0 0 8px">医学知识参考</h4>
        <div v-for="ref in result.references" :key="ref.source" style="font-size: 12px; margin-bottom: 8px; padding: 8px; background: #f5f7fa; border-radius: 4px">
          <el-tag size="small" type="success" style="margin-bottom: 4px">{{ ref.source }}</el-tag>
          <span style="color: #909399; margin-left: 4px">相关度: {{ (ref.relevance * 100).toFixed(0) }}%</span>
          <p style="margin: 4px 0 0; color: #606266">{{ ref.content?.substring(0, 200) }}...</p>
        </div>
      </div>

      <!-- Disclaimer -->
      <el-alert
        type="warning"
        :closable="false"
        show-icon
        title="医疗免责声明"
        description="本系统生成的医疗信息仅供参考，不构成医疗建议。请务必咨询持牌医疗专业人士获取实际诊疗意见。"
        style="margin-top: 8px"
      />
    </div>
  </el-card>
</template>

<script setup>
defineProps({
  result: { type: Object, default: null },
})

function urgencyType(level) {
  const map = { low: 'info', medium: 'warning', high: 'danger', emergency: 'danger' }
  return map[level] || 'info'
}

function urgencyLabel(level) {
  const map = { low: '低风险', medium: '中等风险', high: '高风险', emergency: '紧急' }
  return map[level] || level
}

function confidenceLabel(level) {
  const map = { low: '低', moderate: '中等', high: '高' }
  return map[level] || level
}
</script>
