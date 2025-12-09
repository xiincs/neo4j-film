<template>
    <div class="recommendations-view">
        <h1>智能推荐</h1>
        <p>基于知识图谱的个性化电影推荐</p>

        <div class="user-input-section">
            <div class="search-user-container" style="position: relative;">
                <el-input 
                    v-model="userSearchQuery" 
                    placeholder="搜索用户ID..." 
                    style="width: 400px;"
                    @input="handleUserSearch"
                    @keyup.enter="handleEnterKey"
                    clearable>
                    <template #append>
                        <el-button 
                            type="primary" 
                            @click="getRecommendations" 
                            :loading="loading"
                            :disabled="!userId"
                            :icon="Search">
                            获取推荐
                        </el-button>
                    </template>
                </el-input>
                <div v-if="userSearchResults.length > 0 && showUserSearchResults" class="user-search-results">
                    <div 
                        v-for="user in userSearchResults" 
                        :key="user.id"
                        class="user-result-item"
                        @click="selectUser(user)">
                        <div class="user-name">{{ user.name }}</div>
                        <div class="user-info" v-if="user.rating_count">
                            评分: {{ user.rating_count }} 部电影
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div v-if="loading" class="loading-section">
            <el-icon class="is-loading" size="48">
                <Loading />
            </el-icon>
            <p>正在分析用户偏好，生成推荐...</p>
        </div>

        <div v-else-if="error" class="error-section">
            <el-alert :title="error" type="error" :closable="false" />
        </div>

        <div v-else-if="likedMovies.length > 0 || recommendations.length > 0" class="recommendations-content">
            <!-- 推理过程展示 -->
            <div v-if="reasoning" class="reasoning-section">
                <el-card shadow="hover">
                    <template #header>
                        <div class="card-header">
                            <el-icon><Connection /></el-icon>
                            <span>推荐推理过程</span>
                        </div>
                    </template>
                    
                    <div class="reasoning-content">
                        <!-- 用户偏好分析 -->
                        <div v-if="reasoning.genre_preferences && reasoning.genre_preferences.length > 0" class="preference-analysis">
                            <h3>📊 用户偏好分析</h3>
                            <p>根据您的高评分电影（≥4.0分），我们分析了您的类型偏好：</p>
                            <div class="genre-stats">
                                <el-tag 
                                    v-for="(pref, index) in reasoning.genre_preferences" 
                                    :key="index"
                                    :type="index < 3 ? 'success' : 'info'"
                                    size="large"
                                    style="margin: 5px;">
                                    {{ pref.genre }} ({{ pref.movie_count }}部, 平均{{ pref.avg_rating }}分)
                                </el-tag>
                            </div>
                        </div>

                        <!-- 相似用户 -->
                        <div v-if="reasoning.similar_users && reasoning.similar_users.length > 0" class="similar-users">
                            <h3>👥 相似用户发现</h3>
                            <p>我们找到了与您有相似偏好的用户：</p>
                            <div class="similar-users-list">
                                <el-tag 
                                    v-for="(user, index) in reasoning.similar_users" 
                                    :key="index"
                                    type="warning"
                                    size="large"
                                    style="margin: 5px;">
                                    用户 {{ user.user_id }} (共同评分 {{ user.common_movies }} 部电影)
                                </el-tag>
                            </div>
                        </div>

                        <!-- 推荐策略说明 -->
                        <div class="strategy-explanation">
                            <h3>🎯 推荐策略</h3>
                            <el-steps :active="3" finish-status="success" direction="vertical">
                                <el-step title="类型偏好推荐" description="基于您喜欢的电影类型，推荐同类型的高质量电影"></el-step>
                                <el-step title="相似用户推荐" description="找到与您有相似评分偏好的用户，推荐他们喜欢的电影"></el-step>
                                <el-step title="相似电影推荐" description="基于您喜欢的特定电影，推荐类型相似的电影"></el-step>
                            </el-steps>
                        </div>
                    </div>
                </el-card>
            </div>

            <!-- 用户喜欢的电影 -->
            <div v-if="likedMovies.length > 0" class="liked-movies-section">
                <h2>您喜欢的电影</h2>
                <div class="movies-grid">
                    <el-card 
                        v-for="movie in likedMovies" 
                        :key="movie.id" 
                        class="movie-card" 
                        shadow="hover">
                        <div class="movie-content">
                            <h3>{{ movie.title }}</h3>
                            <p v-if="movie.year">年份: {{ movie.year }}</p>
                            <p v-if="movie.genres">类型: {{ movie.genres }}</p>
                            <el-rate 
                                v-model="movie.rating" 
                                disabled 
                                show-score 
                                text-color="#ff9900"
                                score-template="{value}">
                            </el-rate>
                        </div>
                    </el-card>
                </div>
            </div>

            <!-- 推荐电影 -->
            <div v-if="recommendations.length > 0" class="recommendations-section">
                <h2>为您推荐 ({{ reasoning?.total_recommendations || recommendations.length }}部)</h2>
                <div class="movies-grid">
                    <el-card 
                        v-for="movie in recommendations" 
                        :key="movie.id" 
                        class="movie-card recommendation-card" 
                        shadow="hover">
                        <div class="movie-content">
                            <div class="recommendation-badge">
                                <el-tag 
                                    :type="movie.strategy === '类型偏好推荐' ? 'success' : movie.strategy === '相似用户推荐' ? 'warning' : 'info'"
                                    size="small">
                                    {{ movie.strategy }}
                                </el-tag>
                            </div>
                            <h3>{{ movie.title }}</h3>
                            <p v-if="movie.year">年份: {{ movie.year }}</p>
                            <p v-if="movie.genres">类型: {{ movie.genres }}</p>
                            
                            <!-- 推理详情 -->
                            <el-collapse v-if="movie.details" class="reasoning-details">
                                <el-collapse-item title="查看推理过程" :name="movie.id">
                                    <div class="reasoning-explanation">
                                        <p><strong>推荐策略：</strong>{{ movie.details.strategy }}</p>
                                        <p v-if="movie.details.explanation">{{ movie.details.explanation }}</p>
                                        <div v-if="movie.details.reason_genre" class="detail-item">
                                            <strong>偏好类型：</strong>{{ movie.details.reason_genre }}
                                        </div>
                                        <div v-if="movie.details.based_on_movie" class="detail-item">
                                            <strong>基于电影：</strong>{{ movie.details.based_on_movie }}
                                        </div>
                                        <div v-if="movie.details.common_movies" class="detail-item">
                                            <strong>共同评分：</strong>{{ movie.details.common_movies }} 部电影
                                        </div>
                                    </div>
                                </el-collapse-item>
                            </el-collapse>
                            
                            <el-button 
                                type="primary" 
                                size="small" 
                                style="margin-top: 10px;"
                                @click="$router.push(`/network/movie/${movie.id}`)">
                                查看关系
                            </el-button>
                        </div>
                    </el-card>
                </div>
            </div>
        </div>

        <div v-else-if="!loading && userId" class="empty-section">
            <el-empty description="未找到推荐内容，请尝试搜索其他用户" />
        </div>
    </div>
