from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class Neo4jDatabase:
    """Neo4j数据库连接管理类"""
    
    def __init__(self):
        self.uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD", "password")
        self.driver = None
    
    @staticmethod
    def _safe_int_convert(value):
        """
        安全地将值转换为整数
        支持整数、浮点数字符串等格式
        """
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value)
        if isinstance(value, str):
            # 尝试直接转换为整数
            try:
                return int(value)
            except ValueError:
                # 如果是浮点数字符串，先转换为浮点数再转整数
                try:
                    return int(float(value))
                except (ValueError, TypeError):
                    raise ValueError(f"无法将 '{value}' 转换为整数")
        raise ValueError(f"不支持的类型: {type(value)}")
    
    def connect(self):
        """建立数据库连接"""
        if self.driver is None:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
        return self.driver
    
    def close(self):
        """关闭数据库连接"""
        if self.driver:
            self.driver.close()
            self.driver = None
    
    def get_session(self):
        """获取数据库会话"""
        if self.driver is None:
            self.connect()
        return self.driver.session()
    
    def get_movies(self, limit=100, skip=0):
        """获取电影列表"""
        query = """
        MATCH (m:Movie)
        OPTIONAL MATCH (m)-[:IN_GENRE]->(g:Genre)
        WITH m, collect(g.name) as genres
        RETURN m.id as id, m.title as title, m.year as year, genres
        ORDER BY m.id
        SKIP $skip
        LIMIT $limit
        """
        
        with self.get_session() as session:
            result = session.run(query, skip=skip, limit=limit)
            movies = []
            for record in result:
                # 将类型列表转换为字符串，用|分隔
                genres_list = record['genres'] or []
                genres_str = '|'.join(genres_list) if genres_list else ''
                movies.append({
                    'id': str(record['id']) if record['id'] is not None else '',
                    'title': record['title'] or '',
                    'year': record['year'] if record['year'] is not None else None,
                    'genres': genres_str
                })
            return movies
    
    def get_movie_count(self):
        """获取电影总数"""
        query = "MATCH (m:Movie) RETURN count(m) as count"
        
        with self.get_session() as session:
            result = session.run(query)
            record = result.single()
            return record['count'] if record else 0
    
    def search_movies(self, keyword, limit=10):
        """
        搜索电影
        
        Args:
            keyword: 搜索关键词（电影标题）
            limit: 返回结果数量限制
        
        Returns:
            list: 电影列表
        """
        query = """
        MATCH (m:Movie)
        WHERE m.title CONTAINS $keyword
        OPTIONAL MATCH (m)-[:IN_GENRE]->(g:Genre)
        WITH m, collect(g.name) as genres
        RETURN m.id as id, m.title as title, m.year as year, genres
        ORDER BY m.title
        LIMIT $limit
        """
        
        with self.get_session() as session:
            result = session.run(query, keyword=keyword, limit=limit)
            movies = []
            for record in result:
                genres_list = record['genres'] or []
                genres_str = '|'.join(genres_list) if genres_list else ''
                movies.append({
                    'id': str(record['id']) if record['id'] is not None else '',
                    'title': record['title'] or '',
                    'year': record['year'] if record['year'] is not None else None,
                    'genres': genres_str
                })
            return movies
    
    def search_users(self, keyword, limit=10):
        """
        搜索用户（通过ID搜索）
        
        Args:
            keyword: 搜索关键词（用户ID）
            limit: 返回结果数量限制
        
        Returns:
            list: 用户列表
        """
        try:
            # 如果关键词是数字，尝试按ID搜索
            user_id = self._safe_int_convert(keyword)
            query = """
            MATCH (u:User {id: $user_id})
            OPTIONAL MATCH (u)-[r:RATED]->(m:Movie)
            WITH u, count(r) as rating_count
            RETURN u.id as id, u.id as name, rating_count
            LIMIT 1
            """
            
            with self.get_session() as session:
                result = session.run(query, user_id=user_id)
                users = []
                for record in result:
                    users.append({
                        'id': str(record['id']) if record['id'] is not None else '',
                        'name': f"用户 {record['id']}",
                        'rating_count': record['rating_count'] or 0
                    })
                return users
        except ValueError:
            # 如果不是数字，返回空列表
            return []
    
    def get_movie_network(self, movie_id, depth=2, max_nodes=100):
        """
        获取电影的关系网络
        
        Args:
            movie_id: 电影ID
            depth: 关系深度（1-3）
            max_nodes: 最大节点数量限制（默认100）
        
        Returns:
            dict: 包含nodes和links的字典
        """
        # 限制深度在1-3之间
        depth = max(1, min(3, depth))
        # 限制节点数量在10-500之间
        max_nodes = max(10, min(500, max_nodes))
        
        with self.get_session() as session:
            # 首先获取起始节点
            start_query = "MATCH (m:Movie {id: $movie_id}) RETURN m"
            start_result = session.run(start_query, movie_id=self._safe_int_convert(movie_id))
            start_record = start_result.single()
            
            if not start_record:
                return {'nodes': [], 'links': []}
            
            start_node = start_record['m']
            nodes_dict = {}
            links_set = set()
            
            # 添加起始节点
            start_id = str(start_node.get('id', ''))
            nodes_dict[start_id] = self._node_to_dict(start_node, 'Movie')
            
            # 根据深度获取相关节点和关系
            # 使用可变长度路径，但限制在指定深度内
            path_pattern = f"[*1..{depth}]"
            
            # 查询所有相关节点和路径中的关系
            # 使用max_nodes * 2作为查询限制，因为实际返回的节点数可能少于查询限制
            query_limit = max_nodes * 2
            query = f"""
            MATCH (start:Movie {{id: $movie_id}})
            MATCH path = (start)-{path_pattern}-(related)
            WITH start, related, relationships(path) as rels
            RETURN DISTINCT start, related, rels
            LIMIT $query_limit
            """
            
            result = session.run(query, movie_id=self._safe_int_convert(movie_id), query_limit=query_limit)
            
            for record in result:
                # 如果已经达到最大节点数限制，停止添加新节点
                if len(nodes_dict) >= max_nodes:
                    break
                    
                related_node = record['related']
                rels = record['rels']
                
                # 添加相关节点
                related_id = self._get_node_id(related_node)
                if related_id not in nodes_dict:
                    node_type = self._get_node_type(related_node)
                    nodes_dict[related_id] = self._node_to_dict(related_node, node_type)
                
                # 添加路径中的所有关系（只添加已存在节点之间的关系）
                for rel in rels:
                    rel_start_node = rel.start_node
                    rel_end_node = rel.end_node
                    rel_type = rel.type
                    
                    rel_start_id = self._get_node_id(rel_start_node)
                    rel_end_id = self._get_node_id(rel_end_node)
                    
                    # 只添加两个节点都在我们节点字典中的关系
                    if rel_start_id in nodes_dict and rel_end_id in nodes_dict:
                        # 创建关系的唯一标识
                        link_key = (rel_start_id, rel_end_id, rel_type)
                        if link_key not in links_set:
                            links_set.add(link_key)
            
            # 转换links_set为列表（只包含已存在节点之间的关系）
            links = []
            for start_id, end_id, rel_type in links_set:
                if start_id in nodes_dict and end_id in nodes_dict:
                    links.append({
                        'source': start_id,
                        'target': end_id,
                        'type': rel_type
                    })
            
            return {
                'nodes': list(nodes_dict.values()),
                'links': links
            }
    
    def _get_node_id(self, node):
        """获取节点的ID"""
        # 优先使用id属性
        node_id = node.get('id')
        if node_id is not None:
            return str(node_id)
        # Genre节点使用name作为ID
        node_name = node.get('name')
        if node_name is not None:
            return str(node_name)
        # 如果都没有，使用节点的内部ID（不推荐，但作为后备方案）
        return str(node.element_id) if hasattr(node, 'element_id') else str(id(node))
    
    def _get_node_type(self, node):
        """获取节点类型"""
        labels = list(node.labels)
        if labels:
            return labels[0]
        return 'Unknown'
    
    def _node_to_dict(self, node, node_type):
        """将Neo4j节点转换为字典"""
        node_id = self._get_node_id(node)
        
        # 获取节点名称
        name = node.get('title') or node.get('name') or f"{node_type}_{node_id}"
        
        # 构建属性字典
        properties = {}
        for key, value in node.items():
            properties[key] = value
        
        return {
            'id': node_id,
            'name': name,
            'type': node_type,
            'properties': properties
        }
    
    def get_user_recommendations(self, user_id, limit=20, min_rating=4.0):
        """
        基于知识图谱获取用户个性化推荐
        
        推荐策略：
        1. 找到用户评分高的电影（>=min_rating）
        2. 找到这些电影的类型
        3. 推荐相同类型的其他电影
        4. 找到相似用户喜欢的电影
        5. 排除用户已评分的电影
        
        Args:
            user_id: 用户ID
            limit: 返回推荐数量
            min_rating: 最低评分阈值（用于确定用户喜欢的电影）
        
        Returns:
            dict: 包含推荐列表和推理过程的字典
        """
        with self.get_session() as session:
            user_id_int = self._safe_int_convert(user_id)
            
            # 策略1: 基于用户喜欢的电影类型推荐
            # 找到用户评分>=min_rating的电影及其类型
            query1 = """
            MATCH (u:User {id: $user_id})-[r:RATED]->(m:Movie)
            WHERE r.rating >= $min_rating
            MATCH (m)-[:IN_GENRE]->(g:Genre)
            WITH g, count(DISTINCT m) as genre_count
            ORDER BY genre_count DESC
            LIMIT 5
            MATCH (g)<-[:IN_GENRE]-(rec:Movie)
            WHERE NOT EXISTS {
                MATCH (u)-[:RATED]->(rec)
            }
            OPTIONAL MATCH (rec)-[:IN_GENRE]->(genres:Genre)
            WITH rec, collect(genres.name) as genres, g.name as reason_genre
            RETURN DISTINCT rec.id as id, rec.title as title, rec.year as year, 
                   genres, '类型偏好: ' + reason_genre as reason, 1 as score
            LIMIT $limit
            """
            
            # 策略2: 基于相似用户推荐
            # 找到与用户有相似评分偏好的其他用户
            query2 = """
            MATCH (u:User {id: $user_id})-[:RATED]->(m1:Movie)
            MATCH (other:User)-[:RATED]->(m1)
            WHERE other.id <> $user_id
            WITH other, count(DISTINCT m1) as common_movies
            WHERE common_movies >= 3
            MATCH (other)-[:RATED]->(m2:Movie)
            WHERE NOT EXISTS {
                MATCH (u)-[:RATED]->(m2)
            }
            OPTIONAL MATCH (m2)-[:IN_GENRE]->(g:Genre)
            WITH m2, collect(DISTINCT g.name) as genres, 
                 max(common_movies) as max_common_movies,
                 '相似用户推荐 (共同评分' + toString(max(common_movies)) + '部电影)' as reason,
                 2 as score
            ORDER BY max_common_movies DESC
            RETURN m2.id as id, m2.title as title, m2.year as year, 
                   genres, reason, score
            LIMIT $limit
            """
            
            # 策略3: 基于用户高评分电影的相似电影推荐
            # 找到用户高评分电影，然后找相同类型的其他电影
            query3 = """
            MATCH (u:User {id: $user_id})-[r:RATED]->(liked:Movie)
            WHERE r.rating >= $min_rating
            MATCH (liked)-[:IN_GENRE]->(g:Genre)<-[:IN_GENRE]-(similar:Movie)
            WHERE NOT EXISTS {
                MATCH (u)-[:RATED]->(similar)
            }
            AND similar.id <> liked.id
            OPTIONAL MATCH (similar)-[:IN_GENRE]->(genres:Genre)
            WITH similar, collect(DISTINCT genres.name) as genres, 
                 liked.title as liked_title,
                 '基于您喜欢的《' + liked.title + '》' as reason,
                 3 as score
            RETURN DISTINCT similar.id as id, similar.title as title, similar.year as year,
                   genres, reason, score
            LIMIT $limit
            """
            
            # 获取用户偏好类型统计
            genre_preference_query = """
            MATCH (u:User {id: $user_id})-[r:RATED]->(m:Movie)
            WHERE r.rating >= $min_rating
            MATCH (m)-[:IN_GENRE]->(g:Genre)
            WITH g, count(DISTINCT m) as movie_count, avg(r.rating) as avg_rating
            ORDER BY movie_count DESC
            RETURN g.name as genre, movie_count, avg_rating
            LIMIT 10
            """
            
            genre_preferences = []
            genre_result = session.run(genre_preference_query, user_id=user_id_int, min_rating=min_rating)
            for record in genre_result:
                genre_preferences.append({
                    'genre': record['genre'],
                    'movie_count': record['movie_count'],
                    'avg_rating': round(record['avg_rating'], 2)
                })
            
            # 获取相似用户信息
            similar_users_query = """
            MATCH (u:User {id: $user_id})-[:RATED]->(m1:Movie)
            MATCH (other:User)-[:RATED]->(m1)
            WHERE other.id <> $user_id
            WITH other, count(DISTINCT m1) as common_movies
            WHERE common_movies >= 3
            RETURN other.id as user_id, common_movies
            ORDER BY common_movies DESC
            LIMIT 5
            """
            
            similar_users = []
            similar_result = session.run(similar_users_query, user_id=user_id_int)
            for record in similar_result:
                similar_users.append({
                    'user_id': str(record['user_id']),
                    'common_movies': record['common_movies']
                })
            
            recommendations = {}
            recommendation_details = {}  # 存储每个推荐的详细推理信息
            
            # 执行查询1：基于类型偏好
            result1 = session.run(query1, user_id=user_id_int, min_rating=min_rating, limit=limit)
            for record in result1:
                movie_id = str(record['id'])
                if movie_id not in recommendations:
                    genre_name = record['reason'].replace('类型偏好: ', '')
                    recommendations[movie_id] = {
                        'id': movie_id,
                        'title': record['title'] or '',
                        'year': record['year'],
                        'genres': '|'.join(record['genres'] or []),
                        'reason': record['reason'],
                        'score': record['score'],
                        'strategy': '类型偏好推荐'
                    }
                    recommendation_details[movie_id] = {
                        'strategy': '类型偏好推荐',
                        'reason_genre': genre_name,
                        'explanation': f'您喜欢{genre_name}类型的电影，我们为您推荐同类型电影'
                    }
            
            # 执行查询2：基于相似用户
            result2 = session.run(query2, user_id=user_id_int, limit=limit)
            for record in result2:
                movie_id = str(record['id'])
                if movie_id not in recommendations:
                    common_count = record['reason'].split('共同评分')[1].split('部')[0] if '共同评分' in record['reason'] else '3'
                    recommendations[movie_id] = {
                        'id': movie_id,
                        'title': record['title'] or '',
                        'year': record['year'],
                        'genres': '|'.join(record['genres'] or []),
                        'reason': record['reason'],
                        'score': record['score'],
                        'strategy': '相似用户推荐'
                    }
                    recommendation_details[movie_id] = {
                        'strategy': '相似用户推荐',
                        'common_movies': int(common_count),
                        'explanation': f'与您有相似偏好的用户（共同评分{common_count}部电影）也喜欢这部电影'
                    }
            
            # 执行查询3：基于相似电影
            result3 = session.run(query3, user_id=user_id_int, min_rating=min_rating, limit=limit)
            for record in result3:
                movie_id = str(record['id'])
                if movie_id not in recommendations:
                    liked_title = record['reason'].replace('基于您喜欢的《', '').replace('》', '')
                    recommendations[movie_id] = {
                        'id': movie_id,
                        'title': record['title'] or '',
                        'year': record['year'],
                        'genres': '|'.join(record['genres'] or []),
                        'reason': record['reason'],
                        'score': record['score'],
                        'strategy': '相似电影推荐'
                    }
                    recommendation_details[movie_id] = {
                        'strategy': '相似电影推荐',
                        'based_on_movie': liked_title,
                        'explanation': f'基于您喜欢的《{liked_title}》，我们为您推荐相似类型的电影'
                    }
            
            # 按score排序，返回前limit个
            sorted_recs = sorted(recommendations.values(), key=lambda x: x['score'])[:limit]
            
            # 为每个推荐添加详细推理信息
            for rec in sorted_recs:
                if rec['id'] in recommendation_details:
                    rec['details'] = recommendation_details[rec['id']]
            
            return {
                'recommendations': sorted_recs,
                'reasoning': {
                    'genre_preferences': genre_preferences,
                    'similar_users': similar_users,
                    'total_recommendations': len(sorted_recs)
                }
            }
    
    def get_user_liked_movies(self, user_id, min_rating=4.0, limit=10):
        """
        获取用户喜欢的电影列表
        
        Args:
            user_id: 用户ID
            min_rating: 最低评分阈值
            limit: 返回数量限制
        
        Returns:
            list: 用户喜欢的电影列表
        """
        with self.get_session() as session:
            user_id_int = self._safe_int_convert(user_id)
            
            query = """
            MATCH (u:User {id: $user_id})-[r:RATED]->(m:Movie)
            WHERE r.rating >= $min_rating
            OPTIONAL MATCH (m)-[:IN_GENRE]->(g:Genre)
            WITH m, r.rating as rating, collect(g.name) as genres
            RETURN m.id as id, m.title as title, m.year as year, 
                   genres, rating
            ORDER BY rating DESC, m.title
            LIMIT $limit
            """
            
            result = session.run(query, user_id=user_id_int, min_rating=min_rating, limit=limit)
            movies = []
            for record in result:
                genres_list = record['genres'] or []
                genres_str = '|'.join(genres_list) if genres_list else ''
                movies.append({
                    'id': str(record['id']) if record['id'] is not None else '',
                    'title': record['title'] or '',
                    'year': record['year'] if record['year'] is not None else None,
                    'genres': genres_str,
                    'rating': record['rating']
                })
            return movies
    
    def find_shortest_path(self, start_type, start_id, end_type, end_id, max_depth=6):
        """
        查找两个节点之间的最短路径（六度空间）
        
        Args:
            start_type: 起始节点类型（如 'User', 'Movie'）
            start_id: 起始节点ID
            end_type: 目标节点类型
            end_id: 目标节点ID
            max_depth: 最大搜索深度（默认6度）
        
        Returns:
            dict: 包含nodes和links的字典，表示最短路径
        """
        with self.get_session() as session:
            # 构建查询，使用shortestPath函数
            # 注意：使用无向路径搜索，因为关系可能是双向的
            query = f"""
            MATCH (start:{start_type} {{id: $start_id}})
            MATCH (end:{end_type} {{id: $end_id}})
            MATCH path = shortestPath((start)-[*..{max_depth}]-(end))
            RETURN path, length(path) as path_length
            ORDER BY path_length
            LIMIT 1
            """
            
            result = session.run(query, start_id=self._safe_int_convert(start_id), end_id=self._safe_int_convert(end_id))
            record = result.single()
            
            if not record or not record['path']:
                return {'nodes': [], 'links': []}
            
            path = record['path']
            nodes_list = []  # 保持节点顺序
            nodes_dict = {}  # 用于去重
            links = []
            
            # 按顺序提取路径中的所有节点
            for node in path.nodes:
                node_id = self._get_node_id(node)
                node_type = self._get_node_type(node)
                
                if node_id not in nodes_dict:
                    node_dict = self._node_to_dict(node, node_type)
                    nodes_dict[node_id] = node_dict
                    nodes_list.append(node_dict)
            
            # 提取路径中的所有关系，按顺序
            for rel in path.relationships:
                start_node = rel.start_node
                end_node = rel.end_node
                
                start_id_str = self._get_node_id(start_node)
                end_id_str = self._get_node_id(end_node)
                rel_type = rel.type
                
                # 确保两个节点都在节点列表中
                if start_id_str in nodes_dict and end_id_str in nodes_dict:
                    links.append({
                        'source': start_id_str,
                        'target': end_id_str,
                        'type': rel_type
                    })
            
            return {
                'nodes': nodes_list,
                'links': links
            }


# 全局数据库实例
db = Neo4jDatabase()

