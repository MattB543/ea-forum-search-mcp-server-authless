import os
from typing import List
from openai import AsyncOpenAI

async def get_query_embedding(query: str) -> str:
    print(f"DEBUG: Getting OpenAI embedding for query: {query}")
    client = AsyncOpenAI(api_key=os.getenv("OPENAI_KEY"))
    
    response = await client.embeddings.create(
        model="text-embedding-3-small",
        input=query
    )
    embedding = response.data[0].embedding
    print(f"DEBUG: Got {len(embedding)}-dimensional embedding from OpenAI")
    
    embedding_str = "[" + ",".join(map(str, embedding)) + "]"
    print(f"DEBUG: Final embedding length: {len(embedding)}, first 3 values: {embedding[:3]}")
    return embedding_str