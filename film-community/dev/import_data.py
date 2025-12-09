import pandas as pd
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class MovieLensImporter:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def import_all_data(self):
        """导入所有数据"""
        print("开始导入MovieLens数据...")

        # 清空现有数据（可选，第一次运行时使用）
        self.clear_database()

        # 导入电影和类型
        self.import_movies_and_genres()

        # 导入用户和评分
        self.import_ratings()

        # 导入标签
        self.import_tags()

        print("数据导入完成！")

    def clear_database(self):
        """清空数据库（谨慎使用）"""
        with self.driver.session() as session:
            session.execute_write(self._clear_database)
            print("数据库已清空")

    @staticmethod
    def _clear_database(tx):
        query = "MATCH (n) DETACH DELETE n"
        tx.run(query)

    def import_movies_and_genres(self):
        """导入电影和类型数据"""
        print("正在导入电影和类型数据...")

        # 读取movies.csv
        movies_df = pd.read_csv('../ml-latest-small/movies.csv')
        print(f"找到 {len(movies_df)} 部电影")

        with self.driver.session() as session:
            for index, row in movies_df.iterrows():
                # 解析电影标题和年份
                title, year = self.parse_movie_title(row['title'])

                # 解析类型
                genres = row['genres'].split('|') if row['genres'] != '(no genres listed)' else []

                session.execute_write(
                    self._create_movie_and_genres,
                    row['movieId'], title, year, genres
                )

                if index % 100 == 0:
                    print(f"已处理 {index + 1} 部电影")

    def import_ratings(self):
        """导入用户评分数据"""
        print("正在导入评分数据...")

        ratings_df = pd.read_csv('../ml-latest-small/ratings.csv')
        print(f"找到 {len(ratings_df)} 条评分记录")

        with self.driver.session() as session:
            for index, row in ratings_df.iterrows():
                session.execute_write(
                    self._create_rating_relationship,
                    row['userId'], row['movieId'], row['rating'], row['timestamp']
                )

                if index % 1000 == 0:
                    print(f"已处理 {index + 1} 条评分")

    def import_tags(self):
        """导入标签数据"""
        print("正在导入标签数据...")

        tags_df = pd.read_csv('../ml-latest-small/tags.csv')
        print(f"找到 {len(tags_df)} 条标签记录")

        with self.driver.session() as session:
            for index, row in tags_df.iterrows():
                session.execute_write(
                    self._create_tag_relationship,
                    row['userId'], row['movieId'], row['tag'], row['timestamp']
                )

    @staticmethod
    def parse_movie_title(title):
        """解析电影标题和年份"""
        import re
        # 匹配标题中的年份，如 "Toy Story (1995)"
        match = re.search(r'^(.*?)\s*\((\d{4})\)\s*$', title)
        if match:
            movie_title = match.group(1).strip()
            year = int(match.group(2))
        else:
            movie_title = title
            year = None
        return movie_title, year

    @staticmethod
    def _create_movie_and_genres(tx, movie_id, title, year, genres):
        """创建电影节点和类型关系"""
        # 创建电影节点
        query = """
        MERGE (m:Movie {id: $movie_id})
        SET m.title = $title, m.year = $year
        WITH m
        UNWIND $genres AS genre
        MERGE (g:Genre {name: genre})
        MERGE (m)-[:IN_GENRE]->(g)
        """
        tx.run(query, movie_id=movie_id, title=title, year=year, genres=genres)

    @staticmethod
    def _create_rating_relationship(tx, user_id, movie_id, rating, timestamp):
        """创建用户评分关系"""
        query = """
        MERGE (u:User {id: $user_id})
        MERGE (m:Movie {id: $movie_id})
        MERGE (u)-[r:RATED]->(m)
        SET r.rating = $rating, r.timestamp = $timestamp
        """
        tx.run(query, user_id=user_id, movie_id=movie_id, rating=rating, timestamp=timestamp)

    @staticmethod
    def _create_tag_relationship(tx, user_id, movie_id, tag, timestamp):
        """创建用户标签关系"""
        query = """
        MERGE (u:User {id: $user_id})
        MERGE (m:Movie {id: $movie_id})
        MERGE (u)-[t:TAGGED]->(m)
        SET t.tag = $tag, t.timestamp = $timestamp
        """
        tx.run(query, user_id=user_id, movie_id=movie_id, tag=tag, timestamp=timestamp)


def main():
    # Neo4j连接配置 - 修改为你的配置
    NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

    # 创建导入器实例
    importer = MovieLensImporter(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)

    try:
        # 执行数据导入
        importer.import_all_data()

        # 验证数据导入
        importer.verify_import()

    except Exception as e:
        print(f"导入过程中出错: {e}")
    finally:
        importer.close()


def verify_import(self):
    """验证数据导入结果"""
    print("\n验证数据导入结果...")
    with self.driver.session() as session:
        # 统计节点数量
        result = session.execute_write(self._count_nodes)
        print(f"数据库中的节点数量: {result['total_nodes']}")
        print(f"电影数量: {result['movie_count']}")
        print(f"用户数量: {result['user_count']}")
        print(f"类型数量: {result['genre_count']}")

        # 统计关系数量
        rel_result = session.execute_write(self._count_relationships)
        print(f"评分关系数量: {rel_result['rating_count']}")
        print(f"标签关系数量: {rel_result['tag_count']}")


@staticmethod
def _count_nodes(tx):
    query = """
    MATCH (n)
    RETURN 
        count(n) as total_nodes,
        count(CASE WHEN n:Movie THEN 1 ELSE null END) as movie_count,
        count(CASE WHEN n:User THEN 1 ELSE null END) as user_count,
        count(CASE WHEN n:Genre THEN 1 ELSE null END) as genre_count
    """
    result = tx.run(query)
    return result.single()


@staticmethod
def _count_relationships(tx):
    query = """
    MATCH ()-[r]-()
    RETURN 
        count(CASE WHEN type(r) = 'RATED' THEN 1 ELSE null END) as rating_count,
        count(CASE WHEN type(r) = 'TAGGED' THEN 1 ELSE null END) as tag_count
    """
    result = tx.run(query)
    return result.single()


if __name__ == "__main__":
    main()