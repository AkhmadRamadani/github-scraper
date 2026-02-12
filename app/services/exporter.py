"""
Export service for creating files
"""

import pandas as pd
from pathlib import Path
from typing import Dict, Any, List
import json

from ..core.config import settings


class ExportService:
    """Service for exporting scraped data to various formats"""
    
    def __init__(self):
        self.output_dir = settings.OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def _create_profile_df(self, profile_data: Dict[str, Any]) -> pd.DataFrame:
        """Create DataFrame from profile data"""
        return pd.DataFrame([{
            'Username': profile_data.get('login', ''),
            'Name': profile_data.get('name', ''),
            'Bio': profile_data.get('bio', ''),
            'Company': profile_data.get('company', ''),
            'Location': profile_data.get('location', ''),
            'Email': profile_data.get('email', ''),
            'Blog': profile_data.get('blog', ''),
            'Twitter': profile_data.get('twitter_username', ''),
            'Public Repos': profile_data.get('public_repos', 0),
            'Public Gists': profile_data.get('public_gists', 0),
            'Followers': profile_data.get('followers', 0),
            'Following': profile_data.get('following', 0),
            'Created At': profile_data.get('created_at', ''),
            'Updated At': profile_data.get('updated_at', ''),
            'Profile URL': profile_data.get('html_url', '')
        }])
    
    def _create_repos_df(self, repos_data: List[Dict[str, Any]]) -> pd.DataFrame:
        """Create DataFrame from repositories data"""
        rows = []
        for repo in repos_data:
            rows.append({
                'Repository Name': repo.get('name', ''),
                'Description': repo.get('description', ''),
                'URL': repo.get('html_url', ''),
                'Stars': repo.get('stars', 0),
                'Forks': repo.get('forks', 0),
                'Watchers': repo.get('watchers', 0),
                'Language': repo.get('language', 'N/A'),
                'Open Issues': repo.get('open_issues', 0),
                'Created At': repo.get('created_at', ''),
                'Updated At': repo.get('updated_at', ''),
                'Size (KB)': repo.get('size', 0),
                'Default Branch': repo.get('default_branch', 'main'),
                'Is Fork': repo.get('is_fork', False),
                'README Content': repo.get('readme_content', '')
            })
        
        return pd.DataFrame(rows)
    
    async def export_to_excel(
        self,
        job_id: str,
        data: Dict[str, Any]
    ) -> Path:
        """
        Export data to Excel format
        
        Args:
            job_id: Job ID for filename
            data: Scrape data containing profile and repositories
            
        Returns:
            Path to exported file
        """
        username = data.get('username', 'unknown')
        output_file = self.output_dir / f"{job_id}_{username}_data.xlsx"
        
        # Create DataFrames
        profile_df = self._create_profile_df(data.get('profile', {}))
        repos_data = [repo.dict() if hasattr(repo, 'dict') else repo 
                     for repo in data.get('repositories', [])]
        repos_df = self._create_repos_df(repos_data)
        
        # Write to Excel
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            profile_df.to_excel(writer, sheet_name='Profile', index=False)
            repos_df.to_excel(writer, sheet_name='Repositories', index=False)
            
            # Auto-adjust column widths
            for sheet_name in writer.sheets:
                worksheet = writer.sheets[sheet_name]
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(cell.value)
                        except:
                            pass
                    
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width
        
        return output_file
    
    async def export_to_csv(
        self,
        job_id: str,
        data: Dict[str, Any]
    ) -> List[Path]:
        """
        Export data to CSV format
        
        Args:
            job_id: Job ID for filename
            data: Scrape data containing profile and repositories
            
        Returns:
            List of paths to exported files
        """
        username = data.get('username', 'unknown')
        
        profile_file = self.output_dir / f"{job_id}_{username}_profile.csv"
        repos_file = self.output_dir / f"{job_id}_{username}_repositories.csv"
        
        # Create DataFrames
        profile_df = self._create_profile_df(data.get('profile', {}))
        repos_data = [repo.dict() if hasattr(repo, 'dict') else repo 
                     for repo in data.get('repositories', [])]
        repos_df = self._create_repos_df(repos_data)
        
        # Write to CSV
        profile_df.to_csv(profile_file, index=False)
        repos_df.to_csv(repos_file, index=False)
        
        return [profile_file, repos_file]
    
    async def export_to_json(
        self,
        job_id: str,
        data: Dict[str, Any]
    ) -> Path:
        """
        Export data to JSON format
        
        Args:
            job_id: Job ID for filename
            data: Scrape data
            
        Returns:
            Path to exported file
        """
        username = data.get('username', 'unknown')
        output_file = self.output_dir / f"{job_id}_{username}_data.json"
        
        # Convert to JSON-serializable format
        export_data = {
            'username': username,
            'profile': data.get('profile', {}),
            'repositories': [
                repo.dict() if hasattr(repo, 'dict') else repo
                for repo in data.get('repositories', [])
            ],
            'total_stars': data.get('total_stars', 0),
            'total_forks': data.get('total_forks', 0),
            'top_languages': data.get('top_languages', {})
        }
        
        # Write to JSON
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        return output_file
