#!/usr/bin/env python3
import requests
import json

# Test the API directly
try:
    response = requests.post(
        'http://localhost:8000/api/auto-download/',
        json={'url': 'https://www.youtube.com/watch?v=XNNjYas8Xo8'},
        timeout=30
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    print(f"Response Text: {response.text}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Success: {data.get('success')}")
        if data.get('success'):
            print(f"Download URL: {data.get('download_url')}")
        else:
            print(f"Error: {data.get('error')}")
    else:
        print(f"HTTP Error: {response.status_code}")
        
except Exception as e:
    print(f"Exception: {e}")
    import traceback
    traceback.print_exc()
