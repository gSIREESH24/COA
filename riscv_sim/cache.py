import math

class CacheBlock:
    def __init__(self, tag=None, data=None, valid=False):
        self.tag = tag
        self.data = data
        self.valid = valid
        self.dirty = False
        self.access_time = 0
        self.frequency = 0

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

    def read(self, address):
        self.total_accesses += 1
        self.access_counter += 1
        tag = self._get_tag(address)
        set_index = self._get_set_index(address)
        
        for block in self.cache[set_index]:
            if block.valid and block.tag == tag:
                self.cache_hits += 1
                block.access_time = self.access_counter
                block.frequency += 1
                return True, self.latency, block.data
                
        self.cache_misses += 1
        return False, self.latency, None

    def write(self, address, data):
        self.total_accesses += 1
        self.access_counter += 1
        tag = self._get_tag(address)
        set_index = self._get_set_index(address)
        
        for block in self.cache[set_index]:
            if block.valid and block.tag == tag:
                self.cache_hits += 1
                block.data = data
                block.dirty = True
                block.access_time = self.access_counter
                block.frequency += 1
                return True, self.latency
                
        self.cache_misses += 1
        return False, self.latency

    def allocate(self, address, data, is_dirty=False):
        self.access_counter += 1
        tag = self._get_tag(address)
        set_index = self._get_set_index(address)
        cache_set = self.cache[set_index]
        
        victim_index = None
        for i, block in enumerate(cache_set):
            if not block.valid:
                victim_index = i
                break
                
        if victim_index is None:
            victim_index = self._find_victim(cache_set)
            
        victim_block = cache_set[victim_index]
        
        evicted_addr = None
        was_dirty = False
        evicted_data = None
        
        if victim_block.valid:
            evicted_addr = (victim_block.tag << (self.block_offset_bits + self.set_index_bits)) | (set_index << self.block_offset_bits)
            was_dirty = victim_block.dirty
            evicted_data = victim_block.data
        
        victim_block.tag = tag
        victim_block.data = data
        victim_block.valid = True
        victim_block.dirty = is_dirty
        victim_block.access_time = self.access_counter
        victim_block.frequency = 1
        
        return evicted_addr, was_dirty, evicted_data

    def _find_victim(self, cache_set):
        if self.replacement_policy == "LFU":
            return min(range(len(cache_set)), key=lambda i: cache_set[i].frequency)
        else:
            return min(range(len(cache_set)), key=lambda i: cache_set[i].access_time)

    def invalidate(self, address):
        tag = self._get_tag(address)
        set_index = self._get_set_index(address)
        cache_set = self.cache[set_index]
        for block in cache_set:
            if block.valid and block.tag == tag:
                block.valid = False
                return True, block.dirty, block.data
        return False, False, None

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
                block.dirty = False
                block.tag = None
                block.data = None