import os
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

security = HTTPBasic()


def _load_secret(secret_path: str) -> str:
    """
    Load a secret from a file (Docker Secrets or volume mount).
    
    The configuration no longer supports reading credentials from the
    environment. A file **must** be present at the specified path or a
    ``ValueError`` is raised. This enforces the use of Docker secrets or
    mounted files only.
    
    Args:
        secret_path: Path to the secret file
        
    Returns:
        The secret value
        
    Raises:
        ValueError: If secret cannot be loaded
    """
    # Try to read from file first (Docker Secrets pattern)
    if os.path.isfile(secret_path):
        try:
            with open(secret_path, 'r') as f:
                return f.read().strip()
        except Exception as e:
            raise ValueError(f"Failed to read secret from {secret_path}: {e}")

    # No secret found
    raise ValueError(
        f"Secret not found at {secret_path}. "
        f"Credentials must be provided via Docker Secrets or mounted files."
    )


# Load credentials from secret files only (no environment fallback)
# Priority: Docker Secrets file > mounted files
try:
    API_USERNAME = _load_secret("/run/secrets/api_username")
except ValueError:
    API_USERNAME = None

try:
    API_PASSWORD = _load_secret("/run/secrets/api_password")
except ValueError:
    API_PASSWORD = None


def _ensure_credentials_loaded():
    """Verify that credentials are loaded before starting the app.

    The service requires a username/password pair, but for local development
    it's often convenient not to have to configure secrets. Setting the
    environment variable ``DEV_ALLOW_INSECURE`` to any non-empty value will
    cause the app to fall back to a hard‑coded ``admin/admin`` pair and log a
    warning instead of crashing. This is **NOT** suitable for production.
    """
    if not API_USERNAME or not API_PASSWORD:
        # development override
        if os.getenv("DEV_ALLOW_INSECURE"):
            import logging
            logging.warning(
                "API credentials not provided; falling back to insecure default 'admin/admin' because DEV_ALLOW_INSECURE is set."
            )
            global API_USERNAME, API_PASSWORD
            API_USERNAME = "admin"
            API_PASSWORD = "admin"
            return

        raise RuntimeError(
            "API credentials not configured! "
            "Please provide credentials via:\n"
            "  1. Docker Secrets: /run/secrets/api_username and /run/secrets/api_password\n"
            "  2. Volume mounts: /app/secrets/username and /app/secrets/password"
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
