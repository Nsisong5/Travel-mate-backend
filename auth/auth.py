
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta
from database import get_db
import models, schemas
from core.config import settings 




ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
router = APIRouter(prefix="/auth", tags=["auth"])

def verify_password(plain, hashed):
    return pwd_context.verify(plain, hashed)

def hash_password(pw):
    return pwd_context.hash(pw)

def create_access_token(data: dict, expires_minutes: int = ACCESS_TOKEN_EXPIRE_MINUTES):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

@router.post("/register", response_model=schemas.UserOut)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.email == user.email).first()
    if existing:
        raise HTTPException(400, "Email already registered")
    new_user = models.User(email=user.email, hashed_password=hash_password(user.password), full_name=user.full_name or "")
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/login", response_model=schemas.Token)
def login(body: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == body.email).first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}

def get_current_user(db: Session = Depends(get_db), token: str = Depends(lambda authorization: authorization)):
    """
    Lightweight token extractor from Authorization header "Bearer <token>".
    FastAPI dependency tip: Define in deps.py for reuse; kept inline for brevity.
    """
    from fastapi import Request
    def extractor(request: Request):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing token")
        return auth.split(" ", 1)[1]
    return extractor  # return callable (we'll use proper deps in main)