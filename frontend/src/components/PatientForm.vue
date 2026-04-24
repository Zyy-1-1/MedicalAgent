<template>
  <el-card shadow="hover">
    <template #header>
      <span><el-icon><User /></el-icon> 患者信息</span>
    </template>
    <el-form label-position="top" size="small">
      <el-form-item label="年龄">
        <el-input-number
          :model-value="modelValue?.age"
          @update:model-value="update('age', $event)"
          :min="0"
          :max="150"
          style="width: 100%"
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
          <el-option label="男" value="male" />
          <el-option label="女" value="female" />
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
        />
      </el-form-item>
      <el-form-item label="当前用药">
        <el-input
          :model-value="modelValue?.current_medications"
          @update:model-value="update('current_medications', $event)"
          placeholder="如：二甲双胍 500mg"
        />
      </el-form-item>
    </el-form>
  </el-card>
</template>

<script setup>
const props = defineProps({
  modelValue: { type: Object, default: null },
})

const emit = defineEmits(['update:modelValue'])

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
