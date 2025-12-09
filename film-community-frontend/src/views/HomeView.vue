<template>
    <div class="home">
        <div class="hero-section">
            <h1>电影知识图谱系统</h1>
            <p class="subtitle">基于MovieLens数据集的电影关系网络探索平台</p>
        </div>

        <!-- 数据集介绍 -->
        <el-card class="section-card" shadow="hover">
            <template #header>
                <div class="card-header">
                    <el-icon><Document /></el-icon>
                    <span>数据集介绍</span>
                </div>
            </template>
            <div class="dataset-info">
                <p>本系统使用 <strong>MovieLens ml-latest-small</strong> 数据集，这是一个经典的电影推荐系统数据集，由明尼苏达大学的GroupLens研究组提供。</p>
                
                <div class="dataset-stats">
                    <el-row :gutter="20">
                        <el-col :span="6" v-for="stat in datasetStats" :key="stat.label">
                            <el-statistic :title="stat.label" :value="stat.value" />
                        </el-col>
                    </el-row>
                </div>

                <div class="dataset-details">
                    <h3>数据文件结构</h3>
                    <ul>
                        <li><strong>movies.csv</strong> - 包含9742部电影的信息，包括电影ID、标题和类型</li>
                        <li><strong>ratings.csv</strong> - 包含100836条用户评分记录，评分范围为0.5-5.0星</li>
                        <li><strong>tags.csv</strong> - 包含3683条用户生成的电影标签</li>
                        <li><strong>links.csv</strong> - 包含电影与其他数据源的链接（IMDB、TMDB）</li>
                    </ul>

                    <h3>数据特点</h3>
                    <ul>
                        <li>数据时间跨度：1996年3月29日 - 2018年9月24日</li>
                        <li>所有用户至少评分了20部电影</li>
                        <li>电影类型包括：动作、冒险、动画、喜剧、剧情、科幻等19种类型</li>
                        <li>数据已导入Neo4j图数据库，构建了电影-用户-类型的关系网络</li>
                    </ul>
                </div>
            </div>
        </el-card>

        <!-- 功能介绍 -->
        <el-card class="section-card" shadow="hover">
            <template #header>
                <div class="card-header">
                    <el-icon><Operation /></el-icon>
                    <span>系统功能</span>
                </div>
            </template>
            <div class="feature-cards">
                <el-card 
                    v-for="feature in features" 
                    :key="feature.name" 
                    class="feature-card" 
                    shadow="hover"
                    @click="$router.push(feature.route)">
                    <div class="feature-content">
                        <el-icon size="48" :color="feature.color">
                            <component :is="feature.icon" />
                        </el-icon>
                        <h3>{{ feature.name }}</h3>
                        <p>{{ feature.description }}</p>
                        <ul class="feature-list">
                            <li v-for="item in feature.items" :key="item">{{ item }}</li>
                        </ul>
                    </div>
                </el-card>
            </div>
        </el-card>

        <!-- 技术栈 -->
        <el-card class="section-card" shadow="hover">
            <template #header>
                <div class="card-header">
                    <el-icon><Tools /></el-icon>
                    <span>技术栈</span>
                </div>
            </template>
            <div class="tech-stack">
                <el-row :gutter="20">
                    <el-col :span="8">
                        <h4>后端</h4>
                        <ul>
                            <li>Python 3</li>
                            <li>FastAPI</li>
                            <li>Neo4j 图数据库</li>
                            <li>python-dotenv</li>
                        </ul>
                    </el-col>
                    <el-col :span="8">
                        <h4>前端</h4>
                        <ul>
                            <li>Vue 3</li>
                            <li>Element Plus</li>
                            <li>ECharts</li>
                            <li>Vue Router</li>
                        </ul>
                    </el-col>
                    <el-col :span="8">
                        <h4>数据</h4>
                        <ul>
                            <li>MovieLens数据集</li>
                            <li>Neo4j图数据库</li>
                            <li>Cypher查询语言</li>
                        </ul>
                    </el-col>
                </el-row>
            </div>
        </el-card>
    </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import {
    Search,
    Connection,
    Film,
    Star,
    Document,
    Operation,
    Tools
} from '@element-plus/icons-vue'

const datasetStats = ref([
    { label: '电影数量', value: 9742 },
    { label: '用户数量', value: 610 },
    { label: '评分数量', value: 100836 },
    { label: '标签数量', value: 3683 }
])

