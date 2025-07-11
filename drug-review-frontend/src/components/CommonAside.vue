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
    <!-- 知识库管理菜单 -->
    <el-submenu index="/knowledge">
      <template slot="title">
        <i class="el-icon-s-management"></i>
        <span>知识库管理</span>
      </template>
      <el-menu-item index="/knowledge/list">
        <i class="el-icon-document"></i>
        <span slot="title">基本知识管理</span>
      </el-menu-item>
      <el-menu-item index="/knowledge/rules">
        <i class="el-icon-s-order"></i>
        <span slot="title">审评规则管理</span>
      </el-menu-item>
    </el-submenu>

    <!-- 审评项目管理菜单 -->
    <el-submenu index="/project">
      <template slot="title">
        <i class="el-icon-s-order"></i>
        <span>审评项目管理</span>
      </template>
      <el-menu-item index="/project/documents">
        <i class="el-icon-document"></i>
        <span slot="title">审评资料</span>
      </el-menu-item>
    </el-submenu>
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
  padding-top: 0;
}

.el-menu-vertical:not(.el-menu--collapse) {
  width: 240px;
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

.el-submenu .el-menu-item {
  min-width: 180px;
}

.el-menu-item.is-active {
  background-color: #263445 !important;
}

.el-menu-item:hover {
  background-color: #263445 !important;
}

.el-submenu__title:hover {
  background-color: #263445 !important;
}
</style>