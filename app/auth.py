import os
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

# Get credentials from environment variables
API_USERNAME = os.getenv("API_USERNAME", "apiuser")
API_PASSWORD = os.getenv("API_PASSWORD", "apipassword")

security = HTTPBasic()


async def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    """
    Verify HTTP Basic Authentication credentials.
    
    Args:
        credentials: HTTPBasicCredentials from the request
        
    Returns:
        The credentials if valid
        
    Raises:
        HTTPException: If credentials are invalid
    """
    is_correct_username = credentials.username == API_USERNAME
    is_correct_password = credentials.password == API_PASSWORD
    
    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    
    return credentials
