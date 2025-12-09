<template>
    <div class="network-graph-container">
        <div class="graph-controls">
            <div class="search-container" style="position: relative;">
                <el-input 
                    v-model="searchQuery" 
                    placeholder="搜索电影..." 
                    style="width: 300px; margin-right: 10px;"
                    @keyup.enter="handleSearch"
                    @input="handleSearchInput"
                    clearable>
                    <template #append>
                        <el-button @click="handleSearch" :icon="Search" :loading="searching">搜索</el-button>
                    </template>
                </el-input>
                <!-- 搜索结果下拉列表 -->
                <div v-if="searchResults.length > 0 && showSearchResults" class="search-results">
                    <div 
                        v-for="movie in searchResults" 
                        :key="movie.id"
                        class="search-result-item"
                        @click="selectMovie(movie)">
                        <div class="movie-title">{{ movie.title }}</div>
                        <div class="movie-info">
                            <span v-if="movie.year">{{ movie.year }}</span>
                            <span v-if="movie.genres" class="genres">{{ movie.genres.split('|').slice(0, 2).join(', ') }}</span>
                        </div>
                    </div>
                </div>
            </div>

            <el-select v-model="currentDepth" @change="refreshGraph" style="width: 120px;">
                <el-option label="1度关系" :value="1" />
                <el-option label="2度关系" :value="2" />
                <el-option label="3度关系" :value="3" />
            </el-select>

            <el-select v-model="maxNodes" @change="refreshGraph" style="width: 140px;">
                <el-option label="少量 (50)" :value="50" />
                <el-option label="中等 (100)" :value="100" />
                <el-option label="较多 (200)" :value="200" />
                <el-option label="大量 (300)" :value="300" />
            </el-select>

            <el-button @click="resetGraph" :icon="Refresh">重置</el-button>
        </div>

        <div class="graph-content">
            <div ref="chart" class="network-chart"></div>

            <div v-if="selectedNode" class="node-info-panel">
                <h3>节点信息</h3>
                <div class="info-content">
                    <p><strong>名称:</strong> {{ selectedNode.name }}</p>
                    <p><strong>类型:</strong> {{ selectedNode.type }}</p>
                    <div v-if="selectedNode.properties">
                        <p v-if="selectedNode.properties.rating">
                            <strong>评分:</strong> {{ selectedNode.properties.rating }}
                        </p>
                        <p v-if="selectedNode.properties.year">
                            <strong>年份:</strong> {{ selectedNode.properties.year }}
                        </p>
                    </div>
                    <el-button v-if="selectedNode.type === 'Movie' || selectedNode.type === 'Person'"
                        @click="exploreNode(selectedNode)" type="primary" size="small">
                        探索关系
                    </el-button>
                </div>
            </div>
        </div>

        <!-- 六度空间查询面板 -->
        <div class="six-degrees-panel">
            <h4>六度空间查询（用户关系）</h4>
            <div class="six-degrees-controls">
                <div class="search-user-container" style="position: relative;">
                    <el-input 
                        v-model="startNode" 
                        placeholder="起始用户ID" 
                        style="width: 150px;"
                        @input="handleStartUserInput"
                        clearable>
                    </el-input>
                    <div v-if="startUserResults.length > 0 && showStartUserResults" class="user-search-results">
                        <div 
                            v-for="user in startUserResults" 
                            :key="user.id"
                            class="user-result-item"
                            @click="selectStartUser(user)">
                            <div class="user-name">{{ user.name }}</div>
                            <div class="user-info" v-if="user.rating_count">
                                评分: {{ user.rating_count }} 部电影
                            </div>
                        </div>
                    </div>
                </div>
                <span style="margin: 0 10px;">到</span>
                <div class="search-user-container" style="position: relative;">
                    <el-input 
                        v-model="endNode" 
                        placeholder="目标用户ID" 
                        style="width: 150px;"
                        @input="handleEndUserInput"
                        clearable>
                    </el-input>
                    <div v-if="endUserResults.length > 0 && showEndUserResults" class="user-search-results">
                        <div 
                            v-for="user in endUserResults" 
                            :key="user.id"
                            class="user-result-item"
                            @click="selectEndUser(user)">
                            <div class="user-name">{{ user.name }}</div>
                            <div class="user-info" v-if="user.rating_count">
                                评分: {{ user.rating_count }} 部电影
                            </div>
                        </div>
                    </div>
                </div>
                <el-button @click="findShortestPath" type="success" size="small" :loading="pathSearching">
                    查找路径
                </el-button>
            </div>
            <div v-if="pathResult" class="path-result">
                <p><strong>路径度数:</strong> {{ pathResult.degrees }} 度</p>
                <p><strong>路径:</strong> {{ pathResult.path.join(' → ') }}</p>
            </div>
            <div v-if="pathError" class="path-error">
                <p style="color: #f56c6c;">{{ pathError }}</p>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import * as echarts from 'echarts'
import { Search, Refresh } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

// 响应式数据
const searchQuery = ref('')
const searchResults = ref([])
const showSearchResults = ref(false)
const searching = ref(false)
const currentDepth = ref(2)
const maxNodes = ref(100)
const chart = ref(null)
let chartInstance = null
const selectedNode = ref(null)
const startNode = ref('')
const endNode = ref('')
const startUserResults = ref([])
const endUserResults = ref([])
const showStartUserResults = ref(false)
const showEndUserResults = ref(false)
const pathResult = ref(null)
const pathError = ref(null)
const pathSearching = ref(false)
const currentNodeId = ref(null)
const currentNodeType = ref('Movie')

// 图表配置
const getChartOption = (data) => ({
    tooltip: {
        formatter: function (params) {
            if (params.dataType === 'node') {
                return `
          <strong>${params.data.name}</strong><br/>
          类型: ${params.data.type}<br/>
          ${params.data.properties?.rating ? `评分: ${params.data.properties.rating}<br/>` : ''}
          ${params.data.properties?.year ? `年份: ${params.data.properties.year}` : ''}
        `
            } else {
                return `关系: ${params.data.relationType}`
            }
        }
    },
    series: [{
        type: 'graph',
        layout: 'force',
        data: data.nodes,
        links: data.links,
        roam: true,
        label: {
            show: true,
            position: 'right',
            formatter: '{b}'
        },
        lineStyle: {
            color: 'source',
            curveness: 0.3
        },
        emphasis: {
            focus: 'adjacency',
            lineStyle: {
                width: 3
            }
        },
        force: {
            repulsion: 200,
            gravity: 0.1,
            edgeLength: 100
        },
        categories: [
            { name: 'Movie', itemStyle: { color: '#5470c6' } },
            { name: 'Person', itemStyle: { color: '#91cc75' } },
            { name: 'Genre', itemStyle: { color: '#fac858' } },
            { name: 'User', itemStyle: { color: '#ee6666' } }
        ]
    }]
})

// 初始化图表
const initChart = () => {
    if (!chart.value) return

    chartInstance = echarts.init(chart.value)

    // 添加点击事件
    chartInstance.on('click', (params) => {
        if (params.dataType === 'node') {
            selectedNode.value = params.data
        }
    })

    // 窗口大小变化时重绘
    window.addEventListener('resize', handleResize)
}

