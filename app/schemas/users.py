from pydantic import BaseModel, EmailStr, Field, model_validator, field_validator
import re
from datetime import datetime

class UserCreate(BaseModel):
    username: str = Field(min_length=5, max_length=20, description="Username must be between 5 and 20 characters long")
    email: EmailStr = Field(description="User's email address")
    password: str = Field(min_length=8, max_length=255, description="Password must be at least 8 characters long")
    confirm_password: str = Field(min_length=8, max_length=255, description="Password confirmation must match the password")

    ########################### username validation ###########################
    @field_validator("username")
    def validate_username(cls, username):
        if not re.match(r"^[a-zA-Z0-9_]+$", username):
            raise ValueError("Username can only contain letters, numbers, and underscores")
        return username

    ########################### password validation ###########################
    @model_validator(mode="before")
    def validate_passwords(cls, values):
        password = values.get("password")
        confirm_password = values.get("confirm_password")
        if password != confirm_password:
            raise ValueError("Passwords do not match.")
        return values

    @field_validator("password")
    def validate_password_strength(cls, password):
        if not re.search(r"[A-Z]", password):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not re.search(r"[a-z]", password):
            raise ValueError("Password must contain at least one lowercase letter.")
        if not re.search(r"[0-9]", password):
            raise ValueError("Password must contain at least one digit.")
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValueError("Password must contain at least one special character.")
        return password
    ###########################################################################

class UserLogin(BaseModel):
    login: str = Field(min_length=5, max_length=255, description="Username or email address")
    password: str = Field(min_length=8, max_length=255, description="User's password")

class UserUpdate(BaseModel):
    username: str | None = Field(min_length=5, max_length=20, default=None, description="Username must be between 5 and 20 characters long")
    email: EmailStr | None = Field(default=None, description="User's email address")
    password: str | None = Field(min_length=8, max_length=255, default=None, description="Password must be at least 8 characters long")
    confirm_password: str | None = Field(min_length=8, max_length=255, default=None, description="Password confirmation must match the password")

    ########################### username validation ###########################
    @field_validator("username")
    def validate_username(cls, username):
        if username is None:
            return username
        if not re.match(r"^[a-zA-Z0-9_]+$", username):
            raise ValueError("Username can only contain letters, numbers, and underscores")
        return username

    ########################### password validation ###########################
    @model_validator(mode="before")
    def validate_passwords(cls, values):
        password = values.get("password")
        confirm_password = values.get("confirm_password")
        if password != confirm_password:
            raise ValueError("Passwords do not match.")
        return values

    @field_validator("password")
    def validate_password_strength(cls, password):
        if password is None:
            return password
        if not re.search(r"[A-Z]", password):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not re.search(r"[a-z]", password):
            raise ValueError("Password must contain at least one lowercase letter.")
        if not re.search(r"[0-9]", password):
            raise ValueError("Password must contain at least one digit.")
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValueError("Password must contain at least one special character.")
        return password
    ###########################################################################

class UserAdminUpdate(BaseModel):
    username: str | None = Field(min_length=5, max_length=20, default=None, description="Username must be between 5 and 20 characters long")
    role: str | None = Field(min_length=3, max_length=10, default=None, description="User's role")

    ########################### username validation ###########################
    @field_validator("username")
    def validate_username(cls, username):
        if username is None:
            return username
        if not re.match(r"^[a-zA-Z0-9_]+$", username):
            raise ValueError("Username can only contain letters, numbers, and underscores")
        return username
    ########################### role validation ###########################
    @field_validator("role")
    def validate_role(cls, role):
        if role is None:
            return role
        if role not in ["admin", "user", "moderator"]:
            raise ValueError("Role must be one of 'admin', 'user', or 'moderator'")
        return role

class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    role: str
    created_at: datetime

    class Config:
        from_attributes = True

class RefreshToken(BaseModel):
    refresh_token: str