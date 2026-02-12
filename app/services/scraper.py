"""
GitHub API scraper service
"""

import aiohttp
import asyncio
import base64
from typing import Optional, List, Dict, Any
from datetime import datetime

from ..core.config import settings
from ..models.schemas import UserProfile, Repository


class GitHubScraperService:
    """Async GitHub API scraper service"""
    
    def __init__(self, token: Optional[str] = None):
        """
        Initialize the scraper service
        
        Args:
            token: Optional GitHub personal access token
        """
        self.token = token or settings.GITHUB_TOKEN
        self.base_url = settings.GITHUB_API_BASE_URL
        self.headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'GitHub-Scraper-API/1.0'
        }
        
        if self.token:
            self.headers['Authorization'] = f'token {self.token}'
    
    async def _make_request(
        self, 
        session: aiohttp.ClientSession, 
        url: str
    ) -> Optional[Dict[str, Any]]:
        """
        Make async GET request to GitHub API
        
        Args:
            session: aiohttp client session
            url: API endpoint URL
            
        Returns:
            JSON response or None if failed
        """
        try:
            async with session.get(
                url, 
                headers=self.headers,
                timeout=aiohttp.ClientTimeout(total=settings.REQUEST_TIMEOUT)
            ) as response:
                
                # Check rate limit
                remaining = response.headers.get('X-RateLimit-Remaining')
                if remaining and int(remaining) < 10:
                    print(f"⚠️ Warning: Only {remaining} API requests remaining")
                
                if response.status == 200:
                    return await response.json()
                elif response.status == 404:
                    print(f"❌ Resource not found: {url}")
                    return None
                elif response.status == 403:
                    print("❌ Rate limit exceeded or access forbidden")
                    return None
                else:
                    print(f"❌ Error {response.status}: {await response.text()}")
                    return None
                    
        except asyncio.TimeoutError:
            print(f"⏱️ Request timeout: {url}")
            return None
        except Exception as e:
            print(f"❌ Request failed: {str(e)}")
            return None
    
    async def get_user_profile(self, username: str) -> Optional[UserProfile]:
        """
        Fetch GitHub user profile
        
        Args:
            username: GitHub username
            
        Returns:
            UserProfile or None if failed
        """
        url = f"{self.base_url}/users/{username}"
        
        async with aiohttp.ClientSession() as session:
            data = await self._make_request(session, url)
            
            if data:
                try:
                    return UserProfile(**data)
                except Exception as e:
                    print(f"❌ Failed to parse profile: {str(e)}")
                    return None
            
            return None
    
    async def get_user_repos(
        self, 
        username: str, 
        max_repos: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch all public repositories for a user
        
        Args:
            username: GitHub username
            max_repos: Maximum number of repositories to fetch
            
        Returns:
            List of repository data
        """
        repos = []
        page = 1
        per_page = 100
        max_limit = max_repos or settings.DEFAULT_MAX_REPOS
        
        async with aiohttp.ClientSession() as session:
            while True:
                url = f"{self.base_url}/users/{username}/repos?page={page}&per_page={per_page}&sort=updated"
                data = await self._make_request(session, url)
                
                if not data:
                    break
                
                repos.extend(data)
                
                # Check if we've reached the max
                if len(repos) >= max_limit:
                    repos = repos[:max_limit]
                    break
                
                # Check if there are more pages
                if len(data) < per_page:
                    break
                
                page += 1
                await asyncio.sleep(settings.REQUEST_DELAY)
        
        return repos
    
    async def get_readme(
        self, 
        username: str, 
        repo_name: str
    ) -> str:
        """
        Fetch README.md content from a repository
        
        Args:
            username: GitHub username
            repo_name: Repository name
            
        Returns:
            README content or error message
        """
        url = f"{self.base_url}/repos/{username}/{repo_name}/readme"
        
        async with aiohttp.ClientSession() as session:
            data = await self._make_request(session, url)
            
            if not data:
                return "No README found"
            
            content = data.get('content', '')
            
            try:
                # Decode base64 content
                decoded = base64.b64decode(content).decode('utf-8')
                return decoded
            except Exception as e:
                return f"Error decoding README: {str(e)}"
    
    async def get_repos_with_readme(
        self,
        username: str,
        repos: List[Dict[str, Any]],
        truncate_readme: bool = True,
        truncate_length: int = 1000
    ) -> List[Repository]:
        """
        Fetch README files for all repositories concurrently
        
        Args:
            username: GitHub username
            repos: List of repository data
            truncate_readme: Whether to truncate README content
            truncate_length: Maximum length of README content
            
        Returns:
            List of Repository objects with README content
        """
        # Create tasks for fetching READMEs concurrently
        async def fetch_repo_with_readme(repo_data: Dict[str, Any]) -> Repository:
            repo_name = repo_data['name']
            readme_content = await self.get_readme(username, repo_name)
            
            # Truncate if requested
            if truncate_readme and len(readme_content) > truncate_length:
                readme_content = readme_content[:truncate_length] + "..."
            
            # Create Repository object
            repo_data['readme_content'] = readme_content
            repo_data['stargazers_count'] = repo_data.get('stargazers_count', 0)
            repo_data['forks_count'] = repo_data.get('forks_count', 0)
            repo_data['watchers_count'] = repo_data.get('watchers_count', 0)
            repo_data['open_issues_count'] = repo_data.get('open_issues_count', 0)
            repo_data['fork'] = repo_data.get('fork', False)
            
            return Repository(**repo_data)
        
        # Fetch all READMEs concurrently with a semaphore to limit concurrency
        semaphore = asyncio.Semaphore(10)  # Max 10 concurrent requests
        
        async def fetch_with_limit(repo_data):
            async with semaphore:
                return await fetch_repo_with_readme(repo_data)
        
        tasks = [fetch_with_limit(repo) for repo in repos]
        repositories = await asyncio.gather(*tasks)
        
        return repositories
    
    async def scrape_complete(
        self,
        username: str,
        max_repos: Optional[int] = None,
        include_readme: bool = True,
        truncate_readme: bool = True
    ) -> Dict[str, Any]:
        """
        Complete scrape of user profile and repositories
        
        Args:
            username: GitHub username
            max_repos: Maximum repositories to fetch
            include_readme: Whether to include README content
            truncate_readme: Whether to truncate README content
            
        Returns:
            Dictionary with complete scrape results
        """
        # Fetch profile
        profile = await self.get_user_profile(username)
        
        if not profile:
            return {
                'success': False,
                'error': f'User not found: {username}'
            }
        
        # Fetch repositories
        repos_data = await self.get_user_repos(username, max_repos)
        
        # Fetch READMEs if requested
        if include_readme:
            repositories = await self.get_repos_with_readme(
                username,
                repos_data,
                truncate_readme
            )
        else:
            repositories = [Repository(**repo) for repo in repos_data]
        
        # Calculate statistics
        total_stars = sum(repo.stars for repo in repositories)
        total_forks = sum(repo.forks for repo in repositories)
        
        # Top languages
        languages = {}
        for repo in repositories:
            if repo.language:
                languages[repo.language] = languages.get(repo.language, 0) + 1
        
        return {
            'success': True,
            'username': username,
            'profile': profile,
            'repositories': repositories,
            'total_stars': total_stars,
            'total_forks': total_forks,
            'top_languages': dict(sorted(languages.items(), key=lambda x: x[1], reverse=True))
        }
