# Copyright 2021 To 2024-present, Author: MrAKTech

import asyncio
import time
import hashlib
from typing import Dict, Any, Optional, Tuple
from MrAKTech.config import Telegram

# Try to import performance packages with fallbacks
try:
    import orjson as json_lib
    JSON_AVAILABLE = True
except ImportError:
    import json as json_lib
    JSON_AVAILABLE = False

try:
    import lz4.frame as lz4
    LZ4_AVAILABLE = True
except ImportError:
    LZ4_AVAILABLE = False

class AdvancedCache:
    """
    Advanced caching system for improved streaming performance
    """
    
    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        self.max_size = max_size
        self.ttl = ttl  # Time to live in seconds
        self.cache: Dict[str, Tuple[Any, float]] = {}  # key: (value, timestamp)
        self.access_times: Dict[str, float] = {}  # LRU tracking
        self.hit_count = 0
        self.miss_count = 0
        
    def _generate_key(self, *args, **kwargs) -> str:
        """Generate cache key from arguments"""
        key_string = str(args) + str(sorted(kwargs.items()))
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _is_expired(self, timestamp: float) -> bool:
        """Check if cache entry is expired"""
        return time.time() - timestamp > self.ttl
    
    def _evict_lru(self):
        """Evict least recently used items"""
        if len(self.cache) >= self.max_size:
            # Find LRU item
            lru_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
            self.cache.pop(lru_key, None)
            self.access_times.pop(lru_key, None)
    
    def get(self, key: str) -> Optional[Any]:
        """Get item from cache"""
        if key in self.cache:
            value, timestamp = self.cache[key]
            
            if self._is_expired(timestamp):
                # Remove expired item
                self.cache.pop(key, None)
                self.access_times.pop(key, None)
                self.miss_count += 1
                return None
            
            # Update access time
            self.access_times[key] = time.time()
            self.hit_count += 1
            return value
        
        self.miss_count += 1
        return None
    
    def set(self, key: str, value: Any):
        """Set item in cache"""
        # Evict if necessary
        self._evict_lru()
        
        # Add new item
        self.cache[key] = (value, time.time())
        self.access_times[key] = time.time()
    
    def delete(self, key: str):
        """Delete item from cache"""
        self.cache.pop(key, None)
        self.access_times.pop(key, None)
    
    def clear(self):
        """Clear all cache"""
        self.cache.clear()
        self.access_times.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.hit_count + self.miss_count
        hit_ratio = (self.hit_count / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'hit_count': self.hit_count,
            'miss_count': self.miss_count,
            'hit_ratio': hit_ratio,
            'ttl': self.ttl
        }
    
    async def cleanup_expired(self):
        """Periodic cleanup of expired entries"""
        while True:
            try:
                current_time = time.time()
                expired_keys = [
                    key for key, (_, timestamp) in self.cache.items()
                    if current_time - timestamp > self.ttl
                ]
                
                for key in expired_keys:
                    self.cache.pop(key, None)
                    self.access_times.pop(key, None)
                
                if expired_keys:
                    print(f"Cleaned up {len(expired_keys)} expired cache entries")
                
                await asyncio.sleep(300)  # Cleanup every 5 minutes
                
            except Exception as e:
                print(f"Cache cleanup error: {e}")
                await asyncio.sleep(600)

class FileMetadataCache(AdvancedCache):
    """
    Specialized cache for file metadata
    """
    
    def __init__(self):
        super().__init__(max_size=2000, ttl=7200)  # 2 hours TTL for file metadata
    
    def cache_file_info(self, message_id: int, file_id: Any):
        """Cache file information"""
        key = f"file_info_{message_id}"
        self.set(key, file_id)
    
    def get_file_info(self, message_id: int) -> Optional[Any]:
        """Get cached file information"""
        key = f"file_info_{message_id}"
        return self.get(key)

class StreamSessionCache(AdvancedCache):
    """
    Specialized cache for streaming sessions
    """
    
    def __init__(self):
        super().__init__(max_size=500, ttl=1800)  # 30 minutes TTL for sessions
    
    def cache_session(self, client_id: str, dc_id: int, session: Any):
        """Cache streaming session"""
        key = f"session_{client_id}_{dc_id}"
        self.set(key, session)
    
    def get_session(self, client_id: str, dc_id: int) -> Optional[Any]:
        """Get cached session"""
        key = f"session_{client_id}_{dc_id}"
        return self.get(key)

# Global cache instances
file_metadata_cache = FileMetadataCache()
stream_session_cache = StreamSessionCache()
general_cache = AdvancedCache()

async def start_cache_cleanup():
    """Start cache cleanup tasks"""
    asyncio.create_task(file_metadata_cache.cleanup_expired())
    asyncio.create_task(stream_session_cache.cleanup_expired())
    asyncio.create_task(general_cache.cleanup_expired())
    print("Cache cleanup tasks started")
