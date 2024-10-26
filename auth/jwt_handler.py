import time
import jwt
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

JWT_SECRET = os.getenv('SECRET_KEY')
JWT_ALGORITHM = os.getenv('ALGORITHM')

def generate_token(access_token: str, refresh_token: str):
    return {
        "access_token": access_token,
        "refresh_token": refresh_token
    }

def decode_token(token: str):
    try:
        decoded_token = jwt.decode(jwt=token, key=JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return decoded_token if decoded_token['expiry'] >= time.time() else None
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def signin_JWT(user_id: str, name: str, email: str):
    # Generate access token
    access_payload = {
        'user_id': user_id,
        'name': name,
        'email': email,
        'expiry': time.time() + 600  # Access token expires in 10 minutes
    }
    access_token = jwt.encode(payload=access_payload, key=JWT_SECRET, algorithm=JWT_ALGORITHM)

    # Generate refresh token
    refresh_payload = {
        'user_id': user_id,
        'name': name,
        'email': email,
        'expiry': time.time() + 2592000  # Refresh token expires in 30 days
    }
    refresh_token = jwt.encode(payload=refresh_payload, key=JWT_SECRET, algorithm=JWT_ALGORITHM)

    return generate_token(access_token, refresh_token)
