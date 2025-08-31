from sqlalchemy import Column, Integer, String, Text, DateTime, ARRAY
from pgvector.sqlalchemy import Vector
from app.database import Base

class Post(Base):
    __tablename__ = "fellowship_mvp"
    
    id = Column(Integer, primary_key=True)
    post_id = Column(String(255), nullable=False)
    title = Column(Text, nullable=False)
    page_url = Column(Text)
    author_display_name = Column(String(255))
    posted_at = Column(DateTime)
    title_embedding_gemini = Column(Vector(1536))
    summary_embedding_gemini = Column(Vector(1536))

class Comment(Base):
    __tablename__ = "fellowship_mvp_comments"
    
    id = Column(Integer, primary_key=True)
    comment_id = Column(String(255), nullable=False)
    post_id = Column(String(255), nullable=False)
    markdown_content = Column(Text)
    author_display_name = Column(String(255))
    posted_at = Column(DateTime)
    content_embedding = Column(Vector(1536))