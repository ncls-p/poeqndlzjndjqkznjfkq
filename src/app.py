import asyncio
import os
import time

import uvicorn
from fastapi import APIRouter, FastAPI, Request
from poe_api_wrapper import AsyncPoeApi
from pydantic import BaseModel

app = FastAPI()
router = APIRouter()

TOKENS = os.environ.get("TOKENS", "").split(",")
MODELS = [
    {
        "id": "claude_3_igloo",
        "object": "model",
        "created": 1683758102,
        "owned_by": "openai-internal",
    },
    {
        "id": "claude_3_igloo_200k",
        "object": "model",
        "created": 1699046015,
        "owned_by": "system",
    },
    {"id": "gpt4_o", "object": "model", "created": 1706037612, "owned_by": "system"},
    {
        "id": "code_llama_34b_instruct",
        "object": "model",
        "created": 1706037777,
        "owned_by": "system",
    },
    {"id": "acouchy", "object": "model", "created": 1712361441, "owned_by": "system"},
]


class ChatCompletionRequest(BaseModel):
    message: str
    model: str


async def create_client():
    global client
    client = await AsyncPoeApi(
        tokens=dict(token.split(":") for token in TOKENS)
    ).create()


@router.post("/chat/completions")
@router.post("/v1/chat/completions")
async def chat_completions(request: Request, completion_request: ChatCompletionRequest):
    print(request.headers)
    print(request.query_params)
    print(request.body)
    res = ""
    async for chunk in client.send_message(
        bot=completion_request.model, message=completion_request.message
    ):
        res += chunk["response"]
    return {
        "id": "chatcmpl-9dG14JJJGp6LTPzKySM6AzQWZR9N2",
        "object": "chat.completion",
        "created": time.time(),
        "model": completion_request.model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": res},
                "logprobs": None,
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 9, "completion_tokens": 9, "total_tokens": 18},
        "system_fingerprint": None,
    }


@router.get("/models")
@router.get("/v1/models")
async def get_models():
    return {"object": "list", "data": MODELS}


async def main():
    app.include_router(router)
    await create_client()
    config = uvicorn.Config(app, host="0.0.0.0", port=8000)
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())
