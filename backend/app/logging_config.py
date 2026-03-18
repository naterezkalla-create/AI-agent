"""Structured logging configuration for the application."""

import logging
import json
from datetime import datetime
from typing import Any, Dict, Optional


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, "extra_data") and record.extra_data:
            log_data.update(record.extra_data)
        
        return json.dumps(log_data)


class StructuredLogger:
    """Wrapper for structured logging with custom fields."""
    
    def __init__(self, logger_name: str):
        self.logger = logging.getLogger(logger_name)
    
    def log(
        self,
        level: int,
        message: str,
        extra_data: Optional[Dict[str, Any]] = None,
        exc_info: bool = False,
    ):
        """Log a message with optional extra data."""
        record = self.logger.makeRecord(
            self.logger.name,
            level,
            "(unknown file)",
            0,
            message,
            args=(),
            exc_info=None,
        )
        
        if extra_data:
            record.extra_data = extra_data
        
        if exc_info:
            record.exc_info = True
        
        self.logger.handle(record)
    
    def debug(self, message: str, extra_data: Optional[Dict[str, Any]] = None):
        """Log debug message."""
        self.log(logging.DEBUG, message, extra_data)
    
    def info(self, message: str, extra_data: Optional[Dict[str, Any]] = None):
        """Log info message."""
        self.log(logging.INFO, message, extra_data)
    
    def warning(self, message: str, extra_data: Optional[Dict[str, Any]] = None):
        """Log warning message."""
        self.log(logging.WARNING, message, extra_data)
    
    def error(self, message: str, extra_data: Optional[Dict[str, Any]] = None, exc_info: bool = False):
        """Log error message."""
        self.log(logging.ERROR, message, extra_data, exc_info)
    
    def critical(self, message: str, extra_data: Optional[Dict[str, Any]] = None, exc_info: bool = False):
        """Log critical message."""
        self.log(logging.CRITICAL, message, extra_data, exc_info)


def setup_logging(debug: bool = False):
    """Configure structured logging for the application."""
    log_level = logging.DEBUG if debug else logging.INFO
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    
    # Set formatter
    formatter = JSONFormatter()
    console_handler.setFormatter(formatter)
    
    # Add handler to root logger
    root_logger.addHandler(console_handler)
    
    return root_logger


def get_logger(name: str) -> StructuredLogger:
    """Get a structured logger instance."""
    return StructuredLogger(name)
