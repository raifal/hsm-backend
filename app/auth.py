import os
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

security = HTTPBasic()


def _load_properties(properties_path: str) -> dict:
    """
    Load properties from a .properties file.
    
    Args:
        properties_path: Path to the .properties file
        
    Returns:
        Dictionary with properties (key-value pairs)
        
    Raises:
        ValueError: If properties file cannot be loaded
    """
    if not os.path.isfile(properties_path):
        raise ValueError(f"Properties file not found at {properties_path}")
    
    properties = {}
    try:
        with open(properties_path, 'r') as f:
            for line in f:
                line = line.strip()
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                # Parse key=value
                if '=' in line:
                    key, value = line.split('=', 1)
                    properties[key.strip()] = value.strip()
    except Exception as e:
        raise ValueError(f"Failed to read properties from {properties_path}: {e}")
    
    return properties


# Load credentials from properties file
# Try multiple paths in order of priority:
# 1. /app/hsm-backend.properties (Docker volume mount)
# 2. ./hsm-backend.properties (local development)
API_USERNAME = None
API_PASSWORD = None
# Database configuration loaded from properties
DB_HOST: str | None = None
DB_PORT: int | None = None
DB_NAME: str | None = None
DB_USER: str | None = None
DB_PASSWORD: str | None = None

for properties_path in ["/app/hsm-backend.properties", "./hsm-backend.properties"]:
    try:
        properties = _load_properties(properties_path)
        API_USERNAME = properties.get("api.username")
        API_PASSWORD = properties.get("api.password")
        # database settings are kept as module-level variables too
        DB_HOST = properties.get("db.host")
        DB_PORT = int(properties.get("db.port")) if properties.get("db.port") else None
        DB_NAME = properties.get("db.name")
        DB_USER = properties.get("db.user")
        DB_PASSWORD = properties.get("db.password")
        if API_USERNAME and API_PASSWORD:
            break
    except ValueError:
        continue


def _ensure_credentials_loaded():
    """Verify that credentials are loaded from properties file before starting the app."""
    if not API_USERNAME or not API_PASSWORD:
        raise RuntimeError(
            "API credentials not configured! "
            "Please ensure hsm-backend.properties file exists with 'api.username' and 'api.password' entries"
        )


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
