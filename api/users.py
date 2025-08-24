"""
FastAPI 사용자 관리 REST API
"""
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, validator
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import sys
import os

# Python 경로에 모델 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from python.models import User, get_db, create_tables

app = FastAPI(title="User Management API", version="1.0.0")

# Pydantic 모델들
class UserBase(BaseModel):
    """사용자 기본 스키마"""
    username: str
    email: EmailStr

    @validator('username')
    def validate_username(cls, v):
        if len(v) < 3:
            raise ValueError('사용자명은 3자 이상이어야 합니다')
        if len(v) > 50:
            raise ValueError('사용자명은 50자 이하여야 합니다')
        return v

class UserCreate(UserBase):
    """사용자 생성 스키마"""
    pass

class UserUpdate(BaseModel):
    """사용자 수정 스키마"""
    username: Optional[str] = None
    email: Optional[EmailStr] = None

    @validator('username')
    def validate_username(cls, v):
        if v is not None:
            if len(v) < 3:
                raise ValueError('사용자명은 3자 이상이어야 합니다')
            if len(v) > 50:
                raise ValueError('사용자명은 50자 이하여야 합니다')
        return v

class UserResponse(UserBase):
    """사용자 응답 스키마"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class PaginatedResponse(BaseModel):
    """페이지네이션 응답 스키마"""
    items: List[UserResponse]
    total: int
    page: int
    size: int
    pages: int

# 시작 시 테이블 생성
@app.on_event("startup")
async def startup_event():
    create_tables()

# 에러 핸들러
@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"error": "잘못된 요청", "detail": str(exc)}
    )

# API 엔드포인트들
@app.get("/api/users", response_model=PaginatedResponse)
async def get_users(
    page: int = Query(1, ge=1, description="페이지 번호"),
    size: int = Query(20, ge=1, le=100, description="페이지 크기"),
    username: Optional[str] = Query(None, description="사용자명 필터"),
    db: Session = Depends(get_db)
):
    """모든 사용자 조회 (페이지네이션 및 필터링 포함)"""
    try:
        # 기본 쿼리
        query = db.query(User)

        # 필터링
        if username:
            query = query.filter(User.username.contains(username))

        # 전체 개수 조회
        total = query.count()

        # 페이지네이션 적용
        offset = (page - 1) * size
        users = query.offset(offset).limit(size).all()

        # 페이지 계산
        pages = (total + size - 1) // size

        return PaginatedResponse(
            items=[UserResponse.from_orm(user) for user in users],
            total=total,
            page=page,
            size=size,
            pages=pages
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"서버 오류: {str(e)}")

@app.post("/api/users", response_model=UserResponse, status_code=201)
async def create_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """새 사용자 생성"""
    try:
        # 중복 검사
        existing_user = db.query(User).filter(
            (User.username == user_data.username) | (User.email == user_data.email)
        ).first()

        if existing_user:
            if existing_user.username == user_data.username:
                raise HTTPException(status_code=400, detail="이미 존재하는 사용자명입니다")
            else:
                raise HTTPException(status_code=400, detail="이미 존재하는 이메일입니다")

        # 새 사용자 생성
        db_user = User(
            username=user_data.username,
            email=user_data.email
        )

        db.add(db_user)
        db.commit()
        db.refresh(db_user)

        return UserResponse.from_orm(db_user)

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"사용자 생성 중 오류 발생: {str(e)}")

@app.get("/api/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: Session = Depends(get_db)):
    """특정 사용자 조회"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")

    return UserResponse.from_orm(user)

@app.put("/api/users/{user_id}", response_model=UserResponse)
async def update_user(user_id: int, user_data: UserUpdate, db: Session = Depends(get_db)):
    """사용자 정보 수정"""
    try:
        # 사용자 존재 확인
        db_user = db.query(User).filter(User.id == user_id).first()
        if not db_user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")

        # 수정할 데이터가 있는지 확인
        update_data = user_data.dict(exclude_unset=True)
        if not update_data:
            raise HTTPException(status_code=400, detail="수정할 데이터가 없습니다")

        # 중복 검사
        if 'username' in update_data:
            existing = db.query(User).filter(
                User.username == update_data['username'],
                User.id != user_id
            ).first()
            if existing:
                raise HTTPException(status_code=400, detail="이미 존재하는 사용자명입니다")

        if 'email' in update_data:
            existing = db.query(User).filter(
                User.email == update_data['email'],
                User.id != user_id
            ).first()
            if existing:
                raise HTTPException(status_code=400, detail="이미 존재하는 이메일입니다")

        # 데이터 수정
        for field, value in update_data.items():
            setattr(db_user, field, value)

        db_user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_user)

        return UserResponse.from_orm(db_user)

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"사용자 수정 중 오류 발생: {str(e)}")

@app.delete("/api/users/{user_id}")
async def delete_user(user_id: int, db: Session = Depends(get_db)):
    """사용자 삭제"""
    try:
        db_user = db.query(User).filter(User.id == user_id).first()
        if not db_user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")

        db.delete(db_user)
        db.commit()

        return {"message": f"사용자 ID {user_id}가 성공적으로 삭제되었습니다"}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"사용자 삭제 중 오류 발생: {str(e)}")

# 헬스체크 엔드포인트
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
