from pydantic import BaseModel, EmailStr, Field

class SignUpModel(BaseModel):
    name: str = Field(..., description="The full name of the user.")
    email: EmailStr = Field(..., description="The email address of the user.")
    password: str = Field(..., min_length=6, description="The password for the account. Minimum length is 6 characters.")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Maryam Eissa",
                "email": "MaryamEissa@example.com",
                "password": "yourpassword"
            }
        }

class SignInModel(BaseModel):
    email: EmailStr = Field(..., description="The email address of the user.")
    password: str = Field(..., description="The password for the account.")

    class Config:
        json_schema_extra = {
            "example": {
               "email": "MaryamEissa@example.com",
                "password": "yourpassword"
            }
        }

class AuthResponseModel(BaseModel):
    message: str = Field(..., description="Response message indicating the status of the request.")
    access_token: str = Field(..., description="The JWT access token for the user.")
    refresh_token: str = Field(..., description="The JWT refresh token for the user.")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Login successful",
                "access_token": "your_access_token_here",
                "refresh_token": "your_refresh_token_here"
            }
        }


# Request Body Model
class RevokeTokenRequest(BaseModel):
    refresh_token: str