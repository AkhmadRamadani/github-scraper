"""
Cache manager for API responses
"""

import asyncio
from typing import Optional, Any, Dict
from datetime import datetime, timedelta
import hashlib
import json

from ..core.config import settings


class CacheManager:
    """In-memory cache manager with TTL support"""
    
    def __init__(self):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.lock = asyncio.Lock()
    
    def _generate_key(self, prefix: str, identifier: str, **kwargs) -> str:
        """Generate cache key from prefix and parameters"""
        params_str = json.dumps(kwargs, sort_keys=True)
        params_hash = hashlib.md5(params_str.encode()).hexdigest()
        return f"{prefix}:{identifier}:{params_hash}"
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        async with self.lock:
            if key not in self.cache:
                return None
            
            entry = self.cache[key]
            
            # Check if expired
            if datetime.utcnow() > entry['expires_at']:
                del self.cache[key]
                return None
            
            entry['hits'] += 1
            entry['last_accessed'] = datetime.utcnow()
            return entry['value']
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None
    ) -> None:
        """
        Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (default from settings)
        """
        async with self.lock:
            ttl = ttl or settings.CACHE_TTL
            
            self.cache[key] = {
                'value': value,
                'created_at': datetime.utcnow(),
                'expires_at': datetime.utcnow() + timedelta(seconds=ttl),
                'last_accessed': datetime.utcnow(),
                'hits': 0
            }
            
            # Enforce max cache size (LRU eviction)
            if len(self.cache) > settings.CACHE_MAX_SIZE:
                await self._evict_lru()
    
    async def delete(self, key: str) -> bool:
        """
        Delete value from cache
        
        Args:
            key: Cache key
            
        Returns:
            True if deleted, False if not found
        """
        async with self.lock:
            if key in self.cache:
                del self.cache[key]
                return True
            return False
    
    async def clear_all(self) -> int:
        """
        Clear all cache entries
        
        Returns:
            Number of entries cleared
        """
        async with self.lock:
            count = len(self.cache)
            self.cache.clear()
            return count
    
    async def get_cache_size(self) -> int:
        """Get current cache size"""
        return len(self.cache)
    
    async def _evict_lru(self) -> None:
        """Evict least recently used entry"""
        if not self.cache:
            return
        
        # Find LRU entry
        lru_key = min(
            self.cache.keys(),
            key=lambda k: self.cache[k]['last_accessed']
        )
        
        del self.cache[lru_key]
    
    async def cleanup_expired(self) -> int:
        """
        Remove expired entries
        
        Returns:
            Number of entries removed
        """
        async with self.lock:
            now = datetime.utcnow()
            expired_keys = [
                key for key, entry in self.cache.items()
                if now > entry['expires_at']
            ]
            
            for key in expired_keys:
                del self.cache[key]
            
            return len(expired_keys)
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        async with self.lock:
            total_hits = sum(entry['hits'] for entry in self.cache.values())
            
            return {
                'size': len(self.cache),
                'max_size': settings.CACHE_MAX_SIZE,
                'total_hits': total_hits,
                'entries': [
                    {
                        'key': key,
                        'created_at': entry['created_at'].isoformat(),
                        'expires_at': entry['expires_at'].isoformat(),
                        'hits': entry['hits']
                    }
                    for key, entry in list(self.cache.items())[:10]  # Top 10
                ]
            }


# Global cache manager instance
cache_manager = CacheManager()
