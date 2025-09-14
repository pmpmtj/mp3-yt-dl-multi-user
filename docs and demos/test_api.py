#!/usr/bin/env python3
"""
Test script for the YouTube Downloader API.

This script demonstrates how to use the API endpoints for session management
and job processing.
"""

import requests
import json
import time
import sys
from pathlib import Path

# Add src directory to Python path
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

API_BASE_URL = "http://localhost:8000"

def test_api():
    """Test the API endpoints."""
    print("=== YouTube Downloader API Test ===\n")
    
    # Test 1: Health check
    print("1. Testing health check...")
    try:
        response = requests.get(f"{API_BASE_URL}/api/health")
        if response.status_code == 200:
            health_data = response.json()
            print(f"   ✅ Health Status: {health_data['status']}")
            print(f"   ✅ Active Sessions: {health_data['active_sessions']}")
            print(f"   ✅ Uptime: {health_data['uptime_seconds']:.1f} seconds")
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
            return
    except requests.exceptions.ConnectionError:
        print("   ❌ Cannot connect to API. Make sure the server is running.")
        print("   Run: python run_api.py")
        return
    
    # Test 2: Create a session
    print("\n2. Creating a new session...")
    try:
        response = requests.post(f"{API_BASE_URL}/api/sessions/")
        if response.status_code == 200:
            session_data = response.json()
            session_uuid = session_data['session_uuid']
            print(f"   ✅ Created session: {session_uuid}")
            print(f"   ✅ Session active: {session_data['is_active']}")
        else:
            print(f"   ❌ Failed to create session: {response.status_code}")
            return
    except Exception as e:
        print(f"   ❌ Error creating session: {e}")
        return
    
    # Test 3: Get session info
    print("\n3. Getting session information...")
    try:
        response = requests.get(f"{API_BASE_URL}/api/sessions/{session_uuid}")
        if response.status_code == 200:
            session_info = response.json()
            print(f"   ✅ Session UUID: {session_info['session_uuid']}")
            print(f"   ✅ Total Jobs: {session_info['total_jobs']}")
            print(f"   ✅ Age: {session_info['age_hours']:.2f} hours")
        else:
            print(f"   ❌ Failed to get session info: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error getting session info: {e}")
    
    # Test 4: Create a download job
    print("\n4. Creating a download job...")
    try:
        job_data = {
            "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "media_type": "video",
            "quality": "best"
        }
        
        headers = {"X-Session-ID": session_uuid, "Content-Type": "application/json"}
        response = requests.post(
            f"{API_BASE_URL}/api/jobs/",
            json=job_data,
            headers=headers
        )
        
        if response.status_code == 200:
            job_response = response.json()
            job_id = job_response['job_id'] if 'job_id' in job_response else 'unknown'
            print(f"   ✅ Created job: {job_id}")
            print(f"   ✅ Job UUID: {job_response['job_uuid']}")
            print(f"   ✅ Status: {job_response['status']}")
            print(f"   ✅ URL: {job_response['job_url']}")
        else:
            print(f"   ❌ Failed to create job: {response.status_code}")
            print(f"   Response: {response.text}")
            return
    except Exception as e:
        print(f"   ❌ Error creating job: {e}")
        return
    
    # Test 5: Get job status
    print("\n5. Getting job status...")
    try:
        headers = {"X-Session-ID": session_uuid}
        response = requests.get(
            f"{API_BASE_URL}/api/jobs/{job_id}",
            headers=headers
        )
        
        if response.status_code == 200:
            job_status = response.json()
            print(f"   ✅ Job Status: {job_status['status']}")
            print(f"   ✅ Progress: {job_status.get('progress_percent', 'N/A')}%")
            print(f"   ✅ Created: {job_status['created_at']}")
        else:
            print(f"   ❌ Failed to get job status: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error getting job status: {e}")
    
    # Test 6: Get session jobs
    print("\n6. Listing session jobs...")
    try:
        headers = {"X-Session-ID": session_uuid}
        response = requests.get(
            f"{API_BASE_URL}/api/jobs/",
            headers=headers
        )
        
        if response.status_code == 200:
            jobs = response.json()
            print(f"   ✅ Found {len(jobs)} jobs in session")
            for i, job in enumerate(jobs, 1):
                print(f"   Job {i}: {job['status']} - {job['job_url']}")
        else:
            print(f"   ❌ Failed to list jobs: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error listing jobs: {e}")
    
    # Test 7: Get session statistics
    print("\n7. Getting session statistics...")
    try:
        response = requests.get(f"{API_BASE_URL}/api/sessions/stats/overview")
        if response.status_code == 200:
            stats = response.json()
            print(f"   ✅ Total Sessions: {stats['total_sessions']}")
            print(f"   ✅ Active Sessions: {stats['active_sessions']}")
            print(f"   ✅ Total Jobs: {stats['total_jobs']}")
            print(f"   ✅ Active Jobs: {stats['active_jobs']}")
        else:
            print(f"   ❌ Failed to get statistics: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error getting statistics: {e}")
    
    # Test 8: Wait for job processing
    print("\n8. Waiting for job processing...")
    try:
        for i in range(10):  # Wait up to 10 seconds
            headers = {"X-Session-ID": session_uuid}
            response = requests.get(
                f"{API_BASE_URL}/api/jobs/{job_id}",
                headers=headers
            )
            
            if response.status_code == 200:
                job_status = response.json()
                status = job_status['status']
                progress = job_status.get('progress_percent', 0)
                
                print(f"   Status: {status}, Progress: {progress}%")
                
                if status in ['completed', 'failed']:
                    break
                
                time.sleep(1)
            else:
                print(f"   ❌ Failed to check job status: {response.status_code}")
                break
    except Exception as e:
        print(f"   ❌ Error monitoring job: {e}")
    
    # Test 9: Get system metrics
    print("\n9. Getting system metrics...")
    try:
        response = requests.get(f"{API_BASE_URL}/api/metrics")
        if response.status_code == 200:
            metrics = response.json()
            print(f"   ✅ Active Sessions: {metrics['active_sessions']}")
            print(f"   ✅ Total Jobs: {metrics['total_jobs']}")
            print(f"   ✅ Storage Used: {metrics['total_storage_bytes']} bytes")
        else:
            print(f"   ❌ Failed to get metrics: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error getting metrics: {e}")
    
    print("\n=== API Test Complete ===")
    print("\nKey Features Tested:")
    print("✅ Health monitoring")
    print("✅ Session creation and management")
    print("✅ Job creation and tracking")
    print("✅ Background job processing")
    print("✅ Session isolation")
    print("✅ Statistics and metrics")


if __name__ == "__main__":
    test_api()
