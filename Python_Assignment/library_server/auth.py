import os
import models
from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from database import get_db

# .env 로딩
load_dotenv()

# 보안 설정 (프로덕션에서는 반드시 강한 SECRET_KEY 사용)
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 6

# 해시 알고리즘: bcrypt_sha256 (평문-해시 전처리 포함)
# 참고: bcrypt만 사용할 수도 있으나, bcrypt_sha256은 긴 비밀번호 처리에 유리
# pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
pwd_ctx = CryptContext(schemes=["bcrypt_sha256"], deprecated="auto")

# OAuth2 Bearer 토큰 파서 (로그인 엔드포인트 경로 명시)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# 기능 1. 비밀번호 해시/검증
def hash_password(pw: str) -> str:
    return pwd_ctx.hash(pw)

def verify_password(pw: str, pw_hash: str) -> bool:
    return pwd_ctx.verify(pw, pw_hash)

# 기능 2. JWT 생성: payload + exp (만료) 클레임 추가
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# 기능 3. 현재 사용자 조회(인증): 토큰 검증 실패 시 401
def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> models.User:
    cred_exc = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise cred_exc
    except JWTError:
        raise cred_exc
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        raise cred_exc
    return user

# 기능 4. 관리자 권한 확인(인가): 비관리자는 403
def require_admin(user: models.User = Depends(get_current_user)) -> models.User:
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return user
