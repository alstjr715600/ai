from sqlalchemy import Column, Integer, String, DateTime, func
from app.database import Base


class Comment(Base):
    __tablename__ = "comments"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # 어느 게시글의 댓글인지
    post_id = Column(
        Integer,
        nullable=False,
        index=True
    )

    content = Column(
        String(1000),
        nullable=False
    )

    author = Column(
        String(20),
        nullable=False
    )

    # 비밀번호 해시 저장
    hashed_password = Column(
        String(64),
        nullable=False
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )