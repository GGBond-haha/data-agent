from sqlalchemy import Result, text
from sqlalchemy.ext.asyncio import AsyncSession

class DWMySQLRepository:
    """跟MySQL数据库（数仓数据库）交互持久层，必须通过Session对象进行CRUD"""
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_column_type_by_table_id(self, table_id: str) -> dict[str, str]:
        """根据表ID、表名称查询该表下所有字段信息。目的获取字段数据类型"""
        sql = f"SHOW COLUMNS FROM {table_id}"
        result: Result = await self.session.execute(text(sql))
        # 查询结果是多列多行 返回列表 包装对象
        return {row.Field: row.Type for row in result.fetchall()}

    async def get_column_values_by_table_id(self, table_id: str, column_name: str, limit: int = 10) -> list[str]:
        """查询指定个数某张表某个字段取值"""
        sql = f"SELECT DISTINCT {column_name} FROM {table_id} LIMIT {limit}"
        result: Result = await self.session.execute(text(sql))
        # 结果：一列多行
        return result.scalars().fetchall()

    async def get_db_info(self) -> dict[str, str]:
        """查询数仓数据库版本以及SQL方言"""
        # 1、获取数据库版本
        sql = "SELECT VERSION()"
        result = await self.session.execute(text(sql))
        version = result.scalar()
        # 2、获取数据库方言
        dialect = self.session.get_bind().dialect.name
        # 3、返回结果
        return {"version": version, "dialect": dialect}

    async def validate_sql(self, sql: str) -> None:
        """预校验SQL语法合法性，不合法会抛出异常"""
        # 通过EXPLAIN执行计划预检查SQL语法
        await self.session.execute(text(f"EXPLAIN {sql}"))

    async def execute_sql(self, sql: str) -> list[dict]:
        """执行SQL并返回字典格式的查询结果"""
        result: Result = await self.session.execute(text(sql))
        # 将每行结果映射为字典，封装为列表返回
        return [dict(row_mapping) for row_mapping in result.mappings().fetchall()]
