"""
Example usage of the GitHub Scraper API
"""

import requests
import time
import json

BASE_URL = "http://localhost:8000"


def example_1_sync_scraping():
    """Example 1: Synchronous scraping"""
    print("\n" + "="*60)
    print("Example 1: Synchronous Profile Scraping")
    print("="*60)
    
    # Scrape profile
    response = requests.get(f"{BASE_URL}/api/v1/scrape/profile/octocat")
    data = response.json()
    
    print(f"\nUser: {data['profile']['name']}")
    print(f"Username: {data['profile']['login']}")
    print(f"Followers: {data['profile']['followers']}")
    print(f"Public Repos: {data['profile']['public_repos']}")
    print(f"Cached: {data['cached']}")


def example_2_scrape_repos():
    """Example 2: Scrape repositories"""
    print("\n" + "="*60)
    print("Example 2: Scrape Repositories")
    print("="*60)
    
    # Scrape repositories
    response = requests.get(
        f"{BASE_URL}/api/v1/scrape/repositories/octocat",
        params={'max_repos': 5, 'include_readme': True}
    )
    data = response.json()
    
    print(f"\nFound {data['total_repos']} repositories")
    print("\nTop repositories:")
    for repo in data['repositories'][:5]:
        print(f"  • {repo['name']}: {repo['stars']} ⭐ ({repo['language']})")


def example_3_complete_scrape():
    """Example 3: Complete scrape with statistics"""
    print("\n" + "="*60)
    print("Example 3: Complete Scrape")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/api/v1/scrape/complete/octocat")
    data = response.json()
    
    print(f"\nUser: {data['username']}")
    print(f"Total Stars: {data['total_stars']}")
    print(f"Total Forks: {data['total_forks']}")
    print(f"\nTop Languages:")
    for lang, count in list(data['top_languages'].items())[:5]:
        print(f"  • {lang}: {count} repos")


def example_4_async_scraping():
    """Example 4: Async scraping with background job"""
    print("\n" + "="*60)
    print("Example 4: Async Scraping (Background Job)")
    print("="*60)
    
    # Start async job
    print("\nStarting async scrape job...")
    response = requests.post(
        f"{BASE_URL}/api/v1/scrape/async/torvalds",
        json={
            'username': 'torvalds',
            'max_repos': 20,
            'include_readme': True,
            'export_format': 'excel'
        }
    )
    
    job = response.json()
    job_id = job['job_id']
    print(f"Job ID: {job_id}")
    print(f"Status: {job['status']}")
    
    # Poll for completion
    print("\nWaiting for job to complete...")
    while True:
        status_response = requests.get(f"{BASE_URL}/api/v1/jobs/{job_id}")
        status = status_response.json()
        
        print(f"Progress: {status['progress']}% - Status: {status['status']}")
        
        if status['status'] in ['completed', 'failed']:
            break
        
        time.sleep(2)
    
    if status['status'] == 'completed':
        print("\n✓ Job completed successfully!")
        print(f"Export files: {status['export_files']}")
        
        # Download the file
        if status['export_files']:
            filename = status['export_files'][0].split('/')[-1]
            download_url = f"{BASE_URL}/api/v1/download/{job_id}/{filename}"
            
            print(f"\nDownloading: {filename}")
            file_response = requests.get(download_url)
            
            with open(filename, 'wb') as f:
                f.write(file_response.content)
            
            print(f"✓ Downloaded to: {filename}")
    else:
        print(f"\n✗ Job failed: {status.get('error')}")


def example_5_job_management():
    """Example 5: Job management"""
    print("\n" + "="*60)
    print("Example 5: Job Management")
    print("="*60)
    
    # List all jobs
    response = requests.get(f"{BASE_URL}/api/v1/jobs")
    jobs = response.json()
    
    print(f"\nTotal jobs: {len(jobs)}")
    
    if jobs:
        print("\nRecent jobs:")
        for job in jobs[:5]:
            print(f"  • {job['job_id'][:8]}... - {job['username']} - {job['status']}")


