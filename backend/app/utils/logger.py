"""
Structured Logging System for FinWall Invoice Platform

This module provides:
- Per-user logging (logs organized by user email)
- System-level logging for unauthenticated requests and startup events
- Structured log format with timestamps, log levels, and context
"""

import os
import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Optional
from functools import lru_cache


class StructuredFormatter(logging.Formatter):
    """Custom formatter that outputs structured JSON logs"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add extra fields if present
        if hasattr(record, 'user_email'):
            log_data['user_email'] = record.user_email
        if hasattr(record, 'organization_id'):
            log_data['organization_id'] = record.organization_id
        if hasattr(record, 'request_id'):
            log_data['request_id'] = record.request_id
        if hasattr(record, 'method'):
            log_data['method'] = record.method
        if hasattr(record, 'path'):
            log_data['path'] = record.path
        if hasattr(record, 'status_code'):
            log_data['status_code'] = record.status_code
        if hasattr(record, 'duration_ms'):
            log_data['duration_ms'] = record.duration_ms
        if hasattr(record, 'ip_address'):
            log_data['ip_address'] = record.ip_address
        if hasattr(record, 'error'):
            log_data['error'] = record.error
        if hasattr(record, 'extra_data'):
            log_data['extra_data'] = record.extra_data
            
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
            
        return json.dumps(log_data, default=str)


class LoggerManager:
    """
    Manages loggers for the application.
    Creates per-user loggers and system logger.
    """
    
    _instance = None
    _loggers: dict = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.log_dir = Path(os.getenv("LOG_DIR", "logs"))
        self.log_level = getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper())
        self._initialized = True
        
        # Ensure base log directory exists
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create system logger
        self._system_logger = self._create_logger("system", self.log_dir / "system")
        
    def _create_logger(self, name: str, log_path: Path) -> logging.Logger:
        """Create a logger with file and optional console handlers"""
        
        # Ensure log directory exists
        log_path.mkdir(parents=True, exist_ok=True)
        
        logger = logging.getLogger(name)
        logger.setLevel(self.log_level)
        
        # Avoid duplicate handlers
        if logger.handlers:
            return logger
        
        # File handler with structured format
        today = datetime.now().strftime("%Y-%m-%d")
        file_handler = logging.FileHandler(
            log_path / f"{today}.log",
            encoding='utf-8'
        )
        file_handler.setLevel(self.log_level)
        file_handler.setFormatter(StructuredFormatter())
        logger.addHandler(file_handler)
        
        # Console handler for development (simpler format)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(self.log_level)
        console_format = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_format)
        logger.addHandler(console_handler)
        
        # Prevent propagation to root logger
        logger.propagate = False
        
        return logger
    
    def get_system_logger(self) -> logging.Logger:
        """Get the system-level logger for startup events and unauthenticated requests"""
        return self._system_logger
    
    def get_user_logger(self, user_email: str) -> logging.Logger:
        """
        Get or create a logger for a specific user.
        Logs are stored in: logs/{sanitized_email}/
        """
        if user_email in self._loggers:
            return self._loggers[user_email]
        
        # Sanitize email for use as folder name
        sanitized_email = self._sanitize_email(user_email)
        user_log_path = self.log_dir / sanitized_email
        
        logger = self._create_logger(f"user.{sanitized_email}", user_log_path)
        self._loggers[user_email] = logger
        
        return logger
    
    def _sanitize_email(self, email: str) -> str:
        """
        Sanitize email for use as folder name.
        Replace @ and . with safe characters.
        """
        return email.replace("@", "_at_").replace(".", "_")
    
    def log_request(
        self,
        user_email: Optional[str],
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        ip_address: str,
        request_id: str,
        organization_id: Optional[str] = None,
        error: Optional[str] = None,
        extra_data: Optional[dict] = None
    ):
        """Log an API request to the appropriate logger"""
        
        if user_email:
            logger = self.get_user_logger(user_email)
        else:
            logger = self._system_logger
        
        # Determine log level based on status code
        if status_code >= 500:
            level = logging.ERROR
        elif status_code >= 400:
            level = logging.WARNING
        else:
            level = logging.INFO
        
        message = f"{method} {path} -> {status_code} ({duration_ms:.2f}ms)"
        
        # Create log record with extra fields
        extra = {
            'user_email': user_email or 'anonymous',
            'organization_id': organization_id,
            'request_id': request_id,
            'method': method,
            'path': path,
            'status_code': status_code,
            'duration_ms': duration_ms,
            'ip_address': ip_address,
        }
        
        if error:
            extra['error'] = error
        if extra_data:
            extra['extra_data'] = extra_data
            
        logger.log(level, message, extra=extra)
    
    def log_startup(self, message: str, extra_data: Optional[dict] = None):
        """Log a startup event"""
        extra = {'extra_data': extra_data} if extra_data else {}
        self._system_logger.info(f"[STARTUP] {message}", extra=extra)
    
    def log_shutdown(self, message: str):
        """Log a shutdown event"""
        self._system_logger.info(f"[SHUTDOWN] {message}")
    
    def log_db_operation(
        self,
        user_email: Optional[str],
        operation: str,
        table: str,
        record_id: Optional[str] = None,
        extra_data: Optional[dict] = None
    ):
        """Log a database operation"""
        if user_email:
            logger = self.get_user_logger(user_email)
        else:
            logger = self._system_logger
        
        message = f"[DB] {operation} on {table}"
        if record_id:
            message += f" (id: {record_id})"
        
        extra = {
            'user_email': user_email or 'system',
            'extra_data': {
                'operation': operation,
                'table': table,
                'record_id': record_id,
                **(extra_data or {})
            }
        }
        
        logger.info(message, extra=extra)
    
    def log_error(
        self,
        user_email: Optional[str],
        error: str,
        exc_info: bool = False,
        extra_data: Optional[dict] = None
    ):
        """Log an error"""
        if user_email:
            logger = self.get_user_logger(user_email)
        else:
            logger = self._system_logger
        
        extra = {'error': error}
        if extra_data:
            extra['extra_data'] = extra_data
            
        logger.error(f"[ERROR] {error}", exc_info=exc_info, extra=extra)


# Singleton instance
@lru_cache()
def get_logger_manager() -> LoggerManager:
    """Get the singleton LoggerManager instance"""
    return LoggerManager()


# Convenience functions
def get_system_logger() -> logging.Logger:
    """Get the system logger"""
    return get_logger_manager().get_system_logger()


def get_user_logger(user_email: str) -> logging.Logger:
    """Get a user-specific logger"""
    return get_logger_manager().get_user_logger(user_email)


def log_request(**kwargs):
    """Log an API request"""
    get_logger_manager().log_request(**kwargs)


def log_startup(message: str, extra_data: Optional[dict] = None):
    """Log a startup event"""
    get_logger_manager().log_startup(message, extra_data)


def log_shutdown(message: str):
    """Log a shutdown event"""
    get_logger_manager().log_shutdown(message)


def log_db_operation(**kwargs):
    """Log a database operation"""
    get_logger_manager().log_db_operation(**kwargs)


def log_error(**kwargs):
    """Log an error"""
    get_logger_manager().log_error(**kwargs)
