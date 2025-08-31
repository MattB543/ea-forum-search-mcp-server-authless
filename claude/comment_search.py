import os
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from openai import OpenAI
from app.models import Comment
from app.schemas import CommentResult

async def get_query_embedding(query: str) -> List[float]:
    from openai import AsyncOpenAI
    client = AsyncOpenAI(api_key=os.getenv("OPENAI_KEY"))
    response = await client.embeddings.create(
        model="text-embedding-3-small",
        input=query
    )
    return response.data[0].embedding

async def search_similar_comments(
    db: AsyncSession, 
    query: str, 
    limit: int = 10, 
    threshold: float = 0.7
) -> List[CommentResult]:
    query_embedding = await get_query_embedding(query)
    
    embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"
    
    sql = text(f"""
        SELECT 
            id, comment_id, post_id, markdown_content, author_display_name, posted_at,
            1 - (content_embedding <=> '{embedding_str}') as similarity_score
        FROM fellowship_mvp_comments 
        WHERE content_embedding IS NOT NULL
            AND 1 - (content_embedding <=> '{embedding_str}') >= {threshold}
        ORDER BY similarity_score DESC
        LIMIT {limit}
    """)
    
    result = await db.execute(sql)
    
    rows = result.fetchall()
    return [
        CommentResult(
            id=row.id,
            comment_id=row.comment_id,
            post_id=row.post_id,
            content=row.markdown_content,
            author=row.author_display_name,
            posted_at=row.posted_at,
            similarity_score=round(float(row.similarity_score), 6)
        )
        for row in rows
    ]