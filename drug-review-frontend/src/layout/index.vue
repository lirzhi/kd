<template>
  <div class="app-wrapper">
    <!-- 头部栏 -->
    <div class="navbar">
      <div class="navbar-left">
        <span class="system-title">人工智能辅助审评工具</span>
      </div>
      <div class="navbar-right">
        <el-dropdown trigger="click">
          <span class="el-dropdown-link">
            <el-avatar :size="32" icon="el-icon-user"></el-avatar>
            <span style="margin: 0 8px;">管理员</span>
            <i class="el-icon-arrow-down el-icon--right"></i>
          </span>
          <el-dropdown-menu slot="dropdown">
            <el-dropdown-item>个人信息</el-dropdown-item>
            <el-dropdown-item>修改密码</el-dropdown-item>
            <el-dropdown-item divided @click.native="logout">退出登录</el-dropdown-item>
          </el-dropdown-menu>
        </el-dropdown>
      </div>
    </div>
    <!-- 主体部分 -->
    <el-container class="main-layout">
      <el-aside width="210px" class="sidebar-container">
        <el-menu
          :default-active="$route.path"
          class="el-menu-vertical"
          :collapse="isCollapse"
          background-color="#304156"
          text-color="#bfcbd9"
          active-text-color="#409EFF"
          router
        >
          <el-submenu index="/knowledge">
            <template slot="title">
              <i class="el-icon-s-management"></i>
              <span>知识库管理</span>
            </template>
            <el-menu-item index="/knowledge/laws">法律法规</el-menu-item>
            <el-menu-item index="/knowledge/guidence">指导原则</el-menu-item>
            <el-menu-item index="/knowledge/regulations">制度规范</el-menu-item>
            <el-menu-item index="/knowledge/qa">问答数据</el-menu-item>
            <el-menu-item index="/knowledge/pharmacy">药典数据</el-menu-item>
            <el-menu-item index="/knowledge/rules">审评规则</el-menu-item>
          </el-submenu>
          <el-submenu index="/project">
            <template slot="title">
              <i class="el-icon-s-order"></i>
              <span>审评项目管理</span>
            </template>
            <el-menu-item index="/project/documents">审评项目</el-menu-item>
          </el-submenu>
        </el-menu>
      </el-aside>
      <el-main class="app-main">
        <router-view />
      </el-main>
    </el-container>
  </div>
</template>

<script>
import Breadcrumb from '@/components/Breadcrumb'

export default {
  name: 'MainLayout',
  components: {
    Breadcrumb
  },
  data() {
    return {
      isCollapse: false
    }
  },
  methods: {
    toggleSideBar() {
      this.isCollapse = !this.isCollapse
    },
    async logout() {
      try {
        await this.$confirm('确认退出登录吗？', '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })
        
        // 清除token
        localStorage.removeItem('token')
        // 跳转到登录页
        this.$router.push('/login')
      } catch (error) {
        // 取消退出
      }
    }
  }
}
</script>

<style lang="scss" scoped>
/* 让body、html、#app、.app-wrapper都100% */
html, body, #app, .app-wrapper {
  height: 100%;
  width: 100%;
  margin: 0;
  padding: 0;
  background: #f0f2f5;
  overflow: hidden;
}

.app-wrapper {
  min-height: 100vh;
  min-width: 100vw;
  overflow: hidden;
}

.navbar {
  height: 60px;
  width: 100%;
  background: linear-gradient(to right, #1890ff, #36cfc9);
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 30px;
  z-index: 1002;
  position: fixed;
  top: 0;
  left: 0;
}

.navbar-left {
  display: flex;
  align-items: center;
}
.system-title {
  font-size: 20px;
  font-weight: 600;
  color: #fff;
  letter-spacing: 1px;
}
.navbar-right {
  display: flex;
  align-items: center;
}
.el-dropdown-link {
  display: flex;
  align-items: center;
  cursor: pointer;
  color: #fff;
  i {
    margin-right: 5px;
  }
}

.main-layout {
  position: absolute;
  top: 60px;
  left: 0;
  right: 0;
  bottom: 0;
  height: calc(100vh - 60px);
  width: 100vw;
  overflow: hidden;
}

.sidebar-container {
  background-color: #304156;
  height: 100%;
  overflow: hidden;
}

.el-menu-vertical {
  height: 100%;
  border: none;
}

.app-main {
  padding: 20px;
  background-color: #f0f2f5;
  height: 100%;
  min-height: 100%;
  overflow: hidden;
}
</style> 