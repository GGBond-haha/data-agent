from dataclasses import asdict

from elastic_transport import ObjectApiResponse
from elasticsearch import AsyncElasticsearch
from app.entities.value_info import ValueInfo


class ValueESRepository:
    """操作字段取值ES持久层类"""

    idx_name = "data-agent-column"
    es_index_mappings = {
        "dynamic": False,
        "properties": {
            "id": {"type": "keyword"},
            "value": {"type": "text", "analyzer": "ik_max_word", "search_analyzer": "ik_max_word"},
            "column_id": {"type": "keyword"}
        }
    }

    def __init__(self, client: AsyncElasticsearch):
        self.client = client

    async def ensure_index(self):
        if not await self.client.indices.exists(index=self.idx_name):
            await self.client.indices.create(
                index=self.idx_name,
                mappings=self.es_index_mappings
            )

    async def upsert(self, value_infos: list[ValueInfo], batch_size=10):
        for i in range(0, len(value_infos), batch_size):
            batch = value_infos[i: i + batch_size]
            operations: list = []
            for value_info in batch:
                operations.append({
                    "index": {
                        "_index": self.idx_name,
                        "_id": value_info.id
                    }
                })
                operations.append(asdict(value_info))
                await self.client.bulk(operations=operations)

    async def search(self, keyword: str, score: float = 0.6, limit: int = 10) -> list[ValueInfo]:
        # 1、执行全文检索
        result = await self.client.search(
            index=self.idx_name,
            query={
                "match": {
                    "value": keyword
                }
            },
            min_score=score,
            size=limit
        )
        # 2、兼容不同版本ES客户端，统一取hits
        if hasattr(result, 'body'):
            hits = result.body.get("hits", {}).get("hits", [])
        else:
            hits = result.get("hits", {}).get("hits", [])

        # 3、明确字段构造ValueInfo对象，避免**解包的隐性问题
        return [
            ValueInfo(
                id=hit["_source"]["id"],
                value=hit["_source"]["value"],
                column_id=hit["_source"]["column_id"]
            )
            for hit in hits
        ]






















