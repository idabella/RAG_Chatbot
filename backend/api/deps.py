from typing import Generator, Optional, Dict, Any
from datetime import datetime
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from core.config import settings
from core.database import get_db
from core.security import token_manager, SecurityException
from models.user import User, UserRole

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user from token"""
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Use our custom token manager instead of jose
        payload = token_manager.verify_token(credentials.credentials, "access")
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
            
    except SecurityException:
        raise credentials_exception
    except Exception:
        raise credentials_exception
    
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception
        
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user"""
    
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


def get_current_admin_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Get current admin user"""
    
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


def get_current_moderator_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Get current moderator or admin user"""
    
    if current_user.role not in [UserRole.ADMIN, UserRole.MODERATOR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


def validate_permissions(required_role: UserRole):
    """Create a permission validator for a specific role"""
    
    def permission_checker(
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        role_hierarchy = {
            UserRole.USER: 1,
            UserRole.MODERATOR: 2,
            UserRole.ADMIN: 3
        }
        
        user_level = role_hierarchy.get(current_user.role, 0)
        required_level = role_hierarchy.get(required_role, 999)
        
        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied. Required role: {required_role.value}"
            )
        return current_user
    
    return permission_checker


class RateLimiter:
    """Simple rate limiter based on client IP and user agent"""
    
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}
    
    def __call__(self, request: Request):
        """Check if request is within rate limits"""
        
        client_ip = request.client.host
        user_agent = request.headers.get("user-agent", "")
        client_id = f"{client_ip}:{hash(user_agent)}"
        
        current_time = datetime.utcnow()
        
        if client_id not in self.requests:
            self.requests[client_id] = []
        
        client_requests = self.requests[client_id]
        
        # Clean old requests
        cutoff_time = current_time.timestamp() - self.window_seconds
        client_requests[:] = [req_time for req_time in client_requests if req_time > cutoff_time]
        
        if len(client_requests) >= self.max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Max {self.max_requests} requests per {self.window_seconds} seconds"
            )
        
        client_requests.append(current_time.timestamp())


def get_rate_limiter(max_requests: int = 100, window_seconds: int = 60):
    """Create a rate limiter with specified limits"""
    return RateLimiter(max_requests, window_seconds)


class AuthenticatedRateLimiter:
    """Rate limiter for authenticated users with role-based limits"""
    
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.user_requests = {}
    
    def __call__(self, current_user: User = Depends(get_current_active_user)):
        """Check rate limits for authenticated user"""
        
        user_id = current_user.id
        current_time = datetime.utcnow()
        
        if user_id not in self.user_requests:
            self.user_requests[user_id] = []
        
        user_request_times = self.user_requests[user_id]
        
        # Clean old requests
        cutoff_time = current_time.timestamp() - self.window_seconds
        user_request_times[:] = [req_time for req_time in user_request_times if req_time > cutoff_time]
        
        # Role-based rate limit multipliers
        max_requests = self.max_requests
        if current_user.role == UserRole.ADMIN:
            max_requests *= 5
        elif current_user.role == UserRole.MODERATOR:
            max_requests *= 2
        
        if len(user_request_times) >= max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded for user. Max {max_requests} requests per {self.window_seconds} seconds"
            )
        
        user_request_times.append(current_time.timestamp())


def get_authenticated_rate_limiter(max_requests: int = 50, window_seconds: int = 60):
    """Create an authenticated rate limiter with specified limits"""
    return AuthenticatedRateLimiter(max_requests, window_seconds)


