from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.schemas import PostResult
from app.services.search_utils import get_query_embedding

async def search_similar_posts(
    db: AsyncSession, 
    query: str, 
    limit: int = 10, 
    threshold: float = 0.7
) -> List[PostResult]:
    embedding_str = await get_query_embedding(query)
    print(f"DEBUG: embedding_str = {embedding_str[:50]}...")
    
    sql = text(f"""
        SELECT 
            id, post_id, title, page_url, author_display_name, posted_at,
            1 - (title_embedding_gemini <=> '{embedding_str}') as similarity_score
        FROM fellowship_mvp 
        WHERE title_embedding_gemini IS NOT NULL
            AND 1 - (title_embedding_gemini <=> '{embedding_str}') >= {threshold}
        ORDER BY similarity_score DESC
        LIMIT {limit}
    """)
    
    result = await db.execute(sql)
    rows = result.fetchall()
    
    results = []
    for row in rows:
        score = row.similarity_score
        if score is None:
            continue
        try:
            score_float = float(score)
            if not (-1 <= score_float <= 1) or score_float != score_float:
                continue
            results.append(PostResult(
                id=row.id,
                post_id=row.post_id,
                title=row.title,
                url=row.page_url,
                author=row.author_display_name,
                posted_at=row.posted_at,
                similarity_score=round(score_float, 6)
            ))
        except (ValueError, OverflowError):
            continue
    return results