def example_6_export_formats():
    """Example 6: Different export formats"""
    print("\n" + "="*60)
    print("Example 6: Export Formats")
    print("="*60)
    
    # Start job with JSON export
    response = requests.post(
        f"{BASE_URL}/api/v1/scrape/async/octocat",
        json={
            'username': 'octocat',
            'max_repos': 5,
            'export_format': 'json'
        }
    )
    
    job_id = response.json()['job_id']
    
    # Wait for completion
    while True:
        status = requests.get(f"{BASE_URL}/api/v1/jobs/{job_id}").json()
        if status['status'] in ['completed', 'failed']:
            break
        time.sleep(1)
    
    if status['status'] == 'completed':
        # Export to different formats
        for fmt in ['excel', 'csv', 'json']:
            export_response = requests.get(
                f"{BASE_URL}/api/v1/export/{job_id}/{fmt}"
            )
            export_data = export_response.json()
            
            print(f"\n{fmt.upper()} export:")
            print(f"  File: {export_data.get('file_path')}")
            print(f"  Size: {export_data.get('file_size')} bytes")


def example_7_caching():
    """Example 7: Cache demonstration"""
    print("\n" + "="*60)
    print("Example 7: Caching")
    print("="*60)
    
    username = "octocat"
    
    # First request (not cached)
    print("\nFirst request (no cache)...")
    start = time.time()
    response1 = requests.get(f"{BASE_URL}/api/v1/scrape/profile/{username}")
    time1 = time.time() - start
    data1 = response1.json()
    
    print(f"Time: {time1:.2f}s")
    print(f"Cached: {data1['cached']}")
    
    # Second request (cached)
    print("\nSecond request (should be cached)...")
    start = time.time()
    response2 = requests.get(f"{BASE_URL}/api/v1/scrape/profile/{username}")
    time2 = time.time() - start
    data2 = response2.json()
    
    print(f"Time: {time2:.2f}s")
    print(f"Cached: {data2['cached']}")
    print(f"Speed improvement: {time1/time2:.1f}x faster")


def example_8_health_check():
    """Example 8: Health check and stats"""
    print("\n" + "="*60)
    print("Example 8: Health Check & Stats")
    print("="*60)
    
    # Health check
    health = requests.get(f"{BASE_URL}/health").json()
    print("\nHealth Check:")
    print(f"  Status: {health['status']}")
    print(f"  Cache Size: {health['cache_size']}")
    print(f"  Active Jobs: {health['active_jobs']}")
    
    # API stats
    stats = requests.get(f"{BASE_URL}/api/v1/stats").json()
    print("\nAPI Statistics:")
    print(f"  Total Jobs: {stats['total_jobs']}")
    print(f"  Completed: {stats['completed_jobs']}")
    print(f"  Failed: {stats['failed_jobs']}")
    print(f"  Running: {stats['running_jobs']}")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("GitHub Scraper API - Usage Examples")
    print("="*60)
    print("\nMake sure the API is running at http://localhost:8000")
    print("Start it with: python -m app.main or ./run.sh")
    
    input("\nPress Enter to continue...")
    
    try:
        # Check if API is running
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print("\n❌ API is not responding correctly!")
            exit(1)
        
        # Run examples
        example_1_sync_scraping()
        example_2_scrape_repos()
        example_3_complete_scrape()
        example_5_job_management()
        example_7_caching()
        example_8_health_check()
        
        # Long-running examples (optional)
        print("\n" + "="*60)
        print("Long-running examples (may take a few minutes)")
        response = input("Run async examples? (y/n): ")
        
        if response.lower() == 'y':
            example_4_async_scraping()
            example_6_export_formats()
        
        print("\n" + "="*60)
        print("All examples completed!")
        print("="*60)
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Cannot connect to API!")
        print("Make sure the API is running at http://localhost:8000")
        print("Start it with: ./run.sh or python -m app.main")
    except KeyboardInterrupt:
        print("\n\n⚠️  Examples interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
