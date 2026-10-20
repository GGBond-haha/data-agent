import jieba.analyse
from langgraph.runtime import Runtime
from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from app.core.log import logger


async def extract_keywords(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    """Graph入口节点：将用户问题进行抽取关键词"""
    # 获取流式输出器
    writer = runtime.stream_writer
    # 输出进度：开始执行
    writer({"type": "progress", "step": "抽取关键字", "status": "running"})
    try:
        # 获取用户查询问题（移入try内，确保异常被捕获）
        query = state["query"]

        # 定义返回指定词性的元组
        allow_pos = (
            "n",  # 名词: 数据、服务器、表格
            "nr",  # 人名: 张三、李四
            "ns",  # 地名: 北京、上海
            "nt",  # 机构团体名: 政府、学校、某公司
            "nz",  # 其他专有名词: Unicode、哈希算法、诺贝尔奖
            "v",  # 动词: 运行、开发
            "vn",  # 名动词: 工作、研究
            "a",  # 形容词: 美丽、快速
            "an",  # 名形词: 难度、合法性、复杂度
            "eng",  # 英文
            "i",  # 成语
            "l",  # 常用固定短语
        )

        # 使用jieba从用户的查询信息中提取关键词，基于TF-IDF算法实现
        keywords = jieba.analyse.extract_tags(query, topK=10, allowPOS=allow_pos)

        # 有序去重，保证原query在首位
        seen = set()
        result = []
        for word in [query] + keywords:
            if word not in seen:
                seen.add(word)
                result.append(word)
        keywords = result

        writer({"type": "progress", "step": "抽取关键字", "status": "success"})
        logger.info(f"抽取关键字成功：{keywords}")

        # 更新state节点数据
        return {"keywords": keywords}
    except Exception as e:
        logger.error(f"抽取关键字异常：{str(e)}")
        writer({"type": "progress", "step": "抽取关键字", "status": "error"})
        raise
