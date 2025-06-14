<template>
    <el-container class="main-container">
        <el-header height="60px">
            <common-header></common-header>
        </el-header>
        <el-container class="main-content">
            <el-aside :width="asideWidth">
                <common-aside></common-aside>
            </el-aside>
            <el-main>
                <router-view></router-view>
            </el-main>
        </el-container>
    </el-container>
</template>


<script>
import CommonAside from "@/components/CommonAside.vue";
import CommonHeader from '@/components/CommonHeader.vue';

export default {
    name: 'MainPage',
    components: {
        CommonAside,
        CommonHeader,
    },
    data() {
        return {
            isCollapse: false
        };
    },
    computed: {
        asideWidth() {
            return this.isCollapse ? '64px' : '200px'
        }
    },
    methods: {},
};

</script>

<style scoped>
.main-container {
    height: 100vh;
    background-color: #f0f2f5;
}

.main-content {
    height: calc(100vh - 60px);
    overflow: hidden;
}

.el-header {
    padding: 0;
    box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
    z-index: 10;
}

.el-aside {
    background-color: #001529;
    transition: width 0.3s;
    overflow: hidden;
}

.el-main {
    padding: 20px;
    overflow-y: auto;
    background-color: #f0f2f5;
}

/* 自定义滚动条样式 */
.el-main::-webkit-scrollbar {
    width: 6px;
    height: 6px;
}

.el-main::-webkit-scrollbar-thumb {
    background: #ccc;
    border-radius: 3px;
}

.el-main::-webkit-scrollbar-track {
    background: #f0f2f5;
}
</style>