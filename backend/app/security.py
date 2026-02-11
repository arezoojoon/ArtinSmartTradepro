from datetime import datetime, timedelta
from typing import Any, Union, Dict
from jose import jwt
from passlib.context import CryptContext
from app.config import get_settings
import time

settings = get_settings()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Token blacklist with TTL — auto-expires entries after ACCESS_TOKEN_EXPIRE_MINUTES.
# In production, replace with Redis: redis.setex(token, TTL, "1")
_BLACKLIST_MAX_SIZE = 10_000
_token_blacklist: Dict[str, float] = {}  # token -> expiry_timestamp


def _cleanup_blacklist():
    """Remove expired tokens from blacklist."""
    now = time.time()
    expired = [k for k, v in _token_blacklist.items() if v < now]
    for k in expired:
        del _token_blacklist[k]


def create_access_token(subject: Union[str, Any], additional_claims: Dict[str, Any] = {}, expires_delta: timedelta = None) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {"exp": expire, "sub": str(subject), "type": "access"}
    to_encode.update(additional_claims)
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_refresh_token(subject: Union[str, Any], additional_claims: Dict[str, Any] = {}) -> str:
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {"exp": expire, "sub": str(subject), "type": "refresh"}
    to_encode.update(additional_claims)
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_password_reset_token(email: str) -> str:
    expire = datetime.utcnow() + timedelta(hours=1)  # 1 hour expiry
    to_encode = {"exp": expire, "sub": email, "type": "password_reset"}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def verify_password_reset_token(token: str) -> str:
    """Returns email if valid, raises otherwise."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != "password_reset":
            raise ValueError("Invalid token type")
        email = payload.get("sub")
        if not email:
            raise ValueError("No email in token")
        return email
    except Exception:
        raise ValueError("Invalid or expired reset token")

def blacklist_token(token: str):
    """Add token to blacklist with TTL (auto-expires)."""
    # Cleanup periodically
    if len(_token_blacklist) > _BLACKLIST_MAX_SIZE:
        _cleanup_blacklist()
    # If still over limit after cleanup, evict oldest
    if len(_token_blacklist) > _BLACKLIST_MAX_SIZE:
        oldest_key = min(_token_blacklist, key=_token_blacklist.get)
        del _token_blacklist[oldest_key]
    
    ttl_seconds = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    _token_blacklist[token] = time.time() + ttl_seconds

def is_token_blacklisted(token: str) -> bool:
    """Check if token has been invalidated (with auto-expiry)."""
    if token not in _token_blacklist:
        return False
    if _token_blacklist[token] < time.time():
        del _token_blacklist[token]  # Expired, remove
        return False
    return True

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)
