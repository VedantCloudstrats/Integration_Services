from fastapi import Header, HTTPException, status

async def verify_api_key(x_api_key: str = Header(None)):
    """
    Verifies that the X-API-Key header matches the allowed secret key.
    Enables secure access for external applications.
    """
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API Key. Please provide the 'X-API-Key' header."
        )
    if x_api_key != "dev-secret-key":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API Key."
        )
    return x_api_key
