<template>
  <el-menu
    :default-active="activeMenu"
    class="el-menu-vertical"
    :collapse="isCollapse"
    background-color="#304156"
    text-color="#bfcbd9"
    active-text-color="#409EFF"
    router
    unique-opened
  >
    <div class="logo-container">
      <img src="../assets/logo.png" alt="Logo" class="logo-img">
      <span class="logo-text" v-show="!isCollapse">药品审评系统</span>
    </div>
    
    <el-menu-item index="/knowledge">
      <i class="el-icon-document"></i>
      <span slot="title">知识库管理</span>
    </el-menu-item>

    <el-menu-item index="/ctd">
      <i class="el-icon-folder"></i>
      <span slot="title">审评文件管理</span>
    </el-menu-item>

    <el-menu-item index="/requirements">
      <i class="el-icon-notebook-2"></i>
      <span slot="title">审评要求</span>
    </el-menu-item>

    <el-menu-item index="/report">
      <i class="el-icon-s-order"></i>
      <span slot="title">审评报告</span>
    </el-menu-item>
  </el-menu>
</template>

<script>
export default {
  name: 'CommonAside',
  data() {
    return {
      isCollapse: false,
      activeMenu: this.$route.path
    }
  },
  watch: {
    $route: {
      handler(route) {
        this.activeMenu = route.path
      },
      immediate: true
    }
  }
}
</script>

<style scoped>
.el-menu-vertical {
  height: 100%;
  border-right: none;
}

.el-menu-vertical:not(.el-menu--collapse) {
  width: 240px;
}

.logo-container {
  height: 60px;
  padding: 10px;
  display: flex;
  align-items: center;
  background: #2b3649;
  overflow: hidden;
}

.logo-img {
  width: 32px;
  height: 32px;
  margin-right: 12px;
}

.logo-text {
  color: #fff;
  font-size: 16px;
  font-weight: 600;
  white-space: nowrap;
}

.el-menu-item {
  height: 50px;
  line-height: 50px;
}

.el-menu-item i {
  margin-right: 5px;
  width: 24px;
  text-align: center;
  font-size: 18px;
}

.el-menu-item.is-active {
  background-color: #263445 !important;
}

.el-menu-item:hover {
  background-color: #263445 !important;
}
</style>