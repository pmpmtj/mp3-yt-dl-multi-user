"""
Main entry point for the audio download module.

This module allows running the audio downloader as a Python module:
python -m src.yt_audio_dl [args]
"""

from .audio_core_cli import main

if __name__ == "__main__":
    main()
