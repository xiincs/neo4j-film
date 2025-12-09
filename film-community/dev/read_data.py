# 1. 下载 MovieLens ml-latest-small.zip
# 2. 创建数据导入脚本

import pandas as pd
from neo4j import GraphDatabase


class DataImporter:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def import_movielens_data(self):
        # 读取CSV文件
        movies_df = pd.read_csv('../ml-latest-small/movies.csv')
        ratings_df = pd.read_csv('../ml-latest-small/data/ratings.csv')

        with self.driver.session() as session:
            # 导入电影数据
            for _, movie in movies_df.iterrows():
                # 解析类型 "Action|Adventure|Sci-Fi" -> ["Action", "Adventure", "Sci-Fi"]
                genres = movie['genres'].split('|') if movie['genres'] != '(no genres listed)' else []

                session.execute_write(self._create_movie,
                                      movie['movieId'],
                                      movie['title'],
                                      genres)

            # 导入评分数据（创建用户和关系）
            # ... 类似逻辑

    @staticmethod
    def _create_movie(tx, movie_id, title, genres):
        query = """
        CREATE (m:Movie {id: $movie_id, title: $title})
        WITH m
        UNWIND $genres AS genre
        MERGE (g:Genre {name: genre})
        MERGE (m)-[:BELONGS_TO]->(g)
        """
        tx.run(query, movie_id=movie_id, title=title, genres=genres)


# 运行导入
importer = DataImporter("bolt://localhost:7687", "neo4j", "password")
importer.import_movielens_data()