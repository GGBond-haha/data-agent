import asyncio

from fastapi import APIRouter
from pydantic import BaseModel
# 导入流式响应类，用于返回流式数据
from fastapi.responses import StreamingResponse

hello_router = APIRouter(tags=["测试路由接口"])

@hello_router.get("/hello/{age}")

async def hello(age: int,name: str):
    return f"hello fastAPI，我是{name}，年龄{age}岁"

class UserInfo(BaseModel):
    name: str
    password: str

@hello_router.post("/login")
async def login(user_info: UserInfo):
    return f"登录信息：{user_info}"


# 模拟视频流生成器函数（异步）
async def fake_video_streamer():
    # 循环生成10次模拟视频字节数据
    for i in range(10):
        yield b"some fake video bytes"
        await asyncio.sleep(0.5)

# 定义根路径GET接口
@hello_router.get("/")
async def main():
    # 返回流式响应，传入视频流生成器
    return StreamingResponse(fake_video_streamer())

async def mock_answer():
    for i in range(10):
        # 添加睡眠，演示延时效果
        await asyncio.sleep(1)
        yield f"data: stage:{i}\n\n"


@hello_router.get("/test_query")
async def test_query():
   return StreamingResponse(mock_answer(), media_type="text/event-stream")