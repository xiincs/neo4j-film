<template>
    <div class="movies-view">
        <h1>电影列表</h1>
        <p>浏览完整的电影数据库</p>

        <div class="loading" v-if="loading">
            <el-icon class="is-loading">
                <Loading />
            </el-icon>
            加载中...
        </div>

        <div v-else>
            <div v-if="movies.length === 0" class="empty-state">
                <p>暂无电影数据</p>
            </div>
            <div v-else>
                <div class="movies-grid">
                    <el-card v-for="movie in movies" :key="movie.id" class="movie-card" shadow="hover">
                        <div class="movie-content">
                            <h3>{{ movie.title }}</h3>
                            <p v-if="movie.year">年份: {{ movie.year }}</p>
                            <p v-if="movie.genres">类型: {{ movie.genres }}</p>
                            <el-button type="primary" size="small" @click="$router.push(`/network/movie/${movie.id}`)">
                                查看关系
                            </el-button>
                        </div>
                    </el-card>
                </div>
                
                <div class="pagination-container">
                    <el-pagination
                        v-model:current-page="currentPage"
                        v-model:page-size="pageSize"
                        :page-sizes="[12, 24, 48, 96]"
                        :total="totalMovies"
                        layout="total, sizes, prev, pager, next, jumper"
                        @size-change="handleSizeChange"
                        @current-change="handlePageChange"
                    />
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Loading } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const loading = ref(true)
const movies = ref([])
const currentPage = ref(1)
const pageSize = ref(24)
const totalMovies = ref(0)

// 获取电影总数
const fetchMovieCount = async () => {
    try {
        const response = await fetch('http://localhost:8000/api/movies/count')
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`)
        }
        const data = await response.json()
        if (data.error) {
            throw new Error(data.error)
        }
        totalMovies.value = data.count || 0
    } catch (error) {
        console.error('获取电影总数失败:', error)
    }
}

// 加载电影数据
const loadMovies = async () => {
    try {
        loading.value = true
        const skip = (currentPage.value - 1) * pageSize.value
        const response = await fetch(
            `http://localhost:8000/api/movies?limit=${pageSize.value}&skip=${skip}`
        )
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`)
        }
        
        const data = await response.json()
        
        // 检查是否有错误
        if (data.error) {
            throw new Error(data.error)
        }
        
        movies.value = data
    } catch (error) {
        console.error('加载电影数据失败:', error)
        ElMessage.error('加载电影数据失败: ' + error.message)
        movies.value = []
    } finally {
        loading.value = false
    }
}

// 每页数量改变
const handleSizeChange = (newSize) => {
    pageSize.value = newSize
    currentPage.value = 1 // 重置到第一页
    loadMovies()
}

// 页码改变
const handlePageChange = (newPage) => {
    currentPage.value = newPage
    loadMovies()
    // 滚动到顶部
    window.scrollTo({ top: 0, behavior: 'smooth' })
}

onMounted(async () => {
    // 先获取总数
    await fetchMovieCount()
    // 然后加载第一页数据
    await loadMovies()
})
</script>

<style scoped>
.movies-view {
    padding: 20px;
    max-width: 1200px;
    margin: 0 auto;
}

.movies-view h1 {
    text-align: center;
    margin-bottom: 10px;
}

.movies-view p {
    text-align: center;
    color: #606266;
    margin-bottom: 40px;
}

.loading {
    text-align: center;
    padding: 40px;
    color: #409EFF;
}

.movies-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 20px;
}

.movie-card {
    cursor: pointer;
}

.movie-content {
    padding: 15px;
}

.movie-content h3 {
    margin-bottom: 10px;
    color: #303133;
}

.movie-content p {
    margin: 5px 0;
    color: #606266;
    font-size: 0.9rem;
}

.empty-state {
    text-align: center;
    padding: 60px 20px;
    color: #909399;
}

.pagination-container {
    margin-top: 40px;
    display: flex;
    justify-content: center;
    padding: 20px 0;
}
</style>