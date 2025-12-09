<template>
    <el-header class="app-header">
        <div class="header-content">
            <div class="logo" @click="$router.push('/')">
                🎬 电影知识图谱
            </div>

            <el-menu mode="horizontal" :default-active="activeIndex" router class="nav-menu">
                <el-menu-item index="/">首页</el-menu-item>
                <el-menu-item index="/network">关系探索</el-menu-item>
                <!-- <el-menu-item index="/search">智能搜索</el-menu-item> -->
                <el-menu-item index="/movies">电影列表</el-menu-item>
                <el-menu-item index="/recommendations">智能推荐</el-menu-item>
            </el-menu>
        </div>
    </el-header>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const activeIndex = computed(() => route.path)
</script>

<style scoped>
.app-header {
    background: #fff;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    padding: 0 20px;
}

.header-content {
    display: flex;
    align-items: center;
    justify-content: space-between;
    max-width: 1200px;
    margin: 0 auto;
    height: 100%;
}

.logo {
    font-size: 1.5rem;
    font-weight: bold;
    color: #409EFF;
    cursor: pointer;
}

.nav-menu {
    border-bottom: none;
}

:deep(.el-menu--horizontal > .el-menu-item) {
    height: 60px;
    line-height: 60px;
}
</style>