from pydantic import BaseModel, EmailStr, ConfigDict, field_serializer
from typing import Optional, List
from datetime import datetime
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")
UTC = ZoneInfo("UTC")

# Users
# 회원 가입 입력 스키마 (평문 password 입력 → 서버에서 해시)
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    is_admin: bool = False

# 사용자 공개 정보 (민감 정보 제외)
class UserOut(BaseModel):
    id: int
    username: str
    email: EmailStr
    full_name: Optional[str]
    is_admin: bool
    class Config:
        from_attributes = True

# Auth
# 로그인 성공 응답: Bearer 토큰
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

# 로그인 요청 (JSON 바디)
class LoginIn(BaseModel):
    username: str
    password: str

# Books
# 공통 필드(입력/출력 공용), available은 출력 전용에서 계산됨
class BookBase(BaseModel):
    title: str
    author: str
    isbn: str
    category: Optional[str] = None
    total_copies: int = 1

# 도서 생성 입력 스키마
class BookCreate(BookBase): pass

# 도서 조회 출력 스키마: 파생 필드 포함
class BookOut(BookBase):
    id: int
    borrowed_copies: int
    available: bool
    class Config:
        from_attributes = True

# Loans 
# 관리자 대리 대출 허용용 (일반사용자면 무시)
class LoanCreate(BaseModel):
    book_id: int
    user_id: Optional[int] = None 

# 대출 내역 응답 스키마 (대출/반납 시각 포함)
class LoanOut(BaseModel):
    id: int
    book_id: int
    user_id: int
    borrowed_at: datetime | None
    returned_at: datetime | None

    model_config = ConfigDict(from_attributes=True)

    # 시간 필드 직렬화: 응답 시 UTC → KST로 변환 (ISO8601)
    @field_serializer("borrowed_at", "returned_at", when_used="json")
    def _to_kst(self, v: datetime | None):
        if v is None:
            return None
        if v.tzinfo is None:
            v = v.replace(tzinfo=UTC)
        return v.astimezone(KST).isoformat() 
