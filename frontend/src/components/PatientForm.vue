<template>
  <el-card shadow="never" class="patient-card">
    <template #header>
      <div class="card-header">
        <el-icon><UserFilled /></el-icon>
        <span>患者信息</span>
        <el-tag v-if="isFilled" size="small" type="success" effect="plain" class="filled-tag">已填写</el-tag>
      </div>
    </template>
    <el-form label-position="top" size="small" class="patient-form">
      <el-form-item label="年龄">
        <el-input-number
          :model-value="modelValue?.age"
          @update:model-value="update('age', $event)"
          :min="0"
          :max="150"
          style="width: 100%"
          controls-position="right"
          placeholder="输入年龄"
        />
      </el-form-item>
      <el-form-item label="性别">
        <el-select
          :model-value="modelValue?.gender"
          @update:model-value="update('gender', $event)"
          clearable
          style="width: 100%"
          placeholder="请选择"
        >
          <el-option label="男" value="male">
            <el-icon><Male /></el-icon> 男
          </el-option>
          <el-option label="女" value="female">
            <el-icon><Female /></el-icon> 女
          </el-option>
          <el-option label="其他" value="other" />
        </el-select>
      </el-form-item>
      <el-form-item label="既往病史">
        <el-input
          :model-value="modelValue?.medical_history"
          @update:model-value="update('medical_history', $event)"
          type="textarea"
          :rows="2"
          placeholder="如：高血压、糖尿病等"
          maxlength="500"
          show-word-limit
        />
      </el-form-item>
      <el-form-item label="当前用药">
        <el-input
          :model-value="modelValue?.current_medications"
          @update:model-value="update('current_medications', $event)"
          placeholder="如：二甲双胍 500mg"
          maxlength="200"
          show-word-limit
        />
      </el-form-item>
    </el-form>
  </el-card>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  modelValue: { type: Object, default: null },
})

const emit = defineEmits(['update:modelValue'])

const isFilled = computed(() => {
  const v = props.modelValue
  return v && (v.age !== undefined || v.gender || v.medical_history || v.current_medications)
})

function update(field, value) {
  const current = { ...(props.modelValue || {}) }
  if (value === '' || value === null || value === undefined) {
    delete current[field]
  } else {
    current[field] = value
  }
  emit('update:modelValue', Object.keys(current).length > 0 ? current : null)
}
</script>

<style scoped>
.patient-card {
  background: linear-gradient(135deg, #ffffff 0%, #fafcff 100%);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
}

.filled-tag {
  margin-left: auto;
}

.patient-form :deep(.el-form-item) {
  margin-bottom: 16px;
}

.patient-form :deep(.el-form-item__label) {
  font-size: 13px;
  font-weight: 500;
  color: #374151;
  padding-bottom: 4px;
}

.patient-form :deep(.el-input-number .el-input-number__decrease),
.patient-form :deep(.el-input-number .el-input-number__increase) {
  border-radius: 6px;
}

.patient-form :deep(.el-textarea__inner),
.patient-form :deep(.el-input__wrapper) {
  border-radius: 8px;
}

.patient-form :deep(.el-textarea__inner:focus),
.patient-form :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px #0d9488 inset;
}
</style>
