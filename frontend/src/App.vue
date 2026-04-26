<template>
  <div id="app">
    <el-container style="min-height: 100vh">
      <!-- 渐变医疗主题头部 -->
      <el-header class="app-header">
        <div class="header-content">
          <div class="header-left">
            <div class="logo-icon">
              <svg viewBox="0 0 24 24" width="28" height="28" fill="currentColor">
                <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-1 9h-4v4h-2v-4H8v-2h4V6h2v4h4v2z"/>
              </svg>
            </div>
            <div class="header-title">
              <h2>医疗诊断多智能体系统</h2>
              <span class="header-subtitle">AI 驱动的辅助诊断平台</span>
            </div>
          </div>
          <div class="header-right">
            <el-tag class="ai-badge" effect="dark" size="small">
              <span class="badge-dot"></span>
              AI 驱动
            </el-tag>
          </div>
        </div>
      </el-header>
      <el-main class="app-main">
        <HomePage />
      </el-main>
    </el-container>
  </div>
</template>

<script setup>
import HomePage from './views/Home.vue'
</script>

<style>
/* ── 全局样式 ── */
* {
  box-sizing: border-box;
}

body {
  margin: 0;
  font-family: 'Inter', 'Helvetica Neue', 'PingFang SC', 'Microsoft YaHei', -apple-system, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  background: #f0f2f5;
}

#app {
  min-height: 100vh;
}

/* ── 头部样式 ── */
.app-header {
  background: linear-gradient(135deg, #0d9488 0%, #0891b2 100%);
  color: white;
  padding: 0 32px !important;
  height: 64px !important;
  box-shadow: 0 2px 12px rgba(13, 148, 136, 0.3);
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 100%;
  max-width: 1600px;
  margin: 0 auto;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 14px;
}

.logo-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 42px;
  height: 42px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 10px;
  backdrop-filter: blur(4px);
}

.header-title h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  letter-spacing: 0.5px;
}

.header-subtitle {
  font-size: 12px;
  opacity: 0.8;
  display: block;
  margin-top: 1px;
}

.header-right {
  display: flex;
  align-items: center;
}

.ai-badge {
  background: rgba(255, 255, 255, 0.25) !important;
  border: 1px solid rgba(255, 255, 255, 0.3) !important;
  color: white !important;
  font-size: 12px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.badge-dot {
  width: 6px;
  height: 6px;
  background: #4ade80;
  border-radius: 50%;
  display: inline-block;
  animation: pulse-dot 2s ease-in-out infinite;
}

@keyframes pulse-dot {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

/* ── 主内容区 ── */
.app-main {
  padding: 20px 24px;
  max-width: 1600px;
  margin: 0 auto;
  min-height: calc(100vh - 64px);
}

/* ── Element Plus 自定义 ── */
.el-card {
  border-radius: 12px !important;
  border: 1px solid #e8eaed !important;
  transition: box-shadow 0.3s ease, transform 0.2s ease !important;
}

.el-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08) !important;
}

.el-card__header {
  border-bottom: 1px solid #f0f0f0 !important;
  padding: 14px 20px !important;
  font-weight: 600;
  font-size: 14px;
  color: #1f2937;
}

.el-card__body {
  padding: 18px 20px !important;
}

/* 滚动条 */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: #d1d5db;
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: #9ca3af;
}
</style>