</template>

<script setup>
import { ref } from 'vue'
import { Search, Loading, Connection } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const userId = ref('')
const userSearchQuery = ref('')
const userSearchResults = ref([])
const showUserSearchResults = ref(false)
const loading = ref(false)
const error = ref('')
const likedMovies = ref([])
const recommendations = ref([])
const reasoning = ref(null)

let userSearchTimer = null

// 搜索用户
const handleUserSearch = async () => {
    const query = userSearchQuery.value.trim()
    if (query.length < 1) {
        userSearchResults.value = []
        showUserSearchResults.value = false
        return
    }
    
    clearTimeout(userSearchTimer)
    userSearchTimer = setTimeout(async () => {
        try {
            const response = await fetch(
                `http://localhost:8000/api/users/search?q=${encodeURIComponent(query)}&limit=5`
            )
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`)
            }
            
            const data = await response.json()
            
            if (data.error) {
                throw new Error(data.error)
            }
            
            userSearchResults.value = data
            showUserSearchResults.value = data.length > 0
        } catch (error) {
            console.error('搜索用户失败:', error)
            userSearchResults.value = []
            showUserSearchResults.value = false
        }
    }, 300)
}

// 选择用户
const selectUser = (user) => {
    userId.value = user.id
    userSearchQuery.value = user.name
    showUserSearchResults.value = false
    // 自动触发推荐
    getRecommendations()
}

// 处理回车键
const handleEnterKey = () => {
    // 如果只有一个搜索结果，自动选择
    if (userSearchResults.value.length === 1) {
        selectUser(userSearchResults.value[0])
    } else if (userId.value) {
        // 如果已经有用户ID，直接获取推荐
        getRecommendations()
    }
}

// 获取推荐
const getRecommendations = async () => {
    if (!userId.value.trim()) {
        ElMessage.warning('请输入用户ID')
        return
    }

    loading.value = true
    error.value = ''
    likedMovies.value = []
    recommendations.value = []

    try {
        // 获取用户喜欢的电影
        const likedResponse = await fetch(
            `http://localhost:8000/api/recommendations/user/${userId.value}/liked?limit=10&min_rating=4.0`
        )
        
        if (!likedResponse.ok) {
            throw new Error(`HTTP error! status: ${likedResponse.status}`)
        }
        
        const likedData = await likedResponse.json()
        if (likedData.error) {
            throw new Error(likedData.error)
        }
        likedMovies.value = likedData

        // 获取推荐
        const recResponse = await fetch(
            `http://localhost:8000/api/recommendations/user/${userId.value}?limit=20&min_rating=4.0`
        )
        
        if (!recResponse.ok) {
            throw new Error(`HTTP error! status: ${recResponse.status}`)
        }
        
        const recData = await recResponse.json()
        if (recData.error) {
            throw new Error(recData.error)
        }
        
        // 处理新的返回格式（包含推理过程）
        if (recData.recommendations && recData.reasoning) {
            recommendations.value = recData.recommendations
            reasoning.value = recData.reasoning
        } else {
            // 兼容旧格式
            recommendations.value = Array.isArray(recData) ? recData : []
            reasoning.value = null
        }

        if (recommendations.value.length === 0 && likedMovies.value.length === 0) {
            ElMessage.warning('该用户暂无评分数据或推荐内容')
        } else {
            ElMessage.success(`为您找到 ${recommendations.value.length} 部推荐电影`)
        }
    } catch (err) {
        console.error('获取推荐失败:', err)
        error.value = '获取推荐失败: ' + err.message
        ElMessage.error('获取推荐失败: ' + err.message)
    } finally {
        loading.value = false
    }
}

// 点击外部关闭搜索结果
const handleClickOutside = (event) => {
    const searchContainer = event.target.closest('.search-user-container')
    if (!searchContainer) {
        showUserSearchResults.value = false
    }
}

// 添加点击外部关闭搜索结果的事件监听
if (typeof document !== 'undefined') {
    document.addEventListener('click', handleClickOutside)
}
</script>

<style scoped>
.recommendations-view {
    padding: 20px;
    max-width: 1200px;
    margin: 0 auto;
}

.recommendations-view h1 {
    text-align: center;
    margin-bottom: 10px;
    color: #303133;
}

.recommendations-view p {
    text-align: center;
    color: #606266;
    margin-bottom: 40px;
}

.user-input-section {
    margin-bottom: 40px;
    padding: 20px;
    background: #f5f7fa;
    border-radius: 8px;
}

.input-group {
    display: flex;
    justify-content: center;
    align-items: center;
    margin-bottom: 10px;
}

.search-user-container {
    position: relative;
    display: flex;
    justify-content: center;
}

.user-search-results {
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    background: white;
    border: 1px solid #e4e7ed;
    border-radius: 4px;
    box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
    z-index: 1000;
    max-height: 200px;
    overflow-y: auto;
    margin-top: 5px;
    min-width: 400px;
}

.user-result-item {
    padding: 10px 15px;
    cursor: pointer;
    border-bottom: 1px solid #f0f0f0;
    transition: background-color 0.2s;
}

.user-result-item:hover {
    background-color: #f5f7fa;
}

.user-result-item:last-child {
    border-bottom: none;
}

.user-name {
    font-weight: 500;
    color: #303133;
    margin-bottom: 2px;
}

.user-info {
    font-size: 12px;
    color: #909399;
}

.loading-section {
    text-align: center;
    padding: 60px 20px;
    color: #409EFF;
}

.loading-section p {
    margin-top: 20px;
    color: #606266;
}

.error-section {
    margin: 20px 0;
}

.recommendations-content {
    margin-top: 40px;
}

.liked-movies-section,
.recommendations-section {
    margin-bottom: 50px;
}

.liked-movies-section h2,
.recommendations-section h2 {
    margin-bottom: 20px;
    color: #303133;
    font-size: 1.5rem;
}

.movies-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 20px;
}

