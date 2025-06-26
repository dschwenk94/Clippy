#!/usr/bin/env python3
"""
Storage Optimizer - Smart caching for viral clipper
Avoids re-downloading videos and manages storage efficiently
"""

import os
import json
import hashlib
from datetime import datetime
from typing import Tuple, Optional

class StorageOptimizer:
    def __init__(self, downloads_dir='downloads'):
        self.downloads_dir = downloads_dir
        self.cache_file = os.path.join(downloads_dir, 'video_cache.json')
        self.cache = self.load_cache()
    
    def load_cache(self) -> dict:
        """Load video cache from JSON file"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Could not load cache: {e}")
        return {}
    
    def save_cache(self):
        """Save video cache to JSON file"""
        try:
            os.makedirs(self.downloads_dir, exist_ok=True)
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save cache: {e}")
    
    def get_url_hash(self, video_url: str) -> str:
        """Generate hash for video URL"""
        return hashlib.md5(video_url.encode()).hexdigest()[:12]
    
    def check_existing_download(self, video_url: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Check if video already exists and return path, title, video_id"""
        url_hash = self.get_url_hash(video_url)
        
        if url_hash in self.cache:
            cache_entry = self.cache[url_hash]
            file_path = cache_entry.get('file_path')
            
            # Check if file still exists
            if file_path and os.path.exists(file_path):
                print(f"📋 Found cached video: {os.path.basename(file_path)}")
                return file_path, cache_entry.get('title'), cache_entry.get('video_id')
            else:
                # File was deleted, remove from cache
                del self.cache[url_hash]
                self.save_cache()
        
        return None, None, None
    
    def add_to_cache(self, video_url: str, file_path: str, title: str, video_id: str = None):
        """Add video to cache"""
        url_hash = self.get_url_hash(video_url)
        
        self.cache[url_hash] = {
            'url': video_url,
            'file_path': file_path,
            'title': title,
            'video_id': video_id or '',
            'cached_at': datetime.now().isoformat(),
            'file_size': os.path.getsize(file_path) if os.path.exists(file_path) else 0
        }
        
        self.save_cache()
        print(f"📝 Added to cache: {title}")
    
    def get_cache_stats(self) -> dict:
        """Get cache statistics"""
        total_files = len(self.cache)
        total_size = sum(entry.get('file_size', 0) for entry in self.cache.values())
        
        return {
            'total_files': total_files,
            'total_size_mb': total_size / (1024 * 1024),
            'cache_file': self.cache_file,
            'downloads_dir': self.downloads_dir
        }
    
    def cleanup_missing_files(self):
        """Remove cache entries for files that no longer exist"""
        removed_count = 0
        for url_hash, entry in list(self.cache.items()):
            file_path = entry.get('file_path')
            if file_path and not os.path.exists(file_path):
                del self.cache[url_hash]
                removed_count += 1
        
        if removed_count > 0:
            self.save_cache()
            print(f"🧹 Cleaned up {removed_count} missing files from cache")
        
        return removed_count

if __name__ == "__main__":
    # Test storage optimizer
    optimizer = StorageOptimizer()
    stats = optimizer.get_cache_stats()
    print(f"Cache stats: {stats['total_files']} files, {stats['total_size_mb']:.1f} MB")
    optimizer.cleanup_missing_files()
