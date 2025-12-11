"""
Centralized logging configuration for the Stock Market application.
Provides structured logging with context and clean formatting.
"""
import logging
import sys
from typing import Any, Dict
from datetime import datetime


class ContextFormatter(logging.Formatter):
    """Custom formatter that adds context information to log messages."""
    
    def format(self, record: logging.LogRecord) -> str:
        # Base format
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        level = record.levelname.ljust(8)
        module = record.name.split('.')[-1][:20].ljust(20)
        
        # Extract request ID from context if available
        try:
            from app.core.request_middleware import get_request_id
            request_id = get_request_id()
        except:
            request_id = None
        
        # Extract context if available
        context_parts = []
        
        # Add request ID first if available
        if request_id:
            context_parts.append(f"req_id={request_id[:8]}")  # Show first 8 chars
        
        if hasattr(record, 'ticker'):
            context_parts.append(f"ticker={record.ticker}")
        if hasattr(record, 'operation'):
            context_parts.append(f"op={record.operation}")
        if hasattr(record, 'duration_ms'):
            context_parts.append(f"duration={record.duration_ms}ms")
        if hasattr(record, 'status'):
            context_parts.append(f"status={record.status}")
        
        context = f"[{', '.join(context_parts)}]" if context_parts else ""
        
        # Format message
        message = record.getMessage()
        
        # Combine
        log_line = f"{timestamp} | {level} | {module} | {context + ' ' if context else ''}{message}"
        
        # Add exception info if present
        if record.exc_info:
            log_line += "\n" + self.formatException(record.exc_info)
        
        return log_line


class SimpleFormatter(logging.Formatter):
    """Simple, clean formatter for production use."""
    
    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        level_emoji = {
            'DEBUG': '🔍',
            'INFO': 'ℹ️ ',
            'WARNING': '⚠️ ',
            'ERROR': '❌',
            'CRITICAL': '🚨'
        }.get(record.levelname, '  ')
        
        message = record.getMessage()
        
        return f"{timestamp} {level_emoji} {message}"


def setup_logging(log_level: str = "INFO", format_type: str = "structured") -> None:
    """
    Configure application-wide logging.
    
    Args:
        log_level: Minimum log level (DEBUG, INFO, WARNING, ERROR)
        format_type: Format type (structured or simple)
    """
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Set formatter
    if format_type == "structured":
        formatter = ContextFormatter()
    else:
        formatter = SimpleFormatter()
    
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Suppress noisy third-party loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("chromadb").setLevel(logging.WARNING)
    logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
    logging.getLogger("transformers").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    
    # Keep SQLAlchemy quiet (no SQL queries)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.dialects").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.orm").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def log_with_context(logger: logging.Logger, level: str, message: str, **context: Any) -> None:
    """
    Log a message with context information.
    
    Args:
        logger: Logger instance
        level: Log level (debug, info, warning, error)
        message: Log message
        **context: Additional context fields (ticker, operation, duration_ms, etc.)
    """
    log_func = getattr(logger, level.lower())
    log_func(message, extra=context)
