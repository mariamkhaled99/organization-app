import re
from fastapi import APIRouter, FastAPI, Depends, HTTPException, status
from passlib.context import CryptContext
from bson import ObjectId
from auth.jwt_handler import signin_JWT, decode_token
from motor.motor_asyncio import AsyncIOMotorClient
from models.auth import AuthResponseModel, RevokeTokenRequest, SignInModel, SignUpModel
import redis
import jwt
from routes.organization import get_current_user
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()


router = APIRouter()




MONGO_URL = os.getenv('DATABASE_URL')
print(f"MONGO_URL:{MONGO_URL}")

# Database setup
# MONGO_URL = "mongodb://db:27017/organization"
client = AsyncIOMotorClient(MONGO_URL)
db = client["organization_app"]
users_collection = db["users"]

REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379')
redis_client = redis.StrictRedis.from_url(REDIS_URL, decode_responses=True)


# Password hashing setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

@router.post("/signup", response_model=dict)
async def sign_up(user: SignUpModel):
    # Check if user already exists
    if await users_collection.find_one({"email": user.email}):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash password and save user
    hashed_password = get_password_hash(user.password)
    user_dict = user.dict()
    user_dict["password"] = hashed_password
    await users_collection.insert_one(user_dict)
    return {"message": "User created successfully"}

@router.post("/signin", response_model=AuthResponseModel)
async def sign_in(user: SignInModel):
    # Check if user exists
    db_user = await users_collection.find_one({"email": user.email})
    if not db_user or not verify_password(user.password, db_user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Generate JWT tokens
    tokens = signin_JWT(str(db_user["_id"]),db_user['name'], user.email)
    return {
        "message": "Login successful",
        "access_token": tokens["access_token"],
        "refresh_token": tokens["refresh_token"]
    }


@router.post("/refresh-token", response_model=AuthResponseModel)
async def refresh_token(refresh_token: str):
    # Check if the refresh token is revoked
    if redis_client.get(refresh_token) == "revoked":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has been revoked"
        )
    
    # Decode the refresh token
    decoded_token = decode_token(refresh_token)
    
    if not decoded_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    user_id = decoded_token['user_id']
    db_user = await users_collection.find_one({"_id": ObjectId(user_id)})
    
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    email = db_user.get('email')
    name = db_user.get('name')
    
    # Generate new access and refresh tokens
    tokens = signin_JWT(user_id, name, email)
    
    return {
        "message": "Token refreshed successfully",
        "access_token": tokens["access_token"],
        "refresh_token": tokens["refresh_token"]
    }





@router.post("/revoke-refresh-token/", response_model=dict)
async def revoke_refresh_token(
    revoke_token_request: RevokeTokenRequest,
    current_user: dict = Depends(get_current_user)
):  
     #Regular expression for validating JWT format (example) 
    JWT_REGEX = r'^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$'
    refresh_token = revoke_token_request.refresh_token

    
    
    # Validate the format of the refresh token
    if not re.match(JWT_REGEX, refresh_token):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid refresh token format"
        )
    
    # Attempt to decode the token to check if it is valid
    try:
        decoded_token = decode_token(refresh_token)  # You should have this function from earlier
        if not decoded_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token"
            )
        
        # Check if the user_id matches the current user's id
        if decoded_token.get("user_id") != str(current_user["id"]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to revoke this token"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid refresh token {e}"
        )
    
    # Store the revoked refresh token in Redis with an expiration
    redis_client.set(refresh_token, "revoked", ex=2592000)  

    return {"message": "Refresh token revoked successfully"}