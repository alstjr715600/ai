import hashlib

from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.post import Post
from app.models.comment import Comment
from app.schemas import (
    CommunityCreateRequest,
    CommunityDeleteRequest,
    CommunityUpdateRequest
)


router = APIRouter(
    prefix="/community/posts",
    tags=["Community"]
)


# =========================
# 비밀번호 해시
# =========================

def hash_password(password: str):
    return hashlib.sha256(
        password.encode()
    ).hexdigest()


# =========================
# 게시글 목록
# =========================

@router.get("")
def get_posts(
    district: str | None = None,
    db: Session = Depends(get_db)
):

    query = db.query(Post)

    if district and district != "전체":
        query = query.filter(
            Post.district_name == district
        )

    posts = query.order_by(
        Post.id.desc()
    ).all()

    return posts



# =========================
# 게시글 상세
# =========================

@router.get("/{post_id}")
def get_post(
    post_id: int,
    db: Session = Depends(get_db)
):

    post = db.query(Post).filter(
        Post.id == post_id
    ).first()


    if not post:
        raise HTTPException(
            status_code=404,
            detail="게시글을 찾을 수 없습니다."
        )


    post.view_count += 1
    db.commit()
    db.refresh(post)


    return post



# =========================
# 게시글 작성
# =========================

@router.post(
    "",
    status_code=status.HTTP_201_CREATED
)
def create_post(
    request: CommunityCreateRequest,
    db: Session = Depends(get_db)
):

    post = Post(
        title=request.title,
        content=request.content,
        district_name=request.district_name,
        author="익명",
        hashed_password=hash_password(
            request.password
        )
    )


    db.add(post)
    db.commit()
    db.refresh(post)


    return post



# =========================
# 게시글 수정
# =========================

@router.put("/{post_id}")
def update_post(
    post_id: int,
    request: CommunityUpdateRequest,
    db: Session = Depends(get_db)
):

    post = db.query(Post).filter(
        Post.id == post_id
    ).first()


    if not post:
        raise HTTPException(
            status_code=404,
            detail="게시글을 찾을 수 없습니다."
        )


    if post.hashed_password != hash_password(
        request.password
    ):
        raise HTTPException(
            status_code=403,
            detail="비밀번호가 일치하지 않습니다."
        )


    post.title = request.title
    post.content = request.content
    post.district_name = request.district_name


    db.commit()
    db.refresh(post)


    return post



# =========================
# 게시글 삭제
# =========================

@router.delete("/{post_id}")
def delete_post(
    post_id: int,
    request: CommunityDeleteRequest,
    db: Session = Depends(get_db)
):

    post = db.query(Post).filter(
        Post.id == post_id
    ).first()


    if not post:
        raise HTTPException(
            status_code=404,
            detail="게시글을 찾을 수 없습니다."
        )


    if post.hashed_password != hash_password(
        request.password
    ):
        raise HTTPException(
            status_code=403,
            detail="비밀번호가 일치하지 않습니다."
        )


    # 댓글 같이 삭제
    db.query(Comment).filter(
        Comment.post_id == post_id
    ).delete()


    db.delete(post)
    db.commit()


    return {
        "message": "삭제되었습니다."
    }



# =================================================
# 댓글
# =================================================


# 댓글 조회

@router.get("/{post_id}/comments")
def get_comments(
    post_id: int,
    db: Session = Depends(get_db)
):

    post = db.query(Post).filter(
        Post.id == post_id
    ).first()


    if not post:
        raise HTTPException(
            status_code=404,
            detail="게시글을 찾을 수 없습니다."
        )


    comments = db.query(Comment).filter(
        Comment.post_id == post_id
    ).order_by(
        Comment.id.desc()
    ).all()


    return comments



# 댓글 작성

@router.post(
    "/{post_id}/comments",
    status_code=status.HTTP_201_CREATED
)
def create_comment(
    post_id: int,
    request: dict,
    db: Session = Depends(get_db)
):

    post = db.query(Post).filter(
        Post.id == post_id
    ).first()


    if not post:
        raise HTTPException(
            status_code=404,
            detail="게시글을 찾을 수 없습니다."
        )


    comment = Comment(
        post_id=post_id,
        content=request["content"],
        author="익명",
        hashed_password=hash_password(
            request["password"]
        )
    )


    db.add(comment)
    db.commit()
    db.refresh(comment)


    return comment



# 댓글 삭제

@router.delete(
    "/comments/{comment_id}"
)
def delete_comment(
    comment_id: int,
    request: CommunityDeleteRequest,
    db: Session = Depends(get_db)
):

    comment = db.query(Comment).filter(
        Comment.id == comment_id
    ).first()


    if not comment:
        raise HTTPException(
            status_code=404,
            detail="댓글을 찾을 수 없습니다."
        )


    if comment.hashed_password != hash_password(
        request.password
    ):
        raise HTTPException(
            status_code=403,
            detail="비밀번호가 일치하지 않습니다."
        )


    db.delete(comment)
    db.commit()


    return {
        "message": "댓글이 삭제되었습니다."
    }