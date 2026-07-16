"""
schemas.py의 CommunityCreateRequest/Update/Delete에 맞춘 repository.
수정/삭제는 반드시 비밀번호 검증을 통과해야만 실행됨.
"""

import random

from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.post import Post
from app.schemas import CommunityCreateRequest, CommunityUpdateRequest
from app.utils.security import hash_password, verify_password


class WrongPasswordError(Exception):
    """비밀번호가 틀렸을 때 발생시키는 예외 (라우터에서 403으로 변환)"""


class PostRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, data: CommunityCreateRequest) -> Post:
        post = Post(
            title=data.title,
            content=data.content,
            district_name=data.district_name,
            author=f"익명{random.randint(1000, 9999)}",  # 닉네임 입력이 없으니 서버가 자동 생성
            hashed_password=hash_password(data.password),
        )
        self.db.add(post)
        self.db.commit()
        self.db.refresh(post)
        return post

    def get_all(self, skip: int = 0, limit: int = 20, district_name: str | None = None) -> list[Post]:
        query = self.db.query(Post)
        if district_name and district_name != "전체":
            query = query.filter(Post.district_name == district_name)
        return query.order_by(desc(Post.created_at)).offset(skip).limit(limit).all()

    def get_by_id(self, post_id: int) -> Post | None:
        post = self.db.query(Post).filter(Post.id == post_id).first()
        if post:
            post.view_count += 1
            self.db.commit()
            self.db.refresh(post)
        return post

    def update(self, post_id: int, data: CommunityUpdateRequest) -> Post | None:
        post = self.db.query(Post).filter(Post.id == post_id).first()
        if not post:
            return None
        if not verify_password(data.password, post.hashed_password):
            raise WrongPasswordError()
        post.title = data.title
        post.content = data.content
        post.district_name = data.district_name
        self.db.commit()
        self.db.refresh(post)
        return post

    def delete(self, post_id: int, password: str) -> bool | None:
        """반환값: True=삭제됨, False=게시글 없음, None은 없음(예외로 처리)"""
        post = self.db.query(Post).filter(Post.id == post_id).first()
        if not post:
            return False
        if not verify_password(password, post.hashed_password):
            raise WrongPasswordError()
        self.db.delete(post)
        self.db.commit()
        return True
