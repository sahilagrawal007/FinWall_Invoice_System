"""
Request Logging Middleware

Logs all API requests with:
- Request details (method, path, IP)
- Response status and duration
- User email (if authenticated)
- Structured format to appropriate log file
"""

import time
import uuid
from typing import Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from jose import JWTError
from app.utils.logger import log_request, get_system_logger
from app.core.security import decode_access_token


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that logs all HTTP requests with timing and user information.
    Logs are directed to user-specific folders when authenticated,
    or to system logs when unauthenticated.
    """
    
    async def dispatch(self, request: Request, call_next) -> Response:
        # Generate unique request ID for tracing
        request_id = str(uuid.uuid4())[:8]
        
        # Record start time
        start_time = time.perf_counter()
        
        # Extract user info from token if present
        user_email = None
        organization_id = None
        
        try:
            auth_header = request.headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
                payload = decode_access_token(token)
                user_email = payload.get("email")
                organization_id = payload.get("organization_id")
        except (JWTError, Exception):
            # Token invalid or not present - will log as anonymous
            pass
        
        # Get client IP
        ip_address = request.client.host if request.client else "unknown"
        
        # Store request_id in request state for use in handlers
        request.state.request_id = request_id
        request.state.user_email = user_email
        
        # Process the request
        error_message = None
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            error_message = str(e)
            status_code = 500
            raise
        finally:
            # Calculate duration
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            # Skip logging for static files and health checks
            path = request.url.path
            if not self._should_skip_logging(path):
                log_request(
                    user_email=user_email,
                    method=request.method,
                    path=path,
                    status_code=status_code,
                    duration_ms=duration_ms,
                    ip_address=ip_address,
                    request_id=request_id,
                    organization_id=organization_id,
                    error=error_message
                )
        
        return response
    
    def _should_skip_logging(self, path: str) -> bool:
        """Determine if this request should be skipped for logging"""
        skip_paths = [
            "/health",
            "/favicon.ico",
            "/docs",
            "/redoc",
            "/openapi.json",
        ]
        return any(path.startswith(skip) for skip in skip_paths)
