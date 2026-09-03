# from pydantic import BaseModel, Field


# class ChatRequest(BaseModel):
#     message: str = Field(min_length=1, max_length=2000)
#     session_id: str = Field(default="default", max_length=100)


# class ChatResponse(BaseModel):
#     response: str
#     order_id: int | None = None

from typing import Optional
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    session_id: str = Field(default="default", max_length=100)


class ChatResponse(BaseModel):
    response: str
    order_id: Optional[int] = None