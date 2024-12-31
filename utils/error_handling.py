import logging
import traceback
import streamlit as st
from functools import wraps
from typing import Callable, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AppError(Exception):
    """Base exception class for application errors"""
    def __init__(self, message: str, error_type: str = "General Error"):
        self.message = message
        self.error_type = error_type
        super().__init__(self.message)

class DatabaseError(AppError):
    """Database related errors"""
    def __init__(self, message: str):
        super().__init__(message, "Database Error")

class ValidationError(AppError):
    """Data validation errors"""
    def __init__(self, message: str):
        super().__init__(message, "Validation Error")

def handle_error(func: Callable) -> Callable:
    """Decorator for handling errors in Streamlit pages and components"""
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        try:
            return func(*args, **kwargs)
        except DatabaseError as e:
            logger.error(f"Database error in {func.__name__}: {str(e)}")
            logger.debug(traceback.format_exc())
            st.error(f"😕 {e.message} Please try again later.")
        except ValidationError as e:
            logger.warning(f"Validation error in {func.__name__}: {str(e)}")
            st.warning(f"⚠️ {e.message}")
        except Exception as e:
            logger.critical(f"Unexpected error in {func.__name__}: {str(e)}")
            logger.debug(traceback.format_exc())
            st.error("😔 Something went wrong. Our team has been notified.")
        return None
    return wrapper

def log_error(error: Exception, context: str = "") -> None:
    """Log error with context information"""
    logger.error(f"Error in {context}: {str(error)}")
    logger.debug(traceback.format_exc())