def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get user from token if provided, otherwise return None"""
    
    if credentials is None:
        return None
    
    try:
        # Use our custom token manager instead of jose
        payload = token_manager.verify_token(credentials.credentials, "access")
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
            
        user = db.query(User).filter(User.id == int(user_id)).first()
        return user if user and user.is_active else None
        
    except (SecurityException, Exception):
        return None


def get_user_context(
    request: Request,
    current_user: Optional[User] = Depends(get_optional_user)
) -> Dict[str, Any]:
    """Get comprehensive user context for request"""
    
    return {
        "user": current_user,
        "user_id": current_user.id if current_user else None,
        "is_authenticated": current_user is not None,
        "client_ip": request.client.host,
        "user_agent": request.headers.get("user-agent"),
        "timestamp": datetime.utcnow(),
        "permissions": {
            "is_admin": current_user.role == UserRole.ADMIN if current_user else False,
            "is_moderator": current_user.role in [UserRole.ADMIN, UserRole.MODERATOR] if current_user else False,
            "can_upload": current_user is not None,
            "can_chat": current_user is not None,
        }
    }


# Pre-configured rate limiters for common use cases
general_rate_limiter = Depends(get_rate_limiter(100, 60))          # 100 requests per minute
api_rate_limiter = Depends(get_rate_limiter(200, 60))              # 200 requests per minute
chat_rate_limiter = Depends(get_authenticated_rate_limiter(30, 60)) # 30 requests per minute for users
upload_rate_limiter = Depends(get_rate_limiter(5, 300))            # 5 uploads per 5 minutes

# Pre-configured permission dependencies
admin_required = Depends(get_current_admin_user)
moderator_required = Depends(get_current_moderator_user)
user_required = Depends(get_current_active_user)

admin_permission = Depends(validate_permissions(UserRole.ADMIN))
moderator_permission = Depends(validate_permissions(UserRole.MODERATOR))


# Enhanced permission validators for specific actions
def require_admin_or_owner(resource_owner_id_field: str = "user_id"):
    """Create a dependency that allows access to admins or resource owners"""
    
    def check_admin_or_owner(
        current_user: User = Depends(get_current_active_user),
        **kwargs
    ) -> User:
        # If user is admin, allow access
        if current_user.role == UserRole.ADMIN:
            return current_user
        
        # Check if user owns the resource
        resource_owner_id = kwargs.get(resource_owner_id_field)
        if resource_owner_id and current_user.id == resource_owner_id:
            return current_user
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access your own resources or need admin privileges"
        )
    
    return check_admin_or_owner


def require_role_or_higher(minimum_role: UserRole):
    """Create a dependency that requires a minimum role level"""
    
    def check_role(current_user: User = Depends(get_current_active_user)) -> User:
        role_hierarchy = {
            UserRole.USER: 1,
            UserRole.MODERATOR: 2,
            UserRole.ADMIN: 3
        }
        
        user_level = role_hierarchy.get(current_user.role, 0)
        required_level = role_hierarchy.get(minimum_role, 999)
        
        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Minimum required role: {minimum_role.value}"
            )
        
        return current_user
    
    return check_role


class RequestLogger:
    """Simple request logging for debugging and monitoring"""
    
    def __init__(self, log_requests: bool = True):
        self.log_requests = log_requests
        self.request_log = []
    
    def __call__(
        self, 
        request: Request,
        current_user: Optional[User] = Depends(get_optional_user)
    ):
        if self.log_requests:
            log_entry = {
                "timestamp": datetime.utcnow(),
                "method": request.method,
                "url": str(request.url),
                "client_ip": request.client.host,
                "user_id": current_user.id if current_user else None,
                "user_role": current_user.role if current_user else None,
            }
            self.request_log.append(log_entry)
            
            # Keep only last 1000 entries
            if len(self.request_log) > 1000:
                self.request_log = self.request_log[-1000:]
    
    def get_recent_logs(self, limit: int = 100) -> list:
        return self.request_log[-limit:]


# Global request logger instance
request_logger = RequestLogger(log_requests=getattr(settings, 'LOG_REQUESTS', False))
log_request = Depends(request_logger)


__all__ = [
    "get_current_user",
    "get_current_active_user", 
    "get_current_admin_user",
    "get_current_moderator_user",
    "get_optional_user",
    "get_user_context",
    "validate_permissions",
    "require_admin_or_owner",
    "require_role_or_higher",
    "RateLimiter",
    "AuthenticatedRateLimiter",
    "get_rate_limiter",
    "get_authenticated_rate_limiter",
    "RequestLogger",
    "general_rate_limiter",
    "api_rate_limiter", 
    "chat_rate_limiter",
    "upload_rate_limiter",
    "admin_required",
    "moderator_required",
    "user_required",
    "admin_permission",
    "moderator_permission",
    "log_request",
]