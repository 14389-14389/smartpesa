from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import secrets
from app.database import get_db
from app.models.user import User
from app.schemas.password import PasswordResetRequest, PasswordResetConfirm
from app.utils.security import get_password_hash
from app.utils.email import send_reset_email

router = APIRouter(tags=["Password"])

@router.post("/forgot", status_code=status.HTTP_200_OK)
def forgot_password(
    request: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        # For security, don't reveal that the email doesn't exist
        return {"message": "If that email is registered, a reset link has been sent."}

    token = secrets.token_urlsafe(32)
    expires = datetime.utcnow() + timedelta(hours=1)

    user.reset_token = token
    user.reset_token_expires = expires
    db.commit()

    reset_url = f"http://localhost:3000/reset-password.html?token={token}"
    send_reset_email(user.email, reset_url)

    return {"message": "If that email is registered, a reset link has been sent."}

@router.post("/reset", status_code=status.HTTP_200_OK)
def reset_password(
    confirm: PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.reset_token == confirm.token).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    if user.reset_token_expires < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Token expired")

    user.hashed_password = get_password_hash(confirm.new_password)
    user.reset_token = None
    user.reset_token_expires = None
    db.commit()

    return {"message": "Password updated successfully"}
