"""
Simple performance monitoring utilities
"""
import time
import functools
from typing import Dict, Any

class PerformanceMonitor:
    def __init__(self):
        self.timings = {}
    
    def time_function(self, func_name: str):
        """Decorator to time function execution"""
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                result = func(*args, **kwargs)
                end_time = time.time()
                
                execution_time = end_time - start_time
                if func_name not in self.timings:
                    self.timings[func_name] = []
                self.timings[func_name].append(execution_time)
                
                print(f"⏱️ {func_name}: {execution_time:.2f}s")
                return result
            return wrapper
        return decorator
    
    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        stats = {}
        for func_name, times in self.timings.items():
            stats[func_name] = {
                'count': len(times),
                'avg_time': sum(times) / len(times),
                'total_time': sum(times),
                'min_time': min(times),
                'max_time': max(times)
            }
        return stats

# Global performance monitor
perf_monitor = PerformanceMonitor()
