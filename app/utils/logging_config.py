# app/utils/logging_config.py
"""
Comprehensive logging configuration for Agentic Data Explorer.
Provides structured, colorized logging with different output formats.
"""

import logging
import logging.handlers
import sys
import os
from datetime import datetime
from typing import Optional
import json
from pathlib import Path

class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors and emojis for console output"""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green  
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
    }
    RESET = '\033[0m'
    
    # Emojis for log levels
    EMOJIS = {
        'DEBUG': '🔍',
        'INFO': 'ℹ️ ',
        'WARNING': '⚠️ ',
        'ERROR': '❌',
        'CRITICAL': '💥'
    }
    
    def format(self, record):
        # Add emoji and color
        emoji = self.EMOJIS.get(record.levelname, '')
        color = self.COLORS.get(record.levelname, '')
        
        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime("%H:%M:%S.%f")[:-3]
        
        # Get the logger name (module)
        logger_name = record.name.split('.')[-1] if '.' in record.name else record.name
        
        # Format the message
        log_message = record.getMessage()
        
        # Build the formatted message
        formatted = f"{color}[{timestamp}] {emoji} {record.levelname:8} {logger_name:15} {log_message}{self.RESET}"
        
        # Add exception info if present
        if record.exc_info:
            formatted += f"\n{self.formatException(record.exc_info)}"
        
        return formatted

class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging (production use)"""
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'thread': record.thread,
            'thread_name': record.threadName,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': self.formatException(record.exc_info)
            }
        
        # Add extra fields from the record
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                          'filename', 'module', 'exc_info', 'exc_text', 'stack_info',
                          'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
                          'thread', 'threadName', 'processName', 'process', 'getMessage']:
                log_entry[key] = value
        
        return json.dumps(log_entry)

class PerformanceFilter(logging.Filter):
    """Filter to add performance metrics to log records"""
    
    def filter(self, record):
        # Add performance context if available
        if hasattr(record, 'execution_time'):
            record.msg = f"{record.msg} [⏱️ {record.execution_time:.2f}ms]"
        
        return True

def setup_logging(
    log_level: str = "INFO",
    log_format: str = "colored",  # "colored", "json", "simple"
    log_file: Optional[str] = None,
    enable_file_logging: bool = True,
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> None:
    """
    Setup comprehensive logging configuration
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Output format ("colored", "json", "simple")
        log_file: Specific log file path (optional)
        enable_file_logging: Whether to enable file logging
        max_file_size: Maximum log file size before rotation
        backup_count: Number of backup files to keep
    """
    
    # Create logs directory
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Clear existing handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Set root logger level
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    
    # Choose formatter based on format preference
    if log_format == "colored":
        console_formatter = ColoredFormatter()
    elif log_format == "json":
        console_formatter = JSONFormatter()
    else:  # simple
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    console_handler.setFormatter(console_formatter)
    
    # Add performance filter
    performance_filter = PerformanceFilter()
    console_handler.addFilter(performance_filter)
    
    root_logger.addHandler(console_handler)
    
    # File logging
    if enable_file_logging:
        # Default log file path
        if not log_file:
            timestamp = datetime.now().strftime("%Y%m%d")
            log_file = logs_dir / f"agentic_data_explorer_{timestamp}.log"
        
        # Rotating file handler
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)  # File logs everything
        
        # Always use JSON format for file logs (better for analysis)
        file_formatter = JSONFormatter()
        file_handler.setFormatter(file_formatter)
        file_handler.addFilter(performance_filter)
        
        root_logger.addHandler(file_handler)
        
        print(f"📝 File logging enabled: {log_file}")
    
    # Configure specific loggers
    configure_component_loggers()
    
    # Log startup message
    logger = logging.getLogger("app.logging")
    logger.info("🚀 Logging system initialized")
    logger.info(f"📊 Log level: {log_level}")
    logger.info(f"🎨 Console format: {log_format}")
    logger.info(f"📁 File logging: {'enabled' if enable_file_logging else 'disabled'}")

