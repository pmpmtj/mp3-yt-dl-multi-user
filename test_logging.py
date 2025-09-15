#!/usr/bin/env python3
"""
Test script to demonstrate the enhanced logging functionality.
"""

import sys
from pathlib import Path

# Add project to path for testing
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from src.common import (
    configure_development_logging, 
    get_logger, 
    get_performance_logger,
    LogPerformance,
    log_performance_metric
)
import time

def test_enhanced_logging():
    """Test the enhanced logging configuration."""
    
    # Setup development logging
    configure_development_logging()
    
    # Test different loggers
    app_logger = get_logger('audio_core')
    api_logger = get_logger('api.main')
    session_logger = get_logger('session_manager')
    perf_logger = get_performance_logger()
    
    # Test basic logging
    app_logger.info("Audio core module initialized")
    app_logger.debug("Debug message from audio core")
    
    api_logger.info("API endpoint called")
    api_logger.warning("API warning message")
    
    session_logger.info("Session created successfully")
    session_logger.debug("Session debug information")
    
    # Test performance logging
    log_performance_metric("test_operation", 1.23, bytes_processed=1024, success=True)
    
    # Test performance context manager
    with LogPerformance("context_operation", component="test") as perf:
        time.sleep(0.1)  # Simulate work
    
    # Test error logging
    try:
        raise ValueError("Test error for logging")
    except Exception as e:
        app_logger.error(f"Caught exception: {e}", exc_info=True)
    
    print("✅ Enhanced logging test completed!")
    print("📁 Check the logs directory for organized log files:")
    print("   - logs/app.log (main application log)")
    print("   - logs/error.log (errors only)")
    print("   - logs/debug.log (daily rotating debug)")
    print("   - logs/performance.log (performance metrics)")
    print("   - logs/api/api.log (API-specific logs)")
    print("   - logs/core/audio_core.log (core module logs)")
    print("   - logs/session/session_manager.log (session logs)")

if __name__ == "__main__":
    test_enhanced_logging()
