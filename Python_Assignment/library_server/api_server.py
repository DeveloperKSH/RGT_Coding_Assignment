from auth import hash_password, verify_password, create_access_token, get_current_user, require_admin
from fastapi import FastAPI, Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional
from database import Base, engine, get_db
import models, schemas

# 앱/DB 초기화
Base.metadata.create_all(bind=engine)
app = FastAPI(title="Library REST API")

# Auth & Users
# 기능 1. 회원 가입 (username/email 중복 금지, 비밀번호 해시 저장)
@app.post("/auth/signup", response_model=schemas.UserOut, status_code=201)
def signup(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    if db.query(models.User).filter((models.User.username==user_in.username) | (models.User.email==user_in.email)).first():
        raise HTTPException(400, "Username or email already exists")
    user = models.User(
        username=user_in.username,
        email=user_in.email,
        full_name=user_in.full_name,
        is_admin=user_in.is_admin,
        password_hash=hash_password(user_in.password),
    )
    db.add(user); db.commit(); db.refresh(user)
    return user

# JSON 바디용 로그인 스키마
class LoginRequest(BaseModel):
    username: str
    password: str

# 기능 2. 로그인 (JSON) → JWT 발급 (자격 증명 검증 실패는 400)
@app.post("/auth/login", response_model=schemas.Token)
def login_json(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == body.username).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    token = create_access_token({"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}

# 기능 3. 내 대출 현황 조회 (인증 필요): 본인 user_id 기준
@app.get("/users/me/loans", response_model=List[schemas.LoanOut])
def my_loans(current=Depends(get_current_user), db: Session = Depends(get_db)):
    loans = db.query(models.Loan).filter(models.Loan.user_id == current.id).all()
    return loans

# Books
# 기능 4. 도서 생성 (관리자 전용)
@app.post("/books", response_model=schemas.BookOut, status_code=201)
def create_book(book_in: schemas.BookCreate, db: Session = Depends(get_db), _: models.User = Depends(require_admin)):
    book = models.Book(**book_in.dict())
    db.add(book); db.commit(); db.refresh(book)
    return _book_out(book)

# 기능 5. 도서 목록 조회(카테고리/대여 가능 여부 필터)
@app.get("/books", response_model=List[schemas.BookOut])
def list_books(
    category: Optional[str] = Query(None),
    available: Optional[bool] = Query(None),
    db: Session = Depends(get_db)
):
    q = db.query(models.Book)
    if category:
        q = q.filter(models.Book.category == category)
    books = q.all()

    # available 필터는 가공 필드이므로 응답 변환 후 적용
    outs = []
    for b in books:
        out = _book_out(b)
        if available is None or out.available == available:
            outs.append(out)
    return outs

# 기능 6. 도서 삭제 (관리자 전용): 존재하지 않으면 404, 대여 중이면 400
@app.delete("/books/{book_id}", status_code=204)
def delete_book(book_id: int, db: Session = Depends(get_db), _: models.User = Depends(require_admin)):
    book = db.query(models.Book).get(book_id)
    if not book:
        raise HTTPException(404, "Book not found")
    if book.borrowed_copies > 0:
        raise HTTPException(400, "Cannot delete: borrowed copies exist")
    db.delete(book); db.commit()
    return

# Loans 
# 기능 7. 대출 생성: 1) 도서 존재 404 2) 재고 없으면 400 3) 일반 사용자는 본인 user_id만
@app.post("/loans", response_model=schemas.LoanOut, status_code=201)
def borrow(loan_in: schemas.LoanCreate, db: Session = Depends(get_db), current=Depends(get_current_user)):
    # 권한: 관리자는 loan_in.user_id로 대출 대행 가능, 일반 사용자는 본인으로 강제
    user_id = loan_in.user_id if current.is_admin and loan_in.user_id else current.id
    book = db.query(models.Book).get(loan_in.book_id)
    if not book: raise HTTPException(404, "Book not found")
    if book.borrowed_copies >= book.total_copies:
        raise HTTPException(400, "No available copies")
    
    # 부작용: Loan 생성 + Book.borrowed_copies 증가 (트랜잭션 내 처리)
    loan = models.Loan(user_id=user_id, book_id=book.id)
    book.borrowed_copies += 1
    db.add(loan); db.commit(); db.refresh(loan)
    return loan

# 기능 8. 반납 처리: 본인 또는 관리자만, 중복 반납 금지
@app.post("/loans/{loan_id}/return", response_model=schemas.LoanOut)
def return_book(loan_id: int, db: Session = Depends(get_db), current=Depends(get_current_user)):
    loan = db.query(models.Loan).get(loan_id)
    if not loan: raise HTTPException(404, "Loan not found")
    # 본인 또는 관리자
    if (loan.user_id != current.id) and (not current.is_admin):
        raise HTTPException(403, "Not allowed")
    if loan.returned_at:
        raise HTTPException(400, "Already returned")
    
    # 부작용: Loan.returned_at 설정 + Book.borrowed_copies 감소
    from datetime import datetime
    loan.returned_at = datetime.utcnow()
    loan.book.borrowed_copies -= 1
    db.commit(); db.refresh(loan)
    return loan

# helpers 
# 기능 H1. Book → BookOut 변환 (available 파생 필드 계산)
def _book_out(b: models.Book) -> schemas.BookOut:
    available = b.borrowed_copies < b.total_copies
    return schemas.BookOut(
        id=b.id, title=b.title, author=b.author, isbn=b.isbn,
        category=b.category, total_copies=b.total_copies,
        borrowed_copies=b.borrowed_copies, available=available
    )
