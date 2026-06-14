import logging
import sys
import time
from typing import Any, Callable

# Centralized logger configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("gastrosense")

def log_execution_time(action_name: str) -> Callable:
    """Decorator to measure and log execution time of functions."""
    def decorator(func: Callable) -> Callable:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            logger.info(f"Starting action '{action_name}'...")
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                logger.info(f"Completed action '{action_name}' in {duration:.4f}s")
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"Failed action '{action_name}' after {duration:.4f}s with error: {str(e)}")
                raise
        return wrapper
    return decorator
