# ai_cache.py - Cache thông minh cho AI responses
import json
import os
import sys
import time
import hashlib
import random
from pathlib import Path
from paths import DATA_STORE_DIR

# Fix encoding for Windows console
if sys.platform == "win32":
    import codecs
    try:
        if hasattr(sys.stdout, 'encoding') and sys.stdout.encoding not in ['utf-8', 'UTF-8', None]:
            if hasattr(sys.stdout, 'buffer'):
                sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        if hasattr(sys.stderr, 'encoding') and sys.stderr.encoding not in ['utf-8', 'UTF-8', None]:
            if hasattr(sys.stderr, 'buffer'):
                sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    except (AttributeError, TypeError):
        pass

AI_CACHE_DIR = Path(DATA_STORE_DIR) / "ai_cache"
AI_CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Cache RAM đơn giản theo phiên
_AI_RAM = {}  # key -> {"ts": int, "hash": str, "data": dict}

def _hash_context(d: dict) -> str:
    """Hash context để detect khi data thay đổi."""
    s = json.dumps(d, ensure_ascii=False, sort_keys=True)
    return hashlib.md5(s.encode("utf-8")).hexdigest()

def cache_key(stock_code: str) -> str:
    """Generate cache key từ stock code."""
    return stock_code.upper()

def cache_path(stock_code: str) -> Path:
    """Đường dẫn file cache cho stock code."""
    return AI_CACHE_DIR / f"{stock_code.upper()}.json"

def load_cache(stock_code: str):
    """
    Load cache từ RAM hoặc disk.
    
    Returns:
        tuple: (data dict, context hash) hoặc (None, None) nếu không có cache
    """
    k = cache_key(stock_code)
    
    # 1) RAM cache (fastest)
    if k in _AI_RAM:
        print(f"[CACHE] Using RAM cache for {stock_code}")
        return _AI_RAM[k]["data"], _AI_RAM[k]["hash"]
    
    # 2) Disk cache
    p = cache_path(stock_code)
    if p.exists():
        try:
            obj = json.loads(p.read_text(encoding="utf-8"))
            _AI_RAM[k] = obj  # Load vào RAM
            print(f"[CACHE] Using disk cache for {stock_code}")
            return obj["data"], obj["hash"]
        except Exception as e:
            print(f"[WARN] Cache read error for {stock_code}: {e}")
            return None, None
    
    return None, None

def save_cache(stock_code: str, ctx_hash: str, data: dict):
    """
    Save cache vào RAM và disk.
    
    Args:
        stock_code: Mã cổ phiếu
        ctx_hash: Hash của context (để detect changes)
        data: Dict chứa tất cả AI sections
    """
    k = cache_key(stock_code)
    p = cache_path(stock_code)
    
    obj = {
        "ts": int(time.time()),
        "hash": ctx_hash,
        "data": data
    }
    
    # Save to RAM
    _AI_RAM[k] = obj
    
    # Save to disk
    try:
        p.write_text(
            json.dumps(obj, ensure_ascii=False, indent=2), 
            encoding="utf-8"
        )
        print(f"[CACHE] Saved cache for {stock_code}")
    except Exception as e:
        print(f"[WARN] Cache write error for {stock_code}: {e}")

def ai_backoff_sleep(attempt, base=8):
    """
    Backoff lũy tiến + jitter khi gặp 429.
    
    Args:
        attempt: Lần thử thứ mấy (0-indexed)
        base: Base delay (giây)
    """
    delay = (base * (2 ** attempt)) + random.uniform(0, 1.5)
    print(f"[BACKOFF] Retry {attempt + 1} after {delay:.1f}s...")
    time.sleep(delay)

def clear_cache(stock_code: str = None):
    """
    Clear cache cho 1 mã hoặc tất cả.
    
    Args:
        stock_code: Nếu None, xóa tất cả cache
    """
    if stock_code:
        k = cache_key(stock_code)
        # Clear RAM
        if k in _AI_RAM:
            del _AI_RAM[k]
        # Clear disk
        p = cache_path(stock_code)
        if p.exists():
            p.unlink()
        print(f"[CACHE] Cleared cache for {stock_code}")
    else:
        # Clear all
        _AI_RAM.clear()
        for f in AI_CACHE_DIR.glob("*.json"):
            f.unlink()
        print("[CACHE] Cleared all cache")

def get_cache_stats():
    """Get cache statistics."""
    ram_count = len(_AI_RAM)
    disk_files = list(AI_CACHE_DIR.glob("*.json"))
    disk_count = len(disk_files)
    
    total_size = sum(f.stat().st_size for f in disk_files)
    
    return {
        "ram_entries": ram_count,
        "disk_entries": disk_count,
        "total_size_mb": total_size / (1024 * 1024),
        "cache_dir": str(AI_CACHE_DIR)
    }

