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
    print(f"DEBUG: Threshold: {threshold}, Limit: {limit}")
    
    sql = text(f"""
        SELECT 
            id, post_id, title, page_url, author_display_name, posted_at,
            (title_embedding <=> '{embedding_str}') as cosine_distance
        FROM fellowship_mvp 
        WHERE title_embedding IS NOT NULL
        ORDER BY cosine_distance ASC
        LIMIT {limit}
    """)
    
    print(f"DEBUG: Executing SQL query...")
    result = await db.execute(sql)
    rows = result.fetchall()
    print(f"DEBUG: Found {len(rows)} rows")
    
    results = []
    for i, row in enumerate(rows):
        distance = row.cosine_distance
        print(f"DEBUG: Row {i} - distance: {distance}, type: {type(distance)}")
        if distance is None:
            print(f"DEBUG: Row {i} - skipped (None)")
            continue
        try:
            distance_float = float(distance)
            print(f"DEBUG: Row {i} - distance_float: {distance_float}")
            if distance_float != distance_float:  # NaN check
                print(f"DEBUG: Row {i} - skipped (NaN)")
                continue
            
            # Convert distance to similarity score
            similarity_score = 1.0 - distance_float
            print(f"DEBUG: Row {i} - similarity_score: {similarity_score}")
            
            # Apply threshold
            if similarity_score < threshold:
                print(f"DEBUG: Row {i} - skipped (below threshold {threshold})")
                continue
                
            results.append(PostResult(
                id=row.id,
                post_id=row.post_id,
                title=row.title,
                url=row.page_url,
                author=row.author_display_name,
                posted_at=row.posted_at,
                similarity_score=round(similarity_score, 6)
            ))
            print(f"DEBUG: Row {i} - added to results")
        except (ValueError, OverflowError) as e:
            print(f"DEBUG: Row {i} - skipped (error: {e})")
            continue
    print(f"DEBUG: Returning {len(results)} results")
    return results