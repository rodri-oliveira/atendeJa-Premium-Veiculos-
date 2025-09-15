from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.core.config import settings
from app.core.security import verify_password, get_password_hash, create_access_token
from app.repositories.models import User

router = APIRouter()


@router.post("/login", summary="Realiza login e retorna um token JWT")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # No nosso caso, usamos email como username
    email = form_data.username.strip().lower()
    user: User | None = db.query(User).filter(User.email == email).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_credentials")
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_credentials")

    access_token = create_access_token(
        subject=user.email,
        expires_minutes=settings.AUTH_JWT_EXPIRE_MINUTES,
        extra={"role": user.role.value},
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", summary="Retorna o usuário logado (a partir do token)")
def read_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role.value,
        "is_active": current_user.is_active,
    }