// 加载网络数据
const loadNetworkData = async (nodeId, nodeType = 'Movie') => {
    try {
        currentNodeId.value = nodeId
        currentNodeType.value = nodeType
        
        const endpoint = nodeType === 'Movie' ? 'movie' : 'person'
        const response = await fetch(
            `http://localhost:8000/api/network/${endpoint}/${nodeId}?depth=${currentDepth.value}&max_nodes=${maxNodes.value}`
        )
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`)
        }
        
        const data = await response.json()
        
        if (data.error) {
            throw new Error(data.error)
        }

        // 转换数据格式以适应ECharts
        const chartData = {
            nodes: data.nodes.map(node => ({
                ...node,
                symbolSize: getNodeSize(node.type),
                category: node.type,
                itemStyle: getNodeStyle(node.type)
            })),
            links: data.links.map(link => ({
                ...link,
                relationType: link.type
            }))
        }

        if (chartInstance) {
            chartInstance.setOption(getChartOption(chartData))
        }

        ElMessage.success(`数据加载成功 (${data.nodes.length}个节点, ${data.links.length}条关系)`)
    } catch (error) {
        console.error('加载网络数据失败:', error)
        ElMessage.error('数据加载失败: ' + error.message)
    }
}

// 刷新图表
const refreshGraph = () => {
    if (currentNodeId.value) {
        loadNetworkData(currentNodeId.value, currentNodeType.value)
    }
}

// 根据节点类型设置大小和样式
const getNodeSize = (type) => {
    const sizes = {
        'Movie': 30,
        'Person': 25,
        'Genre': 20,
        'User': 15
    }
    return sizes[type] || 20
}

const getNodeStyle = (type) => {
    const colors = {
        'Movie': '#5470c6',
        'Person': '#91cc75',
        'Genre': '#fac858',
        'User': '#ee6666'
    }
    return { color: colors[type] || '#73c0de' }
}

// 搜索输入处理（实时搜索）
const handleSearchInput = async () => {
    const query = searchQuery.value.trim()
    if (query.length < 2) {
        searchResults.value = []
        showSearchResults.value = false
        return
    }
    
    // 防抖处理
    clearTimeout(searchInputTimer)
    searchInputTimer = setTimeout(async () => {
        await performSearch(query)
    }, 300)
}

let searchInputTimer = null

// 执行搜索
const performSearch = async (query) => {
    if (!query || query.length < 2) {
        return
    }
    
    try {
        searching.value = true
        const response = await fetch(
            `http://localhost:8000/api/movies/search?q=${encodeURIComponent(query)}&limit=10`
        )
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`)
        }
        
        const data = await response.json()
        
        if (data.error) {
            throw new Error(data.error)
        }
        
        searchResults.value = data
        showSearchResults.value = data.length > 0
    } catch (error) {
        console.error('搜索失败:', error)
        ElMessage.error('搜索失败: ' + error.message)
        searchResults.value = []
        showSearchResults.value = false
    } finally {
        searching.value = false
    }
}

// 搜索处理（点击搜索按钮或按回车）
const handleSearch = async () => {
    const query = searchQuery.value.trim()
    if (!query) {
        ElMessage.warning('请输入搜索内容')
        return
    }
    
    await performSearch(query)
    
    // 如果只有一个结果，直接加载
    if (searchResults.value.length === 1) {
        selectMovie(searchResults.value[0])
    } else if (searchResults.value.length === 0) {
        ElMessage.warning('未找到相关电影')
    }
}

// 选择电影
const selectMovie = (movie) => {
    searchQuery.value = movie.title
    showSearchResults.value = false
    loadNetworkData(movie.id, 'Movie')
}

// 探索节点关系
const exploreNode = (node) => {
    loadNetworkData(node.properties.id || node.id, node.type)
}

// 搜索起始用户
const handleStartUserInput = async () => {
    const query = startNode.value.trim()
    if (query.length < 1) {
        startUserResults.value = []
        showStartUserResults.value = false
        return
    }
    
    clearTimeout(startUserInputTimer)
    startUserInputTimer = setTimeout(async () => {
        await searchUser(query, 'start')
    }, 300)
}

let startUserInputTimer = null

// 搜索目标用户
const handleEndUserInput = async () => {
    const query = endNode.value.trim()
    if (query.length < 1) {
        endUserResults.value = []
        showEndUserResults.value = false
        return
    }
    
    clearTimeout(endUserInputTimer)
    endUserInputTimer = setTimeout(async () => {
        await searchUser(query, 'end')
    }, 300)
}

let endUserInputTimer = null

// 搜索用户
const searchUser = async (query, type) => {
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
        
        if (type === 'start') {
            startUserResults.value = data
            showStartUserResults.value = data.length > 0
        } else {
            endUserResults.value = data
            showEndUserResults.value = data.length > 0
        }
    } catch (error) {
        console.error('搜索用户失败:', error)
        if (type === 'start') {
            startUserResults.value = []
            showStartUserResults.value = false
        } else {
            endUserResults.value = []
            showEndUserResults.value = false
        }
    }
}

// 选择起始用户
const selectStartUser = (user) => {
    startNode.value = user.id
    showStartUserResults.value = false
}

// 选择目标用户
const selectEndUser = (user) => {
    endNode.value = user.id
    showEndUserResults.value = false
}

// 查找最短路径
const findShortestPath = async () => {
    if (!startNode.value || !endNode.value) {
        ElMessage.warning('请输入起始用户和目标用户')
        return
    }

    if (startNode.value === endNode.value) {
        ElMessage.warning('起始用户和目标用户不能相同')
        return
    }

    try {
        pathSearching.value = true
        pathError.value = null
        pathResult.value = null
        
        const response = await fetch(
            `http://localhost:8000/api/network/path/Person/${startNode.value}/Person/${endNode.value}?max_depth=6`
        )
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`)
        }
        
        const data = await response.json()

        if (data.error) {
            throw new Error(data.error)
        }

        if (data.nodes && data.nodes.length > 0) {
            pathResult.value = {
                degrees: data.links.length,
                path: data.nodes.map(node => node.name || node.id)
            }

            // 在图表中高亮显示路径
            highlightPath(data)
            ElMessage.success(`找到路径！共 ${data.links.length} 度关系`)
        } else {
            pathError.value = '未找到路径，可能两个用户之间没有连接，或者超过了6度关系'
            ElMessage.warning('未找到路径')
        }
    } catch (error) {
        console.error('查询失败:', error)
        pathError.value = '查询失败: ' + error.message
        ElMessage.error('查询失败: ' + error.message)
    } finally {
        pathSearching.value = false
    }
}

// 高亮显示路径
const highlightPath = (pathData) => {
    const option = getChartOption(pathData)
    option.series[0].lineStyle = {
        width: (link) => link.data?.isPath ? 5 : 1,
        color: (link) => link.data?.isPath ? '#ff0000' : 'source'
    }

    chartInstance.setOption(option)
}

// 重置图表
const resetGraph = () => {
    selectedNode.value = null
    pathResult.value = null
    currentNodeId.value = null
    currentNodeType.value = 'Movie'
    if (chartInstance) {
        chartInstance.clear()
    }
}

// 响应窗口大小变化
const handleResize = () => {
    if (chartInstance) {
        chartInstance.resize()
    }
}

// 获取路由信息
const route = useRoute()

// 监听路由变化
watch(() => route.params.id, (newId) => {
    if (newId && route.name === 'MovieNetwork') {
        loadNetworkData(newId, 'Movie')
    } else if (newId && route.name === 'PersonNetwork') {
        loadNetworkData(newId, 'Person')
    }
}, { immediate: true })

// 点击外部关闭搜索结果
const handleClickOutside = (event) => {
    const searchContainer = event.target.closest('.search-container')
    if (!searchContainer) {
        showSearchResults.value = false
    }
}

// 生命周期
onMounted(() => {
    initChart()
    // 如果路由中有ID参数，使用路由参数；否则加载默认示例
    const routeId = route.params.id
    if (routeId) {
        if (route.name === 'MovieNetwork') {
            loadNetworkData(routeId, 'Movie')
        } else if (route.name === 'PersonNetwork') {
            loadNetworkData(routeId, 'Person')
        } else {
            loadNetworkData('1', 'Movie')
        }
    } else {
        // 默认加载一个示例网络
        loadNetworkData('1', 'Movie')
    }
    
    // 添加点击外部关闭搜索结果的事件监听
    document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
    if (chartInstance) {
        chartInstance.dispose()
    }
    window.removeEventListener('resize', handleResize)
    document.removeEventListener('click', handleClickOutside)
    if (searchInputTimer) {
        clearTimeout(searchInputTimer)
    }
    if (startUserInputTimer) {
        clearTimeout(startUserInputTimer)
    }
    if (endUserInputTimer) {
        clearTimeout(endUserInputTimer)
    }
})
</script>

<style scoped>
.network-graph-container {
    padding: 20px;
    height: 100vh;
    display: flex;
    flex-direction: column;
}

.graph-controls {
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    gap: 10px;
}

.graph-content {
    display: flex;
    flex: 1;
    gap: 20px;
}

.network-chart {
    flex: 1;
    height: 600px;
    border: 1px solid #e4e7ed;
    border-radius: 4px;
}

.node-info-panel {
    width: 300px;
    padding: 20px;
    border: 1px solid #e4e7ed;
    border-radius: 4px;
    background: #fafafa;
}

.six-degrees-panel {
    margin-top: 20px;
    padding: 15px;
    border: 1px solid #e4e7ed;
    border-radius: 4px;
    background: #f0f9ff;
}

.six-degrees-controls {
    display: flex;
    align-items: center;
    margin-bottom: 10px;
}

.path-result {
    padding: 10px;
    background: white;
    border-radius: 4px;
}

.info-content p {
    margin: 8px 0;
}

.search-container {
    position: relative;
}

.search-results {
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    background: white;
    border: 1px solid #e4e7ed;
    border-radius: 4px;
    box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
    z-index: 1000;
    max-height: 300px;
    overflow-y: auto;
    margin-top: 5px;
}

.search-result-item {
    padding: 12px 15px;
    cursor: pointer;
    border-bottom: 1px solid #f0f0f0;
    transition: background-color 0.2s;
}

.search-result-item:hover {
    background-color: #f5f7fa;
}

.search-result-item:last-child {
    border-bottom: none;
}

.movie-title {
    font-weight: 500;
    color: #303133;
    margin-bottom: 4px;
}

.movie-info {
    font-size: 12px;
    color: #909399;
    display: flex;
    gap: 10px;
}

.movie-info .genres {
    color: #606266;
}

.search-user-container {
    position: relative;
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

.path-error {
    margin-top: 10px;
    padding: 10px;
    background: #fef0f0;
    border: 1px solid #fde2e2;
    border-radius: 4px;
}
</style>