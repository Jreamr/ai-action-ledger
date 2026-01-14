from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader
from app.config import get_settings

# Define the API key header
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    """
    Verify the API key from the X-API-Key header.
    Returns the API key if valid, raises 401 if missing or invalid.
    """
    settings = get_settings()
    
    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-API-Key header"
        )
    
    if api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    return api_key