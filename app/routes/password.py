from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import secrets
import string
from app.database import get_db
from app import models, auth
from app.schemas.password import PasswordResetRequest, PasswordResetConfirm, PasswordResetResponse
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/password", tags=["password"])

# Generate a secure token
def generate_reset_token():
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(64))

# Send email (simplified - in production use a proper email service)
async def send_reset_email(email: str, token: str):
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3001")
    reset_link = f"{frontend_url}/reset-password?token={token}"
    
    # In production, you'd use a real email service
    # For now, we'll just print to console (Render logs will show it)
    print(f"\n🔐 PASSWORD RESET EMAIL")
    print(f"To: {email}")
    print(f"Reset link: {reset_link}")
    print(f"This is a development version - in production, this would be sent via email.\n")
    
    # TODO: Integrate with a real email service like SendGrid, Mailgun, etc.

@router.post("/reset-request", response_model=PasswordResetResponse)
async def request_password_reset(
    request: PasswordResetRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Request a password reset email"""
    user = db.query(models.User).filter(models.User.email == request.email).first()
    
    # Always return success even if user doesn't exist (security)
    if not user:
        return {"message": "If your email exists, you will receive a reset link", "success": True}
    
    # Invalidate old tokens
    old_tokens = db.query(models.PasswordResetToken).filter(
        models.PasswordResetToken.user_id == user.id,
        models.PasswordResetToken.used == False
    ).all()
    
    for token in old_tokens:
        token.used = True
    
    # Create new token
    token_str = generate_reset_token()
    expires_at = datetime.utcnow() + timedelta(hours=24)
    
    reset_token = models.PasswordResetToken(
        user_id=user.id,
        token=token_str,
        expires_at=expires_at,
        used=False
    )
    
    db.add(reset_token)
    db.commit()
    
    # Send email in background
    background_tasks.add_task(send_reset_email, user.email, token_str)
    
    return {"message": "If your email exists, you will receive a reset link", "success": True}

@router.post("/reset-confirm", response_model=PasswordResetResponse)
def confirm_password_reset(
    request: PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    """Confirm password reset with token"""
    # Check if passwords match
    if request.new_password != request.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match"
        )
    
    # Find token
    reset_token = db.query(models.PasswordResetToken).filter(
        models.PasswordResetToken.token == request.token,
        models.PasswordResetToken.used == False,
        models.PasswordResetToken.expires_at > datetime.utcnow()
    ).first()
    
    if not reset_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired token"
        )
    
    # Update password
    user = db.query(models.User).filter(models.User.id == reset_token.user_id).first()
    user.hashed_password = auth.hash_password(request.new_password)
    
    # Mark token as used
    reset_token.used = True
    
    db.commit()
    
    return {"message": "Password reset successful", "success": True}
