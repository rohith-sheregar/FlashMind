import re
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, validator

from app.services.db_setup import get_db
from app.models.user import User
from app.core.security import verify_password, get_password_hash, create_access_token

router = APIRouter()

# Match the actual mounted route prefix in main.py
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str

    @validator("name")
    def validate_name(cls, v):
        if not v.isalpha():
            raise ValueError("Name must contain only letters")
        return v

    @validator("password")
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError("Password too short")
        return v


@router.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    """Simple email/password registration."""
    print(f"DEBUG: Registering user: {user.email}")
    print(f"DEBUG: Password length: {len(user.password)}")
    print(f"DEBUG: Password content (first 5 chars): {user.password[:5]}")
    
    # Check if email exists
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already exists")

    new_user = User(
        name=user.name,
        email=user.email,
        # Match column name defined in models.user.User
        password_hash=get_password_hash(user.password),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User created successfully"}


@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """Password-based login that returns a JWT access token."""
    user = db.query(User).filter(User.email == form_data.username).first()
    
    if not user:
        raise HTTPException(status_code=400, detail="User not found")
        
    if not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect password")

    access_token = create_access_token(data={"sub": user.email, "id": user.id})
    return {"access_token": access_token, "token_type": "bearer"}


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Decode JWT and return current user info (lightweight helper)."""
    from jose import jwt
    from app.core.config import settings

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str | None = payload.get("sub")
        user_id: int | None = payload.get("id")
        if email is None or user_id is None:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        return {"id": user_id, "email": email}
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid credentials")