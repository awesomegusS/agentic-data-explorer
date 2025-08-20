# app/utils/logging_config.py
"""
Logging configuration for structured logging.
"""

import logging
import sys
from datetime import datetime

def setup_logging(log_level: str = "INFO") -> None:
    """Setup application logging"""
    
    # Create custom formatter
    class CustomFormatter(logging.Formatter):
        """Custom formatter with colors and emojis"""
        
        # Color codes
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
            
            # Format message
            log_message = f"{emoji} {record.getMessage()}"
            
            # Add timestamp and level
            timestamp = datetime.now().strftime("%H:%M:%S")
            formatted = f"{color}[{timestamp}] {record.levelname:8} {log_message}{self.RESET}"
            
            return formatted
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(CustomFormatter())
    root_logger.addHandler(console_handler)
    
    # Set specific logger levels
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    
    # Create application logger
    app_logger = logging.getLogger("app")
    app_logger.setLevel(getattr(logging, log_level.upper()))