from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from database import db
from typing import List, Dict

app = FastAPI()

# 配置CORS，允许前端访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该指定具体的前端地址
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}


@app.get("/api/movies", response_model=List[Dict])
async def get_movies(
    limit: int = Query(default=100, ge=1, le=1000, description="返回的电影数量"),
    skip: int = Query(default=0, ge=0, description="跳过的电影数量")
):
    """
    获取电影列表
    
    - **limit**: 返回的电影数量（1-1000）
    - **skip**: 跳过的电影数量（用于分页）
    """
    try:
        movies = db.get_movies(limit=limit, skip=skip)
        return movies
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/movies/count")
async def get_movie_count():
    """获取电影总数"""
    try:
        count = db.get_movie_count()
        return {"count": count}
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/movies/search")
async def search_movies(
    q: str = Query(..., description="搜索关键词"),
    limit: int = Query(default=10, ge=1, le=50, description="返回结果数量")
):
    """
    搜索电影
    
    - **q**: 搜索关键词（电影标题）
    - **limit**: 返回结果数量（1-50）
    """
    try:
        movies = db.search_movies(q, limit=limit)
        return movies
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/users/search")
async def search_users(
    q: str = Query(..., description="搜索关键词（用户ID）"),
    limit: int = Query(default=10, ge=1, le=50, description="返回结果数量")
):
    """
    搜索用户
    
    - **q**: 搜索关键词（用户ID）
    - **limit**: 返回结果数量（1-50）
    """
    try:
        users = db.search_users(q, limit=limit)
        return users
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/network/movie/{movie_id}")
async def get_movie_network(
    movie_id: str,
    depth: int = Query(default=2, ge=1, le=3, description="关系深度（1-3）"),
    max_nodes: int = Query(default=100, ge=10, le=500, description="最大节点数量（10-500）")
):
    """
    获取电影的关系网络
    
    - **movie_id**: 电影ID
    - **depth**: 关系深度，1表示1度关系，2表示2度关系，3表示3度关系
    - **max_nodes**: 最大节点数量限制，用于控制返回的数据量，避免卡顿
    """
    try:
        network_data = db.get_movie_network(movie_id, depth=depth, max_nodes=max_nodes)
        return network_data
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/recommendations/user/{user_id}")
async def get_user_recommendations(
    user_id: str,
    limit: int = Query(default=20, ge=1, le=50, description="返回推荐数量"),
    min_rating: float = Query(default=4.0, ge=0.5, le=5.0, description="最低评分阈值")
):
    """
    获取用户个性化推荐
    
    - **user_id**: 用户ID
    - **limit**: 返回推荐数量（1-50）
    - **min_rating**: 最低评分阈值，用于确定用户喜欢的电影（0.5-5.0）
    """
    try:
        recommendations = db.get_user_recommendations(user_id, limit=limit, min_rating=min_rating)
        return recommendations
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/recommendations/user/{user_id}/liked")
async def get_user_liked_movies(
    user_id: str,
    limit: int = Query(default=10, ge=1, le=50, description="返回数量"),
    min_rating: float = Query(default=4.0, ge=0.5, le=5.0, description="最低评分阈值")
):
    """
    获取用户喜欢的电影列表
    
    - **user_id**: 用户ID
    - **limit**: 返回数量（1-50）
    - **min_rating**: 最低评分阈值（0.5-5.0）
    """
    try:
        movies = db.get_user_liked_movies(user_id, min_rating=min_rating, limit=limit)
        return movies
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/network/path/{start_type}/{start_id}/{end_type}/{end_id}")
async def get_shortest_path(
    start_type: str,
    start_id: str,
    end_type: str,
    end_id: str,
    max_depth: int = Query(default=6, ge=1, le=10, description="最大搜索深度（1-10）")
):
    """
    查找两个节点之间的最短路径（六度空间）
    
    - **start_type**: 起始节点类型（如 'User', 'Movie'），支持 'Person' 作为 'User' 的别名
    - **start_id**: 起始节点ID
    - **end_type**: 目标节点类型，支持 'Person' 作为 'User' 的别名
    - **end_id**: 目标节点ID
    - **max_depth**: 最大搜索深度（默认6度）
    """
    try:
        # 支持Person作为User的别名
        actual_start_type = 'User' if start_type == 'Person' else start_type
        actual_end_type = 'User' if end_type == 'Person' else end_type
        
        path_data = db.find_shortest_path(
            start_type=actual_start_type,
            start_id=start_id,
            end_type=actual_end_type,
            end_id=end_id,
            max_depth=max_depth
        )
        return path_data
    except Exception as e:
        return {"error": str(e)}


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时关闭数据库连接"""
    db.close()
