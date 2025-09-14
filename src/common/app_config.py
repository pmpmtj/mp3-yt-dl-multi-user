"""
Application configuration module.

This module contains all application configuration settings in Python format,
replacing the previous JSON-based configuration system.
"""

import logging
from typing import Dict, Any

# Initialize logger for this module
logger = logging.getLogger("app_config")

# Application configuration for video downloader
APP_CONFIG = {
    "download": {
        "download_path": "./downloads"
    },
    "video": {
        "ext": "mp4",
        "quality": "best", 
        "output_template": "%(title)s.%(ext)s",
        "restrict_filenames": True
    },
    "features": {
        "use_database_as_source": False,
        "enable_file_existence_check": True,
        "enable_metadata_caching": False,
        "enable_download_history": False
    }
}

def get_config() -> Dict[str, Any]:
    """
    Get the application configuration.
    
    Returns:
        Configuration dictionary
    """
    logger.debug("Retrieving application configuration")
    config = APP_CONFIG.copy()
    logger.debug(f"Configuration loaded: {len(config)} top-level sections")
    return config

def get_download_config() -> Dict[str, Any]:
    """
    Get download-specific configuration.
    
    Returns:
        Download configuration dictionary
    """
    logger.debug("Retrieving download configuration")
    config = APP_CONFIG["download"].copy()
    logger.debug(f"Download path: {config.get('download_path', 'default')}")
    return config

def get_video_config() -> Dict[str, Any]:
    """
    Get video-specific configuration.
    
    Returns:
        Video configuration dictionary
    """
    logger.debug("Retrieving video configuration")
    config = APP_CONFIG["video"].copy()
    logger.debug(f"Video settings: ext={config.get('ext')}, quality={config.get('quality')}")
    return config

def get_download_path() -> str:
    """
    Get the download path from configuration.
    
    Returns:
        Download path string
    """
    logger.debug("Retrieving download path from configuration")
    path = APP_CONFIG["download"]["download_path"]
    logger.debug(f"Download path: {path}")
    return path

def get_video_settings() -> Dict[str, Any]:
    """
    Get video settings from configuration.
    
    Returns:
        Video settings dictionary
    """
    logger.debug("Retrieving video settings from configuration")
    settings = {
        'ext': APP_CONFIG["video"]['ext'],
        'quality': APP_CONFIG["video"]['quality'],
        'output_template': APP_CONFIG["video"]['output_template'],
        'restrict_filenames': APP_CONFIG["video"]['restrict_filenames']
    }
    logger.debug(f"Video settings: {settings}")
    return settings

def get_feature_flags() -> Dict[str, Any]:
    """
    Get feature flags configuration.
    
    Returns:
        Feature flags dictionary
    """
    logger.debug("Retrieving feature flags configuration")
    flags = APP_CONFIG["features"].copy()
    logger.debug(f"Feature flags: {flags}")
    return flags

def is_database_source_enabled() -> bool:
    """
    Check if database is configured as the single source of truth.
    
    Returns:
        True if database should be used as source of truth, False otherwise
    """
    enabled = APP_CONFIG["features"]["use_database_as_source"]
    logger.debug(f"Database source enabled: {enabled}")
    return enabled

def is_file_check_enabled() -> bool:
    """
    Check if file existence check should be performed.
    
    Returns:
        True if file existence check should be performed, False otherwise
    """
    enabled = APP_CONFIG["features"]["enable_file_existence_check"]
    logger.debug(f"File existence check enabled: {enabled}")
    return enabled

def is_metadata_caching_enabled() -> bool:
    """
    Check if metadata caching is enabled.
    
    Returns:
        True if metadata caching is enabled, False otherwise
    """
    enabled = APP_CONFIG["features"]["enable_metadata_caching"]
    logger.debug(f"Metadata caching enabled: {enabled}")
    return enabled

def is_download_history_enabled() -> bool:
    """
    Check if download history tracking is enabled.
    
    Returns:
        True if download history is enabled, False otherwise
    """
    enabled = APP_CONFIG["features"]["enable_download_history"]
    logger.debug(f"Download history enabled: {enabled}")
    return enabled
