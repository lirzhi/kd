<template>
  <div class="common-header">
    <div class="left">
      <div class="logo">
        <img src="@/assets/logo.png" alt="Logo" class="logo-img">
        <span class="system-title">药品审评系统</span>
      </div>
    </div>
    <div class="right">
      <el-dropdown trigger="click">
        <span class="user-info">
          <el-avatar :size="32" icon="el-icon-user"></el-avatar>
          <span class="username">管理员</span>
          <i class="el-icon-arrow-down"></i>
        </span>
        <el-dropdown-menu slot="dropdown">
          <el-dropdown-item>个人信息</el-dropdown-item>
          <el-dropdown-item>修改密码</el-dropdown-item>
          <el-dropdown-item divided>退出登录</el-dropdown-item>
        </el-dropdown-menu>
      </el-dropdown>
    </div>
  </div>
</template>

<script>
export default {
  name: 'CommonHeader',
  data() {
    return {
      username: '管理员'
    }
  }
}
</script>

<style scoped>
.common-header {
  height: 60px;
  background: linear-gradient(to right, #1890ff, #36cfc9);
  color: white;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.left {
  display: flex;
  align-items: center;
}

.logo {
  display: flex;
  align-items: center;
  cursor: pointer;
}

.logo-img {
  height: 32px;
  margin-right: 12px;
}

.system-title {
  font-size: 20px;
  font-weight: 600;
  letter-spacing: 1px;
}

.right {
  display: flex;
  align-items: center;
}

.user-info {
  display: flex;
  align-items: center;
  cursor: pointer;
  padding: 0 8px;
  height: 48px;
  border-radius: 24px;
  transition: all 0.3s;
}

.user-info:hover {
  background: rgba(255, 255, 255, 0.1);
}

.username {
  margin: 0 8px;
  font-size: 14px;
}

.el-icon-arrow-down {
  font-size: 12px;
}
</style>
