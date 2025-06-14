<template>
  <div id="app">
      <router-view></router-view>
  </div>
</template>


<script>
export default {
  name: 'App',
}
</script>

<style>
html, body {
  margin: 0;
  padding: 0;
  height: 100%;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'Noto Sans', sans-serif;
}

#app {
  height: 100%;
}

/* 全局过渡动画 */
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s;
}

.fade-enter, .fade-leave-to {
  opacity: 0;
}

/* 全局卡片样式 */
.el-card {
  border-radius: 4px;
  border: none;
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  transition: all 0.3s;
}

.el-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

/* 全局按钮样式 */
.el-button {
  border-radius: 4px;
  font-weight: 500;
}

.el-button--primary {
  background: linear-gradient(to right, #1890ff, #36cfc9);
  border: none;
}

.el-button--primary:hover {
  background: linear-gradient(to right, #40a9ff, #5cdbd3);
}

/* 全局表格样式 */
.el-table {
  border-radius: 4px;
  overflow: hidden;
}

.el-table th {
  background-color: #fafafa !important;
  font-weight: 600;
}

/* 全局表单样式 */
.el-form-item__label {
  font-weight: 500;
}

/* 全局对话框样式 */
.el-dialog {
  border-radius: 8px;
  overflow: hidden;
}

.el-dialog__header {
  padding: 20px;
  border-bottom: 1px solid #f0f0f0;
}

.el-dialog__body {
  padding: 24px;
}

/* 全局加载样式 */
.el-loading-mask {
  background-color: rgba(255, 255, 255, 0.8);
}

/* 全局消息提示样式 */
.el-message {
  min-width: 300px;
  border-radius: 4px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.main-wrapper {
  height: 100vh;
}

.system-header {
  background-color: #409EFF;
  color: white;
  line-height: 60px;
  padding: 0 20px;
}

.system-title {
  font-size: 20px;
  font-weight: bold;
}

.content-wrapper {
  height: calc(100vh - 60px);
}

.nav-sidebar {
  background-color: #f5f7fa;
  border-right: solid 1px #e6e6e6;
}

.menu-container {
  border-right: none;
}

.main-content {
  padding: 20px;
  background-color: #fff;
}
</style>
