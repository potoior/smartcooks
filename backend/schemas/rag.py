from pydantic import BaseModel
from typing import Optional


class QuestionRequest(BaseModel):
    question: str
    image_name: Optional[str] = None


class SearchRequest(BaseModel):
    category: str
    query: Optional[str] = ""


class AnswerResponse(BaseModel):
    answer: str
    route_type: str
    documents: list


class StreamChunk(BaseModel):
    content: str
    route_type: Optional[str] = None
    documents: Optional[list] = None
    done: bool = False
