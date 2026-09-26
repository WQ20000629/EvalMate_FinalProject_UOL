# ------------------------------------------------------------------
# File: backend/app/api/auth.py
# Purpose: Handles user registration, login, logout, and authentication checks.
# ------------------------------------------------------------------

# Import the libraries and modules needed for the auth API
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.db_models import User
from app.core.security import create_access_token, decode_access_token, hash_password, verify_password

# Create a router for the auth endpoints
router = APIRouter()

# Cookie settings for the user login session
COOKIE_NAME = "access_token"
COOKIE_MAX_AGE_SECONDS = 60 * 60 * 24 * 7  # 7 days, same as the JWT expiry


# Request body for creating an account
class RegisterInput(BaseModel):
    email: EmailStr
    password: str


# Request body for logging in
class LoginInput(BaseModel):
    email: EmailStr
    password: str


# User details sent back to the frontend, without the password hash
class UserOut(BaseModel):
    id: int
    email: str


# Create a JWT and save it in a browser cookie for the logged-in user
def _set_auth_cookie(response: Response, user_id: int) -> None:
    token = create_access_token(user_id)
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        max_age=COOKIE_MAX_AGE_SECONDS,
        httponly=True,
        samesite="lax",
        secure=False,  # local HTTP only, use True when running on HTTPS
        path="/",
    )


# Return the logged-in user from the cookie token
def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = request.cookies.get(COOKIE_NAME)
    user_id = decode_access_token(token) if token else None
    if user_id is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


# Same as get_current_user, but it returns None if the user is not logged in
def get_current_user_optional(request: Request, db: Session = Depends(get_db)) -> User | None:
    token = request.cookies.get(COOKIE_NAME)
    user_id = decode_access_token(token) if token else None
    if user_id is None:
        return None
    return db.query(User).filter(User.id == user_id).first()


# Register a new user and set the auth cookie after creating the account
@router.post("/auth/register", response_model=UserOut)
def register(body: RegisterInput, response: Response, db: Session = Depends(get_db)):
    if len(body.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters.")
    if db.query(User).filter(User.email == body.email).first() is not None:
        raise HTTPException(status_code=400, detail="An account with this email already exists.")

    user = User(email=body.email, hashed_password=hash_password(body.password))
    db.add(user)
    db.commit()
    db.refresh(user)

    _set_auth_cookie(response, user.id)
    return user


# Check the email and password, then log the user in and set the cookie
@router.post("/auth/login", response_model=UserOut)
def login(body: LoginInput, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()
    if user is None or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password.")

    _set_auth_cookie(response, user.id)
    return user


# Remove the auth cookie so the user is logged out
@router.post("/auth/logout")
def logout(response: Response):
    response.delete_cookie(COOKIE_NAME, path="/")
    return {"status": "ok"}


# Return the current logged-in user
@router.get("/auth/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user
