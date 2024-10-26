from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import os
from routes.organization import router as organization_router
from routes.auth import router as auth_router
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()

# Now you can use os.getenv() to access them
JWT_SECRET = os.getenv('SECERT_KEY')
JWT_ALGORITHM = os.getenv('ALGORITHUM')

print(f"JWT_SECRET: {JWT_SECRET}")
print(f"JWT_ALGORITHM: {JWT_ALGORITHM}")

# Initialize the FastAPI app
app = FastAPI(
    title="Organization",
    version="v1",
    description="API documentation for Organization"
)

# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB Connection
MONGO_URL = os.getenv("MONGO_URL", "mongodb://db:27017/organization")
client = AsyncIOMotorClient(MONGO_URL)
db = client["organization_app"]

@app.get("/")
async def read_root():
    return {"JWT_SECRET": JWT_SECRET, "JWT_ALGORITHM": JWT_ALGORITHM}

# Include the organization_router with a prefix in the FastAPI app
app.include_router(organization_router, prefix="/api",tags=['organization'])
app.include_router(auth_router, prefix="/api",tags=['auth'])

