"""
schemas.py의 CommunityCreateRequest / CommunityPost 필드에 맞춘 테이블.

주의: CommunityCreateRequest에는 nickname이 없고 password만 있음.
     -> author(작성자 표시명)는 서버가 자동으로 "익명1234" 식으로 만들어서 저장.
     -> password는 그대로 저장하면 안 되니 해시해서 hashed_password 컬럼에 저장.
"""

from sqlalchemy import Column, Integer, String, DateTime, func
from app.database import Base


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    content = Column(String(2000), nullable=False)
    district_name = Column(String(20), default="전체", index=True)
    author = Column(String(20), nullable=False)          # 자동 생성되는 "익명1234" 같은 표시명
    hashed_password = Column(String(64), nullable=False)  # 평문 저장 금지, sha256 해시로 저장
    view_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
