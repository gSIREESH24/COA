import math

class CacheBlock:
    def __init__(self, tag=None, data=None, valid=False):
        self.tag = tag
        self.data = data
        self.valid = valid
        self.access_time = 0
        self.insertion_time = 0


class Cache:

    def __init__(self, cache_size, block_size, associativity, latency, replacement_policy="LRU", cache_name="L1"):
        self.cache_size = cache_size
        self.block_size = block_size
        self.associativity = associativity
        self.latency = latency
        self.replacement_policy = replacement_policy.upper()
        self.cache_name = cache_name
        
        self.num_blocks = cache_size // block_size
        self.num_sets = self.num_blocks // associativity
        
        self.block_offset_bits = int(math.log2(block_size))
        self.set_index_bits = int(math.log2(self.num_sets))
        
        self.cache = [[CacheBlock() for _ in range(associativity)] for _ in range(self.num_sets)]
        
        self.total_accesses = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.access_counter = 0
        
    def _get_set_index(self, address):
        return (address >> self.block_offset_bits) % self.num_sets
    
    def _get_tag(self, address):
        return address >> (self.block_offset_bits + self.set_index_bits)
    
    def _get_block_offset(self, address):
        return address & (self.block_size - 1)
    
    def access(self, address, data=None, is_write=False):
        self.total_accesses += 1
        self.access_counter += 1
        
        tag = self._get_tag(address)
        set_index = self._get_set_index(address)
        cache_set = self.cache[set_index]
        
        for block in cache_set:
            if block.valid and block.tag == tag:
                self.cache_hits += 1
                block.access_time = self.access_counter
                if is_write:
                    block.data = data
                return True, self.latency, block.data
        
        self.cache_misses += 1
        
        victim_index = self._find_victim(cache_set)
        block = cache_set[victim_index]
        block.tag = tag
        block.data = data
        block.valid = True
        block.access_time = self.access_counter
        block.insertion_time = self.access_counter
        
        return False, self.latency, data
    
    def _find_victim(self, cache_set):
        min_time = float('inf')
        victim_index = 0
        
        for i, block in enumerate(cache_set):
            if not block.valid:
                return i
            time_to_check = block.access_time if self.replacement_policy == "LRU" else block.insertion_time
            if time_to_check < min_time:
                min_time = time_to_check
                victim_index = i
        
        return victim_index
    
    def get_miss_rate(self):
        return 0.0 if self.total_accesses == 0 else self.cache_misses / self.total_accesses
    
    def get_hit_rate(self):
        return 0.0 if self.total_accesses == 0 else self.cache_hits / self.total_accesses
    
    def get_stats(self):
        return {
            "name": self.cache_name,
            "total_accesses": self.total_accesses,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "miss_rate": self.get_miss_rate(),
            "hit_rate": self.get_hit_rate()
        }
    
    def flush(self):
        for cache_set in self.cache:
            for block in cache_set:
                block.valid = False
                block.tag = None
                block.data = None