from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional


class InviteUserRequest(BaseModel):
    user_email: EmailStr


class OrganizationModel(BaseModel):
    organization_id: Optional[str] = Field(default=None, description="The id of the organization.")
    name: str = Field(..., description="The name of the organization.")
    description: str = Field(..., description="A brief description of the organization.")
    owner_id: Optional[str] = Field(default=None, description="The owner of the organization.")
    organization_members: Optional[List[dict]] = Field(
        default=[], description="List of members associated with the organization."
    )

    class Config:
        json_schema_extra = {
            "example": {
                "organization_id": "djhuqyuiwosppod",
                "name": "Example Organization",
                "description": "This organization focuses on improving community services.",
                "owner_id": "12345",
                "organization_members": [
                    {
                        "name": "John Doe",
                        "email": "john.doe@example.com",
                        "access_level": "admin"
                    },
                    {
                        "name": "Jane Smith",
                        "email": "jane.smith@example.com",
                        "access_level": "member"
                    }
                ]
            }
        }
