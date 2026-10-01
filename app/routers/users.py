from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy import select
from app.models.users import User
from app.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.users import RefreshToken, UserAdminUpdate, UserCreate, UserLogin, UserResponse, UserUpdate
from jose import JWTError, jwt
from app.security import (
    create_access_token, 
    hash_password, 
    create_refresh_token, 
    require_admin,
    require_moderator, 
    verify_password, 
    get_current_user,
    SECRET_KEY,
    ALGORITHM
)
import time

router = APIRouter(prefix="/users", tags=["users"])


########################## Register/Login #########################
def welcome_message(username, user_id):
    print(f"You've successfully registered! Welcome {username} to the Georgian Railway!")
    time.sleep(3)
    print(f"{username} with ID {user_id} registered successfully") 

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    existing_user = await db.execute(select(User).where((User.email == user.email) | (User.username == user.username)))
    existing_user = existing_user.scalars().first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email or username already exists"
        )

    hashed_password = hash_password(user.password)
    db_user = user.model_dump(exclude={"password", "confirm_password"})
    new_user = User(**db_user, password=hashed_password)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    background_tasks.add_task(welcome_message, new_user.username, new_user.id)
    return new_user


@router.post("/login")
async def login(user: UserLogin, db: AsyncSession = Depends(get_db)):
    authorized_user = await db.execute(select(User).where((User.email == user.login) | (User.username == user.login)))
    authorized_user = authorized_user.scalars().first()
    if not authorized_user or not verify_password(user.password, authorized_user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email, username or password"
        )
    access_token = create_access_token({"user_id": authorized_user.id})
    refresh_token = create_refresh_token({"user_id": authorized_user.id})
    return {
        "access_token": access_token, 
        "refresh_token": refresh_token,
        "token_type": "bearer"
        }

@router.post("/refresh")
async def refresh_token(request: RefreshToken):
    try:
        payload = jwt.decode(request.refresh_token, SECRET_KEY, algorithms=[ALGORITHM])

        user_id = payload.get("user_id")
        token_type = payload.get("token_type")

        if not user_id or token_type != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    access_token = create_access_token(data={"user_id": user_id})

    return {
        'access_token': access_token,
        'token_type': 'bearer'
    }


##########################  User #########################

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.patch("/me", response_model=UserResponse)
async def update_me(user_update: UserUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    user_data = user_update.model_dump(exclude_unset=True)

    if "username" in user_data:
        existing_user = await db.execute(select(User).where(User.username == user_data["username"]))
        existing_user = existing_user.scalars().first()
        if existing_user and existing_user.id != current_user.id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken")
    if "email" in user_data:
        existing_user = await db.execute(select(User).where(User.email == user_data["email"]))
        existing_user = existing_user.scalars().first()
        if existing_user and existing_user.id != current_user.id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already taken")
    if "password" in user_data:
        current_user.password = hash_password(user_data["password"])
        user_data.pop("password", None)
    user_data.pop("confirm_password", None)
    for key, value in user_data.items():
        setattr(current_user, key, value)
    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)
    return current_user

########################## Admin/Moderator #########################

@router.get("/", response_model=list[UserResponse])
async def get_all_users(db: AsyncSession = Depends(get_db), current_user: User = Depends(require_moderator)):
    result = await db.execute(select(User))
    users = result.scalars().all()
    return users

@router.get("/moderators", response_model=list[UserResponse])
async def get_moderators(db: AsyncSession = Depends(get_db), current_user: User = Depends(require_admin)):
    result = await db.execute(select(User).where(User.role == "moderator"))
    moderators = result.scalars().all()
    return moderators

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_moderator)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user

@router.delete("/{user_id}")
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_admin)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    await db.delete(user)
    await db.commit()
    return {"detail": "User deleted successfully"}

@router.patch("/{user_id}", response_model=UserResponse)
async def user_update_by_admin(user_id: int, user_update: UserAdminUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_admin)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    update_data = user_update.model_dump(exclude_unset=True)
    if "username" in update_data:
        existing_username = await db.execute(select(User).where(User.username == update_data["username"]))
        existing_username = existing_username.scalars().first()
        if existing_username and existing_username.id != user.id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")
    for key, value in update_data.items():
        setattr(user, key, value)
    await db.commit()
    await db.refresh(user)
    return user

