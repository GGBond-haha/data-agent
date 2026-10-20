from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.runtime import Runtime
from langgraph.config import get_stream_writer

from app.agent.context import DataAgentContext
from app.agent.llm import llm
from app.agent.state import DataAgentState
from app.core.log import logger
from app.entities.column_info import ColumnInfo
from app.prompt.prompt_loader import load_prompt


async def recall_column(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    # 1、获取流写入器对象
    writer = get_stream_writer()
    # 2、写进度：正在处理中
    writer({"type": "progress", "step": "召回字段", "status": "running"})

    try:
        # 1、基于原query通过llm进行关键词扩展
        query = state["query"]
        # 1.1 构建提示词运行单元
        prompt = PromptTemplate(template=load_prompt("extend_keywords_for_column_recall"), input_variables=["query"])
        # 1.2 构建输出解析器
        output = JsonOutputParser()
        # 1.3 构建调用链，异步执行
        chain = prompt | llm | output
        result = await chain.ainvoke({"query": query})
        logger.info(f"recall_column节点，大模型扩充字段结果：{result}")

        # 2、去重拼接，合并原始关键词与扩展关键词
        keywords = state["keywords"]
        keywords = list(set(result + keywords))

        # 3、遍历关键词列表，根据每个关键词进行向量语义检索
        # 3.1 创建字段信息字典 key:字段ID value：字段信息
        retrieved_columns_map: dict[str, ColumnInfo] = {}
        # 3.2 从runtime获取embedding客户端与向量库操作对象
        embedding_client = runtime.context["embedding_client"]
        column_qdrant_repository = runtime.context["column_qdrant_repository"]

        for keyword in keywords:
            # 3.3 对关键词转为向量
            embedding = await embedding_client.aembed_query(keyword)
            # 3.4 检索字段信息向量集合
            column_infos: list[ColumnInfo] = await column_qdrant_repository.search(embedding)
            # 3.5 按字段ID去重存入字典
            for column_info in column_infos:
                column_id = column_info.id
                if column_id not in retrieved_columns_map:
                    retrieved_columns_map[column_id] = column_info

        # 4、返回召回结果
        writer({"type": "progress", "step": "召回字段", "status": "success"})
        logger.info(f"召回字段成功，字段信息：{list(retrieved_columns_map.keys())}")
        return {"retrieved_columns": list(retrieved_columns_map.values())}

    except Exception as e:
        logger.error(f"召回字段节点执行异常：{str(e)}")
        writer({"type": "progress", "step": "召回字段", "status": "error"})
        raise
