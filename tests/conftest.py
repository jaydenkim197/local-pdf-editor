import os
from pathlib import Path

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
cache = Path(__file__).resolve().parents[1] / '.cache'
cache.mkdir(exist_ok=True)
os.environ.setdefault('XDG_CACHE_HOME', str(cache))
