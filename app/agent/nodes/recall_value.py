from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langgraph.runtime import Runtime
from app.agent.context import DataAgentContext
from app.agent.llm import llm
from app.agent.state import DataAgentState
from app.core.log import logger
from app.entities.value_info import ValueInfo
from app.prompt.prompt_loader import load_prompt


async def recall_value(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    """召回字段取值，获取真实有效字段取值，用于解决llm生成SQL where 部分字段的取值"""
    # 1、获取流写入器对象
    writer = runtime.stream_writer
    writer({"type": "progress", "step": "召回字段取值", "status": "running"})

    try:
        # 2、具体逻辑
        # 2.1 获取state中用户问题、“抽取关键词节点”关键词列表
        query = state["query"]
        keywords = state["keywords"]
        # 2.2 对原问题通过llm扩充关键词
        prompt = PromptTemplate(template=load_prompt("extend_keywords_for_value_recall"), input_variables=["query"])
        chain = prompt | llm | JsonOutputParser()
        result = await chain.ainvoke({"query": query})
        # 2.3 最终关键词列表=llm扩充后+state中关键词列表（去重）
        keywords = list(set(keywords + result))
        # 2.4 初始化字段取值字典，字典key=字段取值ID，value=字段取值对象
        retrieved_values_dict: dict[str, ValueInfo] = {}
        # 2.5 从runtime中获取操作ES持久层对象
        value_es_repository = runtime.context["value_es_repository"]
        # 2.6 遍历关键词列表，执行全文检索，处理结果
        if keywords:
            for keyword in keywords:
                value_infos: list[ValueInfo] = await value_es_repository.search(keyword)
                for value_info in value_infos:
                    value_id = value_info.id
                    if value_id not in retrieved_values_dict:
                        retrieved_values_dict[value_id] = value_info

        writer({"type": "progress", "step": "召回字段取值", "status": "success"})
        logger.info(f"字段取值召回成功：{list(retrieved_values_dict.keys())}")
        # 2.7 更新state中"retrieved_values"
        return {"retrieved_values": list(retrieved_values_dict.values())}

    except Exception as e:
        logger.error(f"召回字段取值发生异常：{str(e)}")
        writer({"type": "progress", "step": "召回字段取值", "status": "error"})
        raise
