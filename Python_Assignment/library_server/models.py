from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime
from zoneinfo import ZoneInfo

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=True)
    password_hash = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False)

    loans = relationship("Loan", back_populates="user")

class Book(Base):
    __tablename__ = "books"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    author = Column(String, nullable=False)
    isbn = Column(String, unique=True, index=True, nullable=False)
    category = Column(String, index=True)
    total_copies = Column(Integer, default=1)
    borrowed_copies = Column(Integer, default=0)

    loans = relationship("Loan", back_populates="book")

# UTC now 팩토리: timezone-aware DateTime 기본값에 사용
def now_utc():
    return datetime.now(ZoneInfo("UTC"))

class Loan(Base):
    __tablename__ = "loans"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    borrowed_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)
    returned_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="loans")
    book = relationship("Book", back_populates="loans")