const features = ref([
    {
        name: '电影列表',
        description: '浏览和搜索完整的电影数据库',
        icon: Film,
        route: '/movies',
        color: '#E6A23C',
        items: [
            '分页浏览9742部电影',
            '支持按标题搜索电影',
            '查看电影详细信息（标题、年份、类型）',
            '快速跳转到电影关系网络'
        ]
    },
    {
        name: '关系网络图',
        description: '可视化探索电影之间的关系网络',
        icon: Connection,
        route: '/network',
        color: '#409EFF',
        items: [
            '交互式网络图可视化',
            '支持1-3度关系深度查询',
            '可调节数据量（50-300节点）',
            '查看电影与类型、用户的关系',
            '点击节点探索更多关系'
        ]
    },
    {
        name: '六度空间查询',
        description: '查找任意两个用户之间的最短关系路径',
        icon: Search,
        route: '/network',
        color: '#67C23A',
        items: [
            '支持最多6度关系查询',
            '实时搜索用户',
            '可视化显示关系路径',
            '展示路径度数和完整路径'
        ]
    },
    {
        name: '智能推荐',
        description: '基于知识图谱的个性化推荐（开发中）',
        icon: Star,
        route: '/recommendations',
        color: '#F56C6C',
        items: [
            '基于用户评分历史',
            '基于电影类型偏好',
            '基于相似用户推荐',
            '个性化推荐算法'
        ]
    }
])

// 获取真实统计数据
onMounted(async () => {
    try {
        const response = await fetch('http://localhost:8000/api/movies/count')
        if (response.ok) {
            const data = await response.json()
            if (data.count) {
                datasetStats.value[0].value = data.count
            }
        }
    } catch (error) {
        console.error('获取统计数据失败:', error)
    }
})
</script>

<style scoped>
.home {
    padding: 20px;
    max-width: 1400px;
    margin: 0 auto;
}

.hero-section {
    text-align: center;
    margin-bottom: 40px;
    padding: 40px 0;
}

.hero-section h1 {
    font-size: 2.8rem;
    margin-bottom: 15px;
    color: #303133;
    font-weight: 600;
}

.subtitle {
    font-size: 1.3rem;
    color: #606266;
    margin: 0;
}

.section-card {
    margin-bottom: 30px;
}

.card-header {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 1.2rem;
    font-weight: 600;
    color: #303133;
}

.dataset-info {
    line-height: 1.8;
}

.dataset-info p {
    font-size: 1.05rem;
    color: #606266;
    margin-bottom: 25px;
}

.dataset-stats {
    margin: 30px 0;
    padding: 20px;
    background: #f5f7fa;
    border-radius: 8px;
}

.dataset-details {
    margin-top: 30px;
}

.dataset-details h3 {
    color: #303133;
    margin: 20px 0 15px;
    font-size: 1.1rem;
}

.dataset-details ul {
    margin: 10px 0 20px 20px;
    color: #606266;
    line-height: 2;
}

.dataset-details li {
    margin-bottom: 8px;
}

.feature-cards {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 20px;
    margin-top: 20px;
}

.feature-card {
    cursor: pointer;
    transition: all 0.3s ease;
    height: 100%;
}

.feature-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.feature-content {
    padding: 25px;
}

.feature-content h3 {
    margin: 15px 0 10px;
    color: #303133;
    font-size: 1.3rem;
}

.feature-content > p {
    color: #606266;
    line-height: 1.6;
    margin-bottom: 15px;
    font-size: 0.95rem;
}

.feature-list {
    list-style: none;
    padding: 0;
    margin: 15px 0 0;
    text-align: left;
}

.feature-list li {
    padding: 8px 0 8px 25px;
    color: #606266;
    position: relative;
    font-size: 0.9rem;
    line-height: 1.5;
}

.feature-list li::before {
    content: '✓';
    position: absolute;
    left: 0;
    color: #67c23a;
    font-weight: bold;
}

.tech-stack {
    padding: 10px 0;
}

.tech-stack h4 {
    color: #303133;
    margin-bottom: 15px;
    font-size: 1.1rem;
}

.tech-stack ul {
    list-style: none;
    padding: 0;
    margin: 0;
}

.tech-stack li {
    padding: 8px 0;
    color: #606266;
    border-bottom: 1px solid #f0f0f0;
}

.tech-stack li:last-child {
    border-bottom: none;
}
</style>