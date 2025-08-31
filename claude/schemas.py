from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class SearchRequest(BaseModel):
    query: str
    limit: int = 10
    threshold: float = 0.7

class PostResult(BaseModel):
    id: int
    post_id: str
    title: str
    url: Optional[str]
    author: Optional[str]
    posted_at: Optional[datetime]
    similarity_score: float

class CommentResult(BaseModel):
    id: int
    comment_id: str
    post_id: str
    content: Optional[str]
    author: Optional[str]
    posted_at: Optional[datetime]
    similarity_score: float

class SearchResponse(BaseModel):
    results: List[PostResult | CommentResult]