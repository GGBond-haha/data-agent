import asyncio
from typing import Optional

from langchain_huggingface import HuggingFaceEndpointEmbeddings

from app.conf.app_config import EmbeddingConfig, app_config


"""
全称：向量嵌入服务客户端管理器

1、名称含义
`embedding` = 向量嵌入（把文本转换为向量的 AI 技术），`client` = 客户端，`manager` = 管理器

2、核心作用
对接 HuggingFace 格式的向量嵌入服务接口，负责将文本转化为向量数据，是整个项目语义能力的基础组件，专门为下游 Qdrant 向量检索提供向量生成能力。

"""


class EmbeddingClientManager:
    """
    向量嵌入客户端管理器类
    用于管理 HuggingFaceEndpointEmbeddings 客户端的初始化和配置
    """

    def __init__(self, config: EmbeddingConfig):
        """
        初始化嵌入式客户端管理器

        Args:
            config (EmbeddingConfig): 嵌入服务的配置对象，包含 host、port 等关键配置
        """
        # 保存嵌入服务配置
        self.config = config
        # 初始化向量嵌入客户端对象，初始值为 None，后续通过 init 方法初始化
        self.client: Optional[HuggingFaceEndpointEmbeddings] = None

    def _get_url(self):
        """
        私有方法：把配置里的 host 和 port 拼接成 http://host:port 格式的完整服务地址。

        Returns:
            str: 拼接后的嵌入式服务地址（http://host:port 格式）
        """
        return f"http://{self.config.host}:{self.config.port}"

    def init(self):
        """
        初始化 HuggingFaceEndpointEmbeddings 客户端
        将拼接好的服务 URL 作为模型地址传入客户端
        """
        self.client = HuggingFaceEndpointEmbeddings(
            model=self._get_url()
        )

# 创建 EmbeddedClientManager 实例（全局变量），传入应用配置中的嵌入服务配置
embedding_client_manager = EmbeddingClientManager(app_config.embedding)


if __name__ == '__main__':
    embedding_client_manager.init()
    client = embedding_client_manager.client

    def test_sync_embedding():
        # embedding_query = client.embed_query("你好")
        embedding_query = client.embed_documents(["你好", "世界"])
        print(len(embedding_query))
        print(embedding_query)

    # test_sync_embedding()

    async def test_async_embedding():
        # query = await client.aembed_query("苹果")
        # print(query)

        # 异步接口：批量对多条文档文本生成向量，await等待异步执行完成
        embed_documents_ = await client.aembed_documents(["苹果", "香蕉"])
        print(embed_documents_)

    asyncio.run(test_async_embedding())