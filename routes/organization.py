from datetime import datetime
from typing import List
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status
from auth.jwt_handler import decode_token
from models.organization import InviteUserRequest, OrganizationModel
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi.security import OAuth2PasswordBearer
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

def organization_helper(org) -> dict:
    return {
        "organization_id": str(org["_id"]),
        "name": org["name"],
        "description": org["description"],
        "owner_id": org.get("owner_id"),
        "organization_members": org["organization_members"]
    }

# Router for organization endpoints
router = APIRouter()


# Database setup

MONGO_URL = os.getenv('MONGO_URL')
# MONGO_URL = "mongodb://db:27017/organization"
client = AsyncIOMotorClient(MONGO_URL)
db = client["organization_app"]






oauth2_scheme = OAuth2PasswordBearer(tokenUrl="signin")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        decoded_token = decode_token(token)
        if not decoded_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return decoded_token  
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

router = APIRouter()
@router.post("/organization")
async def create_organization(
    organization: OrganizationModel,
    current_user: dict = Depends(get_current_user)
):
    user_email = current_user.get("email")
    user_id = str(current_user.get("user_id"))
    name = current_user.get("name")

    # Prepare organization data with owner_id and initial members
    org_data = organization.dict()
    org_data["owner_id"] = user_id
    org_data["organization_members"].append({
        "name": name,
        "email": user_email,
        "access_level": "admin"
    })

    # Insert the organization into the database
    new_org = await db["organizations"].insert_one(org_data)
    created_org = await db["organizations"].find_one({"_id": new_org.inserted_id})

    # Return the fully populated response
    return organization_helper(created_org)



@router.get("/organization", response_model=List[OrganizationModel])
async def get_organizations(current_user: dict = Depends(get_current_user)):
    organizations = []
    
    async for org in db["organizations"].find():
        org_id = str(org["_id"])
        
        # Since members are embedded, directly retrieve them from the organization document
        organization_members = org.get("organization_members", [])
        
        # Add to response list as OrganizationModel instances
        organizations.append(OrganizationModel(
            organization_id=org_id,
            name=org["name"],
            description=org["description"],
            owner_id=org.get("owner_id"),
            organization_members=organization_members
        ))
    
    return organizations

@router.post("/organization/{organization_id}/invite", response_model=dict)
async def invite_user_to_organization(
    organization_id: str,
    invite_request: InviteUserRequest,  
    current_user: dict = Depends(get_current_user)
):
    user_email = invite_request.user_email  
    
    # Check if organization exists
    organization = await db["organizations"].find_one({"_id": ObjectId(organization_id)})
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")

    # Check if the user with the given email exists
    user = await db["users"].find_one({"email": user_email})  
    name = user['name'] if user else None  # Get the user's name or set to None if not found

    # Create the new member
    new_member = {
        "name": name,  # Use the retrieved name or None
        "email": user_email,
        "access_level": "member"
    }

    # Add the member to the organization_members list
    await db["organizations"].update_one(
        {"_id": ObjectId(organization_id)},
        {"$push": {"organization_members": new_member}}
    )

    return {"message": "User invited successfully"}





@router.get("/organization/{organization_id}", response_model=OrganizationModel)
async def get_organization(
    organization_id: str,
    current_user: dict = Depends(get_current_user)
):
    # Check if organization exists
    organization = await db["organizations"].find_one({"_id": ObjectId(organization_id)})
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")

    # Return the organization data
    return organization_helper(organization)
