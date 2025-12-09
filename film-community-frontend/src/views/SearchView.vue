<template>
    <div class="search-view">
        <h1>智能搜索</h1>
        <p>搜索电影、演员、导演，发现隐藏的关系</p>

        <div class="search-container">
            <el-input v-model="searchKeyword" placeholder="输入电影名称、演员姓名..." size="large" @keyup.enter="handleSearch">
                <template #append>
                    <el-button @click="handleSearch" :icon="Search">搜索</el-button>
                </template>
            </el-input>
        </div>

        <div v-if="searchResults" class="results-section">
            <h3>搜索结果</h3>
            <div v-if="searchResults.length === 0" class="no-results">
                未找到相关结果
            </div>
            <div v-else class="results-grid">
                <!-- 这里显示搜索结果 -->
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref } from 'vue'
import { Search } from '@element-plus/icons-vue'

const searchKeyword = ref('')
const searchResults = ref(null)

const handleSearch = async () => {
    if (!searchKeyword.value.trim()) return

    // 这里调用搜索API
    console.log('搜索:', searchKeyword.value)
    // searchResults.value = await searchAPI(searchKeyword.value)
}
</script>

<style scoped>
.search-view {
    padding: 20px;
    max-width: 800px;
    margin: 0 auto;
}

.search-view h1 {
    text-align: center;
    margin-bottom: 10px;
}

.search-view p {
    text-align: center;
    color: #606266;
    margin-bottom: 40px;
}

.search-container {
    margin-bottom: 40px;
}

.no-results {
    text-align: center;
    padding: 40px;
    color: #909399;
}
</style>