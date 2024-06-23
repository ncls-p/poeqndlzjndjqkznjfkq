import asyncio
import logging
import os
import time
from typing import List, Optional

import uvicorn
from fastapi import APIRouter, FastAPI, HTTPException, Request
from poe_api_wrapper import AsyncPoeApi
from pydantic import BaseModel

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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


class Message(BaseModel):
    content: str


class ChatCompletionRequest(BaseModel):
    model: str = "claude_3_igloo"
    messages: Optional[List[Message]] = None
    chatId: Optional[str] = None
    chatCode: Optional[str] = None
    msgPrice: Optional[float] = None
    file_path: Optional[str] = None
    suggest_replies: Optional[bool] = None
    timeout: Optional[int] = None


async def create_client():
    global client
    client = await AsyncPoeApi(
        tokens=dict(token.split(":") for token in TOKENS)
    ).create()


@router.post("/chat/completions")
@router.post("/v1/chat/completions")
async def chat_completions(request: Request, completion_request: ChatCompletionRequest):
    if completion_request.messages is not None:
        combined_message = " ".join(
            [msg.content for msg in completion_request.messages]
        )
    else:
        combined_message = ""
    res = ""

    try:
        # Convert chatId to int if it's not None, otherwise set a default value or handle it as needed
        chat_id_int = (
            int(completion_request.chatId)
            if completion_request.chatId is not None
            else None
        )
        # Ensure chat_id_int is not None or provide a default/fallback value as needed
        if chat_id_int is None:
            raise ValueError("chatId is required and must be an integer.")

        async for chunk in client.send_message(
            bot=completion_request.model,
            message=combined_message,
            chatId=chat_id_int,
            chatCode=(
                completion_request.chatCode
                if completion_request.chatCode is not None
                else ""
            ),
            msgPrice=(
                int(completion_request.msgPrice)
                if completion_request.msgPrice is not None
                else 0
            ),
            file_path=(
                [completion_request.file_path] if completion_request.file_path else []
            ),
            suggest_replies=completion_request.suggest_replies or False,
            timeout=completion_request.timeout or 0,
        ):
            res += chunk["response"]
    except ValueError as ve:
        logger.exception("Invalid chatId value")
        raise HTTPException(status_code=400, detail=f"Invalid chatId value: {str(ve)}")
    except Exception as e:
        logger.exception("Error while processing chat completions")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

    return {
        "id": "chatcmpl-9dG14JJJGp6LTPzKySM6AzQWZR9N2",
        "object": "chat.completion",
        "created": int(time.time()),
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
