from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.auth import verify_token
from app.schemas import SearchRequest, SearchResponse, PostResult, CommentResult
from app.services.post_search import search_similar_posts
from app.services.comment_search import search_similar_comments

app = FastAPI(title="EA Writer Helpers", version="1.0.0")

@app.post("/search/posts", response_model=SearchResponse)
async def search_posts(
    request: SearchRequest,
    db: AsyncSession = Depends(get_db),
    token: str = Depends(verify_token)
):
    try:
        results = await search_similar_posts(
            db, request.query, request.limit, request.threshold
        )
        return SearchResponse(results=results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search/comments", response_model=SearchResponse)
async def search_comments(
    request: SearchRequest,
    db: AsyncSession = Depends(get_db),
    token: str = Depends(verify_token)
):
    try:
        results = await search_similar_comments(
            db, request.query, request.limit, request.threshold
        )
        return SearchResponse(results=results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy"}