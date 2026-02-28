from datetime import datetime, timedelta, timezone
from typing import Any, Union, Dict
from jose import jwt
from passlib.context import CryptContext
from app.config import get_settings
import time
import logging
import redis

logger = logging.getLogger(__name__)

settings = get_settings()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Redis-backed token blacklist (persistent, shared across workers)
_redis_client = None


def _get_redis():
    """Lazy-init Redis connection for token blacklist."""
    global _redis_client
    if _redis_client is None:
        try:
            _redis_client = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=2,
            )
            _redis_client.ping()
            logger.info("Token blacklist: using Redis")
        except Exception as e:
            logger.warning(f"Token blacklist: Redis unavailable ({e}), falling back to in-memory")
            _redis_client = False  # Sentinel: tried and failed
    return _redis_client if _redis_client else None


# In-memory fallback (only used if Redis is unavailable)
_BLACKLIST_MAX_SIZE = 10_000
_token_blacklist: Dict[str, float] = {}  # token -> expiry_timestamp


def _cleanup_blacklist():
    """Remove expired tokens from in-memory blacklist."""
    now = time.time()
    expired = [k for k, v in _token_blacklist.items() if v < now]
    for k in expired:
        del _token_blacklist[k]


def create_access_token(subject: Union[str, Any], additional_claims: Dict[str, Any] = None, expires_delta: timedelta = None) -> str:
    if additional_claims is None:
        additional_claims = {}
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {"exp": expire, "sub": str(subject), "type": "access"}
    to_encode.update(additional_claims)
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_refresh_token(subject: Union[str, Any], additional_claims: Dict[str, Any] = None) -> str:
    if additional_claims is None:
        additional_claims = {}
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {"exp": expire, "sub": str(subject), "type": "refresh"}
    to_encode.update(additional_claims)
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_password_reset_token(email: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=1)  # 1 hour expiry
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
    """Add token to blacklist. Uses Redis if available, else in-memory."""
    ttl_seconds = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    
    r = _get_redis()
    if r:
        try:
            r.setex(f"blacklist:{token}", ttl_seconds, "1")
            return
        except Exception:
            pass  # Fall through to in-memory
    
    # In-memory fallback
    if len(_token_blacklist) > _BLACKLIST_MAX_SIZE:
        _cleanup_blacklist()
    if len(_token_blacklist) > _BLACKLIST_MAX_SIZE:
        oldest_key = min(_token_blacklist, key=_token_blacklist.get)
        del _token_blacklist[oldest_key]
    _token_blacklist[token] = time.time() + ttl_seconds

def is_token_blacklisted(token: str) -> bool:
    """Check if token has been invalidated."""
    r = _get_redis()
    if r:
        try:
            return r.exists(f"blacklist:{token}") > 0
        except Exception:
            pass  # Fall through to in-memory
    
    # In-memory fallback
    if token not in _token_blacklist:
        return False
    if _token_blacklist[token] < time.time():
        del _token_blacklist[token]
        return False
    return True

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)
