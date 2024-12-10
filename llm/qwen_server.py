import asyncio
import logging
import dashscope
import json
import os
from typing import List
from fastapi import FastAPI
from openai import AsyncOpenAI
from pydantic import BaseModel, Field
from datetime import datetime

from starlette.responses import StreamingResponse

os.makedirs("log", exist_ok=True)
logging.basicConfig(format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s',
                    level=logging.DEBUG,
                    filename='log/llm_server.log',
                    filemode='a')
app = FastAPI()


dashscope.api_key = open("temp/key/qwen_key", "r").read()

os.environ["DASHSCOPE_API_KEY"] = dashscope.api_key


class ChatHistory(BaseModel):
    messages: List[dict] = Field(default=[{"role": "user", "content": "你好呀"}])


def save_txt(file_path, data):
    with open(file_path, "w") as f:
        f.write(data)


def save_json(file_path, data):
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(data, ensure_ascii=False))


# 创建异步客户端实例
fast_client = AsyncOpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"), base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)


@app.post("/fastchat")
async def chat_with_model(chat_history: ChatHistory):
    try:
        response = await fast_client.chat.completions.create(
            messages=chat_history.messages,
            # model="qwen-turbo",
            model="qwen-plus",
            # model="qwen-max",
            # model="qwen-long",
        )

        if not response:
            response = "timeout error"
            answer = "timeout error"
        else:
            answer = response.choices[0].message.content
        logging.info(f"request: {chat_history.messages}, response: {str(response)}")
    except:
        answer = "question error"
        logging.warning(f"request: {chat_history.messages}, response: 问题或回答中出现了违禁词")
    return answer


async def fetch_and_stream(messages):
    response = await fast_client.chat.completions.create(
        messages=messages, model="qwen-turbo", stream=True, stream_options={"include_usage": True}
    )
    usage = 0
    async for chunk in response:
        chuck_data = chunk.model_dump_json()
        chuck_data = json.loads(chuck_data)

        if chuck_data["usage"] is not None:
            usage = chuck_data["usage"]

        choices = chuck_data["choices"]
        if len(choices) > 0:
            chuck_str = choices[0]["delta"]["content"]
            yield chuck_str  # 继续传输数据

    # 最后一个chunk输出编码后的json字符串，以及结束标记
    yield f"<JSON_BEGIN>{json.dumps(usage)}<JSON_END>"


@app.post("/chat/stream")
async def chat_with_model(chat_history: ChatHistory):
    return StreamingResponse(fetch_and_stream(chat_history.messages), media_type="text/event-stream")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("qwen_server:app", host="127.0.0.1", port=8024, reload=True)
