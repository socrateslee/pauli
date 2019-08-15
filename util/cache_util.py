# coding:utf-8
from gscache import TinyCache, Cached
from gscache.lock import lock_maker
from .. import conf

in_cache = TinyCache(256)

if 'MEMCACHE_ADDRESS' in conf.__dict__:
    import memcache
    cache = memcache.Client(conf.MEMCACHE_ADDRESS)
    cached = Cached(in_cache, cache)
else:
    cache = in_cache
    cached = Cached(in_cache)

cache_lock = lock_maker(cache)
