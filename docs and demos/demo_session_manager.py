"""
Demo script for the Session Manager functionality.

This demonstrates how to use the session manager for handling multiple concurrent users
in the YouTube downloader application.
"""

import sys
import time
from pathlib import Path

# Add the src directory to the path so we can import our modules
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from src.common import (
    setup_logging, 
    get_session_manager, 
    create_session, 
    get_session,
    generate_job_uuid
)

def main():
    """Demo the session manager functionality."""
    print("=== Session Manager Demo ===\n")
    
    # Setup logging
    setup_logging()
    
    # Get the global session manager
    session_manager = get_session_manager()
    
    print("1. Creating multiple user sessions...")
    
    # Create several user sessions
    session1 = create_session()
    session2 = create_session()
    session3 = create_session()
    
    print(f"   Created sessions: {session1}, {session2}, {session3}")
    
    print("\n2. Getting user contexts for each session...")
    
    # Get user contexts
    user1 = get_session(session1)
    user2 = get_session(session2)
    user3 = get_session(session3)
    
    if user1 and user2 and user3:
        print(f"   Retrieved contexts for all sessions")
        print(f"   User1 session ID: {user1.get_session_id()}")
        print(f"   User2 session ID: {user2.get_session_id()}")
        print(f"   User3 session ID: {user3.get_session_id()}")
    
    print("\n3. Creating job UUIDs for different URLs...")
    
    # Simulate different YouTube URLs for each user
    youtube_urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # User 1
        "https://www.youtube.com/watch?v=9bZkp7q19f0",  # User 2
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # User 3 (same as User 1)
    ]
    
    for i, (user_context, url) in enumerate(zip([user1, user2, user3], youtube_urls), 1):
        if user_context:
            job_uuid = user_context.get_url_uuid(url)
            print(f"   User{i} - URL: {url}")
            print(f"   User{i} - Job UUID: {job_uuid}")
            
            # Get download paths for different media types
            audio_path = user_context.get_audio_download_path(url)
            video_path = user_context.get_video_download_path(url)
            transcript_path = user_context.get_transcript_download_path(url)
            
            print(f"   User{i} - Audio path: {audio_path}")
            print(f"   User{i} - Video path: {video_path}")
            print(f"   User{i} - Transcript path: {transcript_path}")
            print()
    
    print("4. Testing session isolation...")
    
    # Test that each user gets different job UUIDs even for the same URL
    if user1 and user3:
        job1_uuid = user1.get_url_uuid(youtube_urls[0])
        job3_uuid = user3.get_url_uuid(youtube_urls[2])
        
        print(f"   User1 job UUID for URL: {job1_uuid}")
        print(f"   User3 job UUID for same URL: {job3_uuid}")
        print(f"   UUIDs are different (isolated): {job1_uuid != job3_uuid}")
    
    print("\n5. Simulating job lifecycle...")
    
    # Start jobs for each session
    for i, session_id in enumerate([session1, session2, session3], 1):
        success = session_manager.start_job(session_id)
        print(f"   Started job for User{i}: {success}")
    
    # Simulate some jobs completing and failing
    time.sleep(0.1)  # Small delay to simulate processing
    
    session_manager.complete_job(session1, storage_bytes=1024*1024)  # 1MB
    session_manager.complete_job(session2, storage_bytes=512*1024)   # 512KB
    session_manager.fail_job(session3)
    
    print("   Completed jobs for User1 and User2, failed job for User3")
    
    print("\n6. Getting session statistics...")
    
    # Get overall statistics
    stats = session_manager.get_session_stats()
    print(f"   Total sessions: {stats['total_sessions']}")
    print(f"   Active sessions: {stats['active_sessions']}")
    print(f"   Total jobs: {stats['total_jobs']}")
    print(f"   Active jobs: {stats['active_jobs']}")
    print(f"   Total storage used: {stats['total_storage_bytes']} bytes")
    
    print("\n7. Getting detailed session info...")
    
    # Get detailed info for each session
    for i, session_id in enumerate([session1, session2, session3], 1):
        info = session_manager.get_session_info(session_id)
        if info:
            print(f"   User{i} Session Info:")
            print(f"     - Session UUID: {info['session_uuid']}")
            print(f"     - Active: {info['is_active']}")
            print(f"     - Total jobs: {info['total_jobs']}")
            print(f"     - Completed jobs: {info['completed_jobs']}")
            print(f"     - Failed jobs: {info['failed_jobs']}")
            print(f"     - Storage used: {info['storage_used_bytes']} bytes")
            print(f"     - Age: {info['age_hours']:.2f} hours")
    
    print("\n8. Testing session cleanup...")
    
    # Deactivate one session
    session_manager.deactivate_session(session2)
    print("   Deactivated User2's session")
    
    # Get updated statistics
    stats_after = session_manager.get_session_stats()
    print(f"   Active sessions after deactivation: {stats_after['active_sessions']}")
    
    # Test cleanup of expired sessions
    cleaned = session_manager.cleanup_expired_sessions()
    print(f"   Cleaned up {cleaned} expired sessions")
    
    print("\n9. Testing concurrent access simulation...")
    
    # Simulate multiple threads accessing the session manager
    import threading
    
    def worker_thread(session_id, worker_id):
        """Worker thread that accesses session manager."""
        user_context = get_session(session_id)
        if user_context:
            # Simulate some work
            time.sleep(0.05)
            session_manager.start_job(session_id)
            time.sleep(0.05)
            session_manager.complete_job(session_id, storage_bytes=256*1024)
    
    # Create multiple threads
    threads = []
    for i in range(3):
        thread = threading.Thread(target=worker_thread, args=(session1, i))
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    print("   Completed concurrent access simulation")
    
    # Final statistics
    final_stats = session_manager.get_session_stats()
    print(f"   Final active jobs: {final_stats['active_jobs']}")
    print(f"   Final total storage: {final_stats['total_storage_bytes']} bytes")
    
    print("\n=== Demo Complete ===")
    print("\nKey Features Demonstrated:")
    print("✓ Session creation and management")
    print("✓ User context isolation")
    print("✓ Job UUID generation per URL")
    print("✓ Hierarchical download path structure")
    print("✓ Job lifecycle tracking")
    print("✓ Session statistics and monitoring")
    print("✓ Thread-safe concurrent access")
    print("✓ Session cleanup and expiration")


if __name__ == "__main__":
    main()