def configure_component_loggers():
    """Configure logging levels for different components"""
    
    # Reduce noise from external libraries
    logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("snowflake.connector").setLevel(logging.WARNING)
    logging.getLogger("langchain").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    
    # Configure app component loggers
    app_loggers = [
        "app.main",
        "app.services.database",
        "app.services.local_agent", 
        "app.routers.query",
        "app.routers.health",
        "app.utils.config"
    ]
    
    for logger_name in app_loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.INFO)

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the specified name"""
    return logging.getLogger(name)

def log_performance(logger: logging.Logger, operation: str, execution_time: float, **kwargs):
    """Log performance metrics with structured data"""
    extra_data = {
        'operation': operation,
        'execution_time': execution_time,
        **kwargs
    }
    
    if execution_time > 5000:  # > 5 seconds
        logger.warning(f"Slow operation: {operation}", extra=extra_data)
    elif execution_time > 1000:  # > 1 second
        logger.info(f"Operation completed: {operation}", extra=extra_data)
    else:
        logger.debug(f"Operation completed: {operation}", extra=extra_data)

def log_api_request(logger: logging.Logger, method: str, path: str, status_code: int, 
                   execution_time: float, user_agent: str = None):
    """Log API request with structured data"""
    extra_data = {
        'http_method': method,
        'http_path': path,
        'http_status': status_code,
        'execution_time': execution_time,
        'user_agent': user_agent
    }
    
    if status_code >= 500:
        logger.error(f"API Error: {method} {path} - {status_code}", extra=extra_data)
    elif status_code >= 400:
        logger.warning(f"API Client Error: {method} {path} - {status_code}", extra=extra_data)
    else:
        logger.info(f"API Request: {method} {path} - {status_code}", extra=extra_data)

def log_database_query(logger: logging.Logger, query: str, execution_time: float, 
                      row_count: int = None, error: str = None):
    """Log database query with performance metrics"""
    extra_data = {
        'query_type': 'database',
        'execution_time': execution_time,
        'row_count': row_count,
        'query_preview': query[:100] + "..." if len(query) > 100 else query
    }
    
    if error:
        extra_data['error'] = error
        logger.error(f"Database query failed", extra=extra_data)
    elif execution_time > 10000:  # > 10 seconds
        logger.warning(f"Slow database query ({execution_time:.2f}ms)", extra=extra_data)
    else:
        logger.info(f"Database query completed ({row_count} rows)", extra=extra_data)

def log_ai_interaction(logger: logging.Logger, question: str, sql_generated: str,
                      execution_time: float, success: bool, error: str = None):
    """Log AI agent interactions"""
    extra_data = {
        'ai_operation': 'sql_generation',
        'execution_time': execution_time,
        'success': success,
        'question_length': len(question),
        'sql_length': len(sql_generated) if sql_generated else 0
    }
    
    if error:
        extra_data['error'] = error
        logger.error(f"AI query failed: {question[:50]}...", extra=extra_data)
    elif not success:
        logger.warning(f"AI query unsuccessful: {question[:50]}...", extra=extra_data)
    else:
        logger.info(f"AI query successful: {question[:50]}...", extra=extra_data)

class LoggingMiddleware:
    """Middleware to add logging context to requests"""
    
    def __init__(self):
        self.logger = logging.getLogger("app.middleware")
    
    async def __call__(self, request, call_next):
        start_time = datetime.now()
        
        # Log request start
        self.logger.debug(f"Request started: {request.method} {request.url.path}")
        
        try:
            response = await call_next(request)
            
            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # Log request completion
            log_api_request(
                self.logger,
                request.method,
                str(request.url.path),
                response.status_code,
                execution_time,
                request.headers.get("user-agent")
            )
            
            return response
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            self.logger.error(
                f"Request failed: {request.method} {request.url.path}",
                extra={
                    'execution_time': execution_time,
                    'error': str(e),
                    'error_type': type(e).__name__
                }
            )
            raise

# Example usage and testing
if __name__ == "__main__":
    # Test different logging configurations
    print("🧪 Testing logging configurations...")
    
    # Test colored format
    print("\n1. Testing colored format:")
    setup_logging(log_level="DEBUG", log_format="colored", enable_file_logging=False)
    
    logger = get_logger("test.colored")
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    
    # Test performance logging
    log_performance(logger, "test_operation", 1500.0, rows_processed=100)
    
    # Test JSON format
    print("\n2. Testing JSON format:")
    setup_logging(log_level="INFO", log_format="json", enable_file_logging=False)
    
    logger = get_logger("test.json")
    logger.info("JSON formatted message", extra={"custom_field": "value"})
    
    print("\n✅ Logging tests completed!")