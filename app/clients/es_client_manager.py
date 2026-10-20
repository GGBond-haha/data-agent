import asyncio
from typing import Optional

from elasticsearch import AsyncElasticsearch

from app.conf.app_config import ESConfig, app_config



"""

全称：Elasticsearch 异步客户端管理器

名称含义
`es` = Elasticsearch（开源全文搜索引擎），`client` = 客户端，`manager` = 管理器

核心作用
封装 Elasticsearch 的异步客户端连接，负责 ES 索引管理、文档写入、全文检索等能力，支撑项目的商品全文检索、关键词模糊搜索、品牌、价格结构化筛选等业务场景。

"""

class ESClientManager:
    """Elasticsearch异步客户端管理器：封装ES客户端的初始化、连接、关闭逻辑"""
    def __init__(self, config: ESConfig):
        self.config = config
        self.client: Optional[AsyncElasticsearch] = None

    def _get_url(self):
        return f"http://{self.config.host}:{self.config.port}"

    def init(self):
        self.client = AsyncElasticsearch(
            hosts=self._get_url(),
            # 设置请求超时时间为600秒，适配大查询或批量写入场景
            request_timeout=600
        )

    # 异步资源释放方法，安全关闭 ES 客户端连接，避免连接泄漏
    async def close(self):
        # 判断客户端是否已实例化，避免空对象调用报错
        if self.client:
            await self.client.close()        # 异步关闭ES客户端连接

es_client_manager = ESClientManager(app_config.es)


if __name__ == '__main__':
    es_client_manager.init()
    client = es_client_manager.client

    idx_name = "test"

    async def test_index():
        """采用显示映射创建索引库"""
        # 先判断指定名称的索引是否已存在，避免重复创建报错
        if not await client.indices.exists(index=idx_name):
            # 异步调用索引创建接口，创建索引并定义字段映射
            resp = await client.indices.create(
                # 指定要创建的索引名
                index=idx_name,
                # 定义索引的字段映射规则
                mappings={
                    "dynamic": False,
                    "properties": {
                        "id": {
                            "type": "long"
                        },
                        "name": {
                            "type": "text",
                            "analyzer": "ik_max_word"
                        },
                        "brand": {
                            "type": "keyword",
                        },
                        "image": {
                            "type": "keyword",
                            "index": False
                        },
                        "price":{
                            "type": "float"
                        }
                    }
                }
            )
            print(resp)
        await es_client_manager.client.close()

    # asyncio.run(test_index())

    async def test_cod():
        await client.index(
            index=idx_name,
            document={
                "id": 3,
                "name": "小米su7 Ultra长续航版本",
                "brand": "小米汽车",
                "image": "www.xxx.xxx/xm.png",
                "price": 406000
            }
        )
        await client.bulk(
            operations=[
                {
                    "index": {
                        "_index": idx_name
                    }
                },
                {
                    "id": 1,
                    "name": "小米17ProMax 1T 雪花白 8GB+16GB",
                    "brand": "小米",
                    "image": "www.xxx.xxx/xm.png",
                    "price": 5000
                },
                {
                    "index": {
                        "_index": idx_name
                    }
                },
                {
                    "id": 2,
                    "name": "小米17ProMax 1T 冰晶蓝 8GB+16GB",
                    "brand": "小米",
                    "image": "www.xxx.xxx/xm.png",
                    "price": 6000
                }
            ]
        )
        await es_client_manager.client.close()
    asyncio.run(test_cod())


