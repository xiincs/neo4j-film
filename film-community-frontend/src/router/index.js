import { createRouter, createWebHistory } from 'vue-router'

// 导入组件 - 先创建这些基础页面
const Home = () => import('@/views/HomeView.vue')
const NetworkGraph = () => import('@/components/NetworkGraph.vue')
const Search = () => import('@/views/SearchView.vue')
const Movies = () => import('@/views/MoviesView.vue')
const Recommendations = () => import('@/views/RecommendationsView.vue')

const routes = [
    {
        path: '/',
        name: 'Home',
        component: Home,
        meta: { title: '电影知识图谱' }
    },
    {
        path: '/network',
        name: 'Network',
        component: NetworkGraph,
        meta: { title: '关系探索' }
    },
    {
        path: '/network/movie/:id',
        name: 'MovieNetwork',
        component: NetworkGraph,
        meta: { title: '电影关系网络' }
    },
    {
        path: '/network/person/:id',
        name: 'PersonNetwork',
        component: NetworkGraph,
        meta: { title: '人物关系网络' }
    },
    {
        path: '/search',
        name: 'Search',
        component: Search,
        meta: { title: '智能搜索' }
    },
    {
        path: '/movies',
        name: 'Movies',
        component: Movies,
        meta: { title: '电影列表' }
    },
    {
        path: '/recommendations',
        name: 'Recommendations',
        component: Recommendations,
        meta: { title: '智能推荐' }
    },
    {
        path: '/:pathMatch(.*)*',
        name: 'NotFound',
        component: () => import('@/views/NotFound.vue'),
        meta: { title: '页面未找到' }
    }
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

// 路由守卫 - 更新页面标题
router.beforeEach((to, from, next) => {
    document.title = to.meta.title || '电影知识图谱'
    next()
})

export default router