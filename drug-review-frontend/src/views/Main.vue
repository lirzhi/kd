<template>
    <el-container class="app-wrapper">
        <el-aside width="240px" class="sidebar-container">
            <common-aside />
        </el-aside>

        <el-container class="main-container">
            <common-header />

            <el-main class="app-main">
                <router-view />
            </el-main>
        </el-container>
    </el-container>
</template>

<script>
import CommonAside from '@/components/CommonAside.vue'
import CommonHeader from '@/components/CommonHeader.vue'

export default {
    name: 'MainPage',
    components: {
        CommonAside,
        CommonHeader
    }
}
</script>

<style lang="scss" scoped>
.app-wrapper {
    height: 100vh;
    width: 100%;
}

.sidebar-container {
    background-color: #304156;
    height: 100%;
    transition: width 0.28s;
    overflow: hidden;
}

.main-container {
    height: 100%;
    display: flex;
    flex-direction: column;
}

.app-main {
    padding: 20px;
    background-color: #f0f2f5;
    height: calc(100vh - 60px);
    overflow-y: auto;
}
</style>