import logging
import logging.config
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path
import os
import time
from datetime import datetime

# Ensure logs directory exists
LOG_DIR = Path(__file__).resolve().parent.parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Create subdirectories for organized logging
(LOG_DIR / "api").mkdir(exist_ok=True)
(LOG_DIR / "core").mkdir(exist_ok=True)
(LOG_DIR / "session").mkdir(exist_ok=True)
(LOG_DIR / "archive").mkdir(exist_ok=True)

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,

    'formatters': {
        'detailed': {
            'format': '%(asctime)s.%(msecs)03d [%(levelname)8s] [%(name)s] [PID:%(process)d] [Thread:%(threadName)s] %(funcName)s:%(lineno)d - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'standard': {
            'format': '%(asctime)s [%(levelname)8s] %(name)s: %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'simple': {
            'format': '[%(levelname)s] %(name)s: %(message)s'
        },
        'performance': {
            'format': '%(asctime)s.%(msecs)03d [PERF] %(name)s: %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        }
    },

    'handlers': {
        # Console handler with simple formatting
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
            'level': 'INFO',
        },
        
        # Main application log with detailed formatting
        'app_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': str(LOG_DIR / 'app.log'),
            'maxBytes': 10 * 1024 * 1024,  # 10MB
            'backupCount': 10,
            'formatter': 'detailed',
            'mode': 'a',
            'encoding': 'utf-8',
        },
        
        # Error-only log
        'error_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': str(LOG_DIR / 'error.log'),
            'maxBytes': 5 * 1024 * 1024,  # 5MB
            'backupCount': 5,
            'formatter': 'detailed',
            'mode': 'a',
            'level': 'ERROR',
            'encoding': 'utf-8',
        },
        
        # Download monitoring log
        'monitor_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': str(LOG_DIR / 'download_monitor.log'),
            'maxBytes': 10 * 1024 * 1024,  # 10MB
            'backupCount': 7,
            'formatter': 'detailed',
            'mode': 'a',
            'encoding': 'utf-8',
        },
        
        # API-specific log
        'api_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': str(LOG_DIR / 'api' / 'api.log'),
            'maxBytes': 5 * 1024 * 1024,  # 5MB
            'backupCount': 5,
            'formatter': 'detailed',
            'mode': 'a',
            'encoding': 'utf-8',
        },
        
        # Core downloader log
        'core_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': str(LOG_DIR / 'core' / 'audio_core.log'),
            'maxBytes': 10 * 1024 * 1024,  # 10MB
            'backupCount': 7,
            'formatter': 'detailed',
            'mode': 'a',
            'encoding': 'utf-8',
        },
        
        # Session management log
        'session_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': str(LOG_DIR / 'session' / 'session_manager.log'),
            'maxBytes': 5 * 1024 * 1024,  # 5MB
            'backupCount': 5,
            'formatter': 'detailed',
            'mode': 'a',
            'encoding': 'utf-8',
        },
        
        # Daily rotating debug log
        'debug_daily': {
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': str(LOG_DIR / 'debug.log'),
            'when': 'midnight',
            'interval': 1,
            'backupCount': 7,
            'formatter': 'detailed',
            'mode': 'a',
            'encoding': 'utf-8',
        },
        
        # Performance monitoring log
        'performance_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': str(LOG_DIR / 'performance.log'),
            'maxBytes': 5 * 1024 * 1024,  # 5MB
            'backupCount': 3,
            'formatter': 'performance',
            'mode': 'a',
            'encoding': 'utf-8',
        },
    },
    
    'loggers': {
        # Download monitoring
        'download_monitor': {
            'handlers': ['console', 'monitor_file'],
            'level': 'INFO',
            'propagate': False,
        },
        
        # API loggers
        'api': {
            'handlers': ['console', 'api_file', 'error_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'api.main': {
            'handlers': ['api_file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'api.sessions': {
            'handlers': ['api_file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'api.jobs': {
            'handlers': ['api_file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'api.health': {
            'handlers': ['api_file'],
            'level': 'INFO',
            'propagate': True,
        },
        
        # Core audio downloader
        'audio_core': {
            'handlers': ['console', 'core_file', 'error_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'audio_cli': {
            'handlers': ['console', 'core_file'],
            'level': 'INFO',
            'propagate': False,
        },
        
        # Session management
        'session_manager': {
            'handlers': ['console', 'session_file', 'error_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'user_context': {
            'handlers': ['session_file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        
        # Common utilities
        'url_utils': {
            'handlers': ['core_file'],
            'level': 'INFO',
            'propagate': True,
        },
        'uuid_utils': {
            'handlers': ['session_file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'app_config': {
            'handlers': ['app_file'],
            'level': 'INFO',
            'propagate': True,
        },
        
        # Performance monitoring
        'performance': {
            'handlers': ['performance_file'],
            'level': 'INFO',
            'propagate': False,
        },
        
        # Third-party libraries (reduce noise)
        'yt_dlp': {
            'handlers': ['core_file'],
            'level': 'WARNING',
            'propagate': False,
        },
        'urllib3': {
            'handlers': ['error_file'],
            'level': 'WARNING',
            'propagate': False,
        },
        'requests': {
            'handlers': ['error_file'],
            'level': 'WARNING',
            'propagate': False,
        },
        'httpx': {
            'handlers': ['api_file'],
            'level': 'WARNING',
            'propagate': False,
        },
    },

    'root': {
        'handlers': ['console', 'app_file', 'error_file'],
        'level': 'INFO',
    },
}

def setup_logging(debug_mode: bool = False):
    """
    Setup logging configuration.
    
    Args:
        debug_mode: If True, enables debug logging and adds debug handler
    """
    # Adjust log levels for debug mode
    if debug_mode:
        LOGGING_CONFIG['root']['level'] = 'DEBUG'
        LOGGING_CONFIG['loggers']['audio_core']['level'] = 'DEBUG'
        LOGGING_CONFIG['loggers']['session_manager']['level'] = 'DEBUG'
        LOGGING_CONFIG['loggers']['api']['level'] = 'DEBUG'
        
        # Add debug handler to root logger if not already present
        if 'debug_daily' not in LOGGING_CONFIG['root']['handlers']:
            LOGGING_CONFIG['root']['handlers'].append('debug_daily')
    
    logging.config.dictConfig(LOGGING_CONFIG)
    
    # Log the startup message
    logger = logging.getLogger('app_config')
    logger.info(f"Logging initialized. Debug mode: {debug_mode}")
    logger.info(f"Log directory: {LOG_DIR}")


def get_logger(name: str, level: str = None) -> logging.Logger:
    """
    Get a configured logger for a specific module.
    
    Args:
        name: Logger name (usually module name)
        level: Optional log level override
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    if level:
        logger.setLevel(getattr(logging, level.upper()))
    return logger


def get_performance_logger() -> logging.Logger:
    """Get the performance monitoring logger."""
    return logging.getLogger('performance')


def cleanup_old_logs(days_to_keep: int = 30):
    """
    Clean up old log files beyond the rotation limit.
    
    Args:
        days_to_keep: Number of days of logs to keep
    """
    import glob
    import time
    
    logger = logging.getLogger('app_config')
    cutoff_time = time.time() - (days_to_keep * 24 * 60 * 60)
    
    # Find all log files
    log_patterns = [
        str(LOG_DIR / "*.log*"),
        str(LOG_DIR / "*" / "*.log*"),
        str(LOG_DIR / "archive" / "*.log*")
    ]
    
    files_removed = 0
    for pattern in log_patterns:
        for log_file in glob.glob(pattern):
            log_path = Path(log_file)
            if log_path.is_file() and log_path.stat().st_mtime < cutoff_time:
                try:
                    # Move to archive instead of deleting
                    archive_path = LOG_DIR / "archive" / f"{log_path.name}.{int(time.time())}"
                    log_path.rename(archive_path)
                    files_removed += 1
                    logger.debug(f"Archived old log file: {log_file}")
                except OSError as e:
                    logger.warning(f"Could not archive log file {log_file}: {e}")
    
    if files_removed > 0:
        logger.info(f"Archived {files_removed} old log files")


def log_system_info():
    """Log system information for debugging purposes."""
    import platform
    import psutil
    import sys
    
    logger = logging.getLogger('app_config')
    
    logger.info("=== System Information ===")
    logger.info(f"Platform: {platform.platform()}")
    logger.info(f"Python: {sys.version}")
    logger.info(f"CPU Count: {psutil.cpu_count()}")
    logger.info(f"Memory: {psutil.virtual_memory().total / (1024**3):.1f} GB")
    logger.info(f"Disk Free: {psutil.disk_usage('.').free / (1024**3):.1f} GB")
    logger.info("=== End System Information ===")


def configure_development_logging():
    """Configure logging for development environment."""
    setup_logging(debug_mode=True)
    log_system_info()


def configure_production_logging():
    """Configure logging for production environment."""
    setup_logging(debug_mode=False)
    
    # Perform log cleanup on startup
    cleanup_old_logs(days_to_keep=30)
    
    logger = logging.getLogger('app_config')
    logger.info("Production logging configured")


def log_performance_metric(operation: str, duration: float, **kwargs):
    """
    Log a performance metric.
    
    Args:
        operation: Name of the operation
        duration: Time taken in seconds
        **kwargs: Additional metric data
    """
    perf_logger = get_performance_logger()
    metric_data = {
        'operation': operation,
        'duration_seconds': duration,
        **kwargs
    }
    perf_logger.info(f"METRIC: {metric_data}")


# Context manager for performance logging
class LogPerformance:
    """Context manager for automatic performance logging."""
    
    def __init__(self, operation: str, logger_name: str = 'performance', **kwargs):
        self.operation = operation
        self.logger = logging.getLogger(logger_name)
        self.kwargs = kwargs
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        self.logger.debug(f"Starting operation: {self.operation}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        if exc_type is None:
            log_performance_metric(self.operation, duration, **self.kwargs)
            self.logger.debug(f"Completed operation: {self.operation} in {duration:.3f}s")
        else:
            self.logger.error(f"Failed operation: {self.operation} after {duration:.3f}s: {exc_val}")


# Convenience function to get the standard datetime timestamp
def get_log_timestamp() -> str:
    """Get standardized timestamp for logging."""
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]