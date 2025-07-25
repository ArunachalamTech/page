# Copyright 2021 To 2024-present, Author: MrAKTech

import asyncio
import logging
import psutil
import time
from typing import Dict, List
from MrAKTech.config import Telegram

logger = logging.getLogger("performance")

class PerformanceMonitor:
    """
    Advanced performance monitoring for streaming optimization
    """
    
    def __init__(self):
        self.stats = {
            'connections': 0,
            'active_streams': 0,
            'bandwidth_usage': 0,
            'memory_usage': 0,
            'cpu_usage': 0,
            'cache_hits': 0,
            'cache_misses': 0
        }
        self.connection_history: List[Dict] = []
        self.start_time = time.time()
        
    async def monitor_performance(self):
        """
        Continuous performance monitoring
        """
        while True:
            try:
                # Get system metrics
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                network = psutil.net_io_counters()
                
                # Update stats
                self.stats.update({
                    'cpu_usage': cpu_percent,
                    'memory_usage': memory.percent,
                    'memory_available': memory.available,
                    'network_sent': network.bytes_sent,
                    'network_recv': network.bytes_recv,
                    'uptime': time.time() - self.start_time
                })
                
                # Log performance if critical
                if cpu_percent > 90:
                    logger.warning(f"High CPU usage: {cpu_percent}%")
                
                if memory.percent > 90:  # Slightly higher threshold to reduce noise
                    logger.warning(f"High memory usage: {memory.percent}%")
                    # Force garbage collection on high memory usage
                    import gc
                    gc.collect()
                
                # Store historical data (keep last 100 entries)
                self.connection_history.append({
                    'timestamp': time.time(),
                    'cpu': cpu_percent,
                    'memory': memory.percent,
                    'active_streams': self.stats['active_streams']
                })
                
                if len(self.connection_history) > 100:
                    self.connection_history.pop(0)
                
                await asyncio.sleep(30)  # Monitor every 30 seconds
                
            except Exception as e:
                logger.error(f"Performance monitoring error: {e}")
                await asyncio.sleep(60)
    
    def increment_active_streams(self):
        """Increment active stream counter"""
        self.stats['active_streams'] += 1
        
    def decrement_active_streams(self):
        """Decrement active stream counter"""
        if self.stats['active_streams'] > 0:
            self.stats['active_streams'] -= 1
    
    def cache_hit(self):
        """Record cache hit"""
        self.stats['cache_hits'] += 1
        
    def cache_miss(self):
        """Record cache miss"""
        self.stats['cache_misses'] += 1
    
    def get_cache_hit_ratio(self) -> float:
        """Calculate cache hit ratio"""
        total = self.stats['cache_hits'] + self.stats['cache_misses']
        if total == 0:
            return 0.0
        return (self.stats['cache_hits'] / total) * 100
    
    def get_performance_summary(self) -> Dict:
        """Get comprehensive performance summary"""
        return {
            **self.stats,
            'cache_hit_ratio': self.get_cache_hit_ratio(),
            'average_cpu': sum(h['cpu'] for h in self.connection_history[-10:]) / min(10, len(self.connection_history)) if self.connection_history else 0,
            'average_memory': sum(h['memory'] for h in self.connection_history[-10:]) / min(10, len(self.connection_history)) if self.connection_history else 0,
            'peak_streams': max((h['active_streams'] for h in self.connection_history), default=0)
        }

# Global performance monitor instance
performance_monitor = PerformanceMonitor()

async def start_performance_monitoring():
    """Start the performance monitoring task"""
    asyncio.create_task(performance_monitor.monitor_performance())
    logger.info("Performance monitoring started")