.movie-card {
    cursor: pointer;
    transition: transform 0.3s ease;
}

.movie-card:hover {
    transform: translateY(-5px);
}

.movie-content {
    padding: 15px;
}

.recommendation-badge {
    margin-bottom: 10px;
}

.movie-content h3 {
    margin-bottom: 10px;
    color: #303133;
    font-size: 1.1rem;
}

.movie-content p {
    margin: 5px 0;
    color: #606266;
    font-size: 0.9rem;
    text-align: left;
}

.empty-section {
    margin-top: 60px;
}

.reasoning-section {
    margin-bottom: 40px;
}

.card-header {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 1.1rem;
    font-weight: 600;
    color: #303133;
}

.reasoning-content {
    padding: 10px 0;
}

.preference-analysis,
.similar-users,
.strategy-explanation {
    margin-bottom: 30px;
    padding-bottom: 20px;
    border-bottom: 1px solid #f0f0f0;
}

.preference-analysis:last-child,
.similar-users:last-child,
.strategy-explanation:last-child {
    border-bottom: none;
}

.preference-analysis h3,
.similar-users h3,
.strategy-explanation h3 {
    color: #303133;
    margin-bottom: 10px;
    font-size: 1.1rem;
}

.preference-analysis p,
.similar-users p {
    color: #606266;
    margin-bottom: 15px;
    line-height: 1.6;
}

.genre-stats,
.similar-users-list {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
}

.reasoning-details {
    margin: 15px 0;
}

.reasoning-explanation {
    padding: 10px;
    background: #f5f7fa;
    border-radius: 4px;
    line-height: 1.8;
}

.reasoning-explanation p {
    margin: 8px 0;
    color: #606266;
}

.detail-item {
    margin: 8px 0;
    color: #606266;
}
</style>