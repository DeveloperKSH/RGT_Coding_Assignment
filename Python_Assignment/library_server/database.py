import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# .env 로딩
load_dotenv()

# 기능 1. DB URL 결정: 환경변수 없으면 로컬 SQLite로 폴백
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./library.db")

# 공통 엔진 옵션
engine_kwargs = {
    "pool_pre_ping": True,  # 유휴 커넥션 끊김 방지 (Supabase 무료티어 슬립 대비)
}

# 드라이버별 세부 설정
if DATABASE_URL.startswith("sqlite"):
    # SQLite는 기본적으로 스레드 제한 → FastAPI에서 멀티스레드 접근 허용
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    # Postgres(psycopg) 권장 값: 풀/리사이클은 환경별로 .env에서 조정 가능
    engine_kwargs.update(
        dict(
            pool_size=int(os.getenv("DB_POOL_SIZE", "5")),
            max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "5")),
            pool_recycle=int(os.getenv("DB_POOL_RECYCLE", "300")),  # 초 단위
            # 서버/클라이언트 시차 최소화를 위해 DB 세션 타임존을 UTC로 고정
            connect_args={"options": "-c timezone=UTC"},
        )
    )
    # 참고: SSL은 DATABASE_URL에 ?sslmode=require 식으로 포함 권장

engine = create_engine(DATABASE_URL, **engine_kwargs)

# 세션 팩토리/베이스
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 기능 2. DB 세션 의존성: 요청 스코프 세션 생성/정리
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
