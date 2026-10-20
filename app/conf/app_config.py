from dataclasses import dataclass
from pathlib import Path


from omegaconf import OmegaConf
from typing import Optional  # 新增：导入可选类型



# 日志配置
@dataclass
class File:
    enable: bool
    level: str
    path: str
    rotation: str
    retention: str

@dataclass
class Console:
    enable: bool
    level: str

@dataclass
class LoggingConfig:
    file: File
    console: Console

# 数据库配置
@dataclass
class DBConfig:
    host: str
    port: int
    user: str
    password: str
    database: str

@dataclass
class QdrantConfig:
    host: str
    port: int
    embedding_size: int

@dataclass
class EmbeddingConfig:
    host: str
    port: int
    model: str

@dataclass
class ESConfig:
    host: str
    port: int
    index_name: str

@dataclass
class LLMConfig:
    model_name: str
    api_key: str  # 修改：声明为可选字符串，允许为 None


@dataclass
class AppConfig:
    logging: LoggingConfig
    db_meta: DBConfig
    db_dw: DBConfig
    qdrant: QdrantConfig
    embedding: EmbeddingConfig
    es: ESConfig
    llm: LLMConfig


# 加载配置
context = OmegaConf.load(Path(__file__).parents[2] / "conf" / "app_config.yaml")
structured = OmegaConf.structured(AppConfig)
app_config: AppConfig = OmegaConf.to_object(OmegaConf.merge(structured, context))

# if __name__ == "__main__":
    # from app.core.log import logger
    # # print(app_config)
    # # print(app_config.db_dw.host, app_config.db_dw.database)
    #
    # logger.debug("Debug日志")
    # logger.info("Info日志")
    # logger.warning("Warning日志")
    # logger.error("Error日志")

