<template>
  <div id="app">
    <el-container style="height: 100vh">
      <el-header style="background: #409eff; color: white; display: flex; align-items: center; padding: 0 20px">
        <h2 style="margin: 0">医疗诊断多智能体系统</h2>
        <el-tag style="margin-left: 12px" type="warning" size="small">AI 驱动</el-tag>
      </el-header>
      <el-main style="background: #f5f7fa; padding: 20px">
        <HomePage />
      </el-main>
    </el-container>
  </div>
</template>

<script setup>
import HomePage from './views/Home.vue'
</script>

<style>
body {
  margin: 0;
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Microsoft YaHei', sans-serif;
}
#app {
  height: 100vh;
}
</style>
