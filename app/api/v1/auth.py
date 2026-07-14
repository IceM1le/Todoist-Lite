from fastapi import Depends, HTTPException, APIRouter
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token
from app.models.user import User
from app.schemas.user import UserCreate

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", status_code=201)
async def register(user_create: UserCreate, db=Depends(get_db)):
    user = await db.execute(select(User).where(User.name == user_create.name))
    if user.scalars().first():
        raise HTTPException(status_code=400, detail="Username taken")
    existing_email = await db.execute(select(User).where(User.email == user_create.email))
    if existing_email.scalars().first():
        raise HTTPException(status_code=400, detail="Email already registered")
    new_user = User(name=user_create.name,
                    hashed_password=hash_password(user_create.password),
                    email=user_create.email)
    db.add(new_user)
    await db.commit()
    return {"ok": True}


@router.post("/login", status_code=201)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db=Depends(get_db)):
    result = await db.execute(select(User).where(User.name == form_data.username))
    user = result.scalars().first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Bad credentials")
    token = create_access_token(data={"sub": user.name})
    return {"access_token": token, "token_type": "bearer"}
