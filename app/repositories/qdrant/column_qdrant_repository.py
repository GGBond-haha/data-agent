from dataclasses import asdict

from qdrant_client import AsyncQdrantClient
from qdrant_client.http.models import PointStruct, QueryResponse
from qdrant_client.models import VectorParams, Distance
from app.conf.app_config import app_config
from app.entities.column_info import ColumnInfo


class ColumnQdrantRepository:

    coll_name = "data-agent-column"

    def __init__(self, client: AsyncQdrantClient):
        self.client = client

    async def ensure_collection(self):
        if not await self.client.collection_exists(collection_name=self.coll_name):
            await self.client.create_collection(
                collection_name=self.coll_name,
                vectors_config=VectorParams(
                    size=app_config.qdrant.embedding_size,
                    distance=Distance.COSINE
                )
            )

    async def upsert(self, ids:list[str], embeddings:list[list[float]], payloads:list[ColumnInfo], batch_size:int=10):
        # 1、采用zip函数，按照“索引下标”打包为元组迭代器[(id,vector,payload),(id,vector,payload),(id,vector,payload)]
        zipped = list(zip(ids, embeddings, payloads))

        # 2、采用分批次保存向量数据点到qdrant
        for i in range(0, len(zipped), batch_size):
            batch = zipped[i: i+batch_size]
            points = [PointStruct(
                id=id,
                vector=embedding,
                payload=asdict(payload)
            ) for id, embedding, payload in batch]
            await self.client.upsert(collection_name=self.coll_name, points=points)

    async def search(self, embedding:list[float], score_threshold: float = 0.5, limit: int = 10) -> list[ColumnInfo]:
        result:QueryResponse = await self.client.query_points(collection_name=self.coll_name, query=embedding,
                                                score_threshold=score_threshold, limit=limit)

        # **point.payload 结构表达式，将Qdrant中payload字典{id: "abc"} 转为 id = "abc"
        return [ColumnInfo(**point.payload) for point in result.points]

