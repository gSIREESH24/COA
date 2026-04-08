import math


class CacheBlock:
    def __init__(self, block_size, tag=None, valid=False):
        self.tag = tag
        self.data = bytearray(block_size)
        self.valid = valid
        self.dirty = False
        self.access_time = 0
        self.frequency = 0


class Cache:
    def __init__(
        self,
        cache_size,
        block_size,
        associativity,
        latency,
        replacement_policy="LRU",
        cache_name="L1",
    ):
        if cache_size <= 0 or block_size <= 0 or associativity <= 0:
            raise ValueError("cache_size, block_size, and associativity must be positive")

        if cache_size % block_size != 0:
            raise ValueError("cache_size must be divisible by block_size")

        self.cache_size = cache_size
        self.block_size = block_size
        self.associativity = associativity
        self.latency = latency
        self.replacement_policy = replacement_policy.upper()
        self.cache_name = cache_name

        self.num_blocks = cache_size // block_size
        self.num_sets = self.num_blocks // associativity

        if self.num_sets <= 0:
            raise ValueError("Invalid cache configuration")

        self.block_offset_bits = int(math.log2(block_size))
        self.set_index_bits = int(math.log2(self.num_sets))

        self.cache = [
            [CacheBlock(block_size) for _ in range(associativity)]
            for _ in range(self.num_sets)
        ]

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

    def _normalize_block_data(self, block_data):
        result = bytearray(self.block_size)
        if block_data is None:
            return result

        src = bytes(block_data)
        n = min(len(src), self.block_size)
        result[:n] = src[:n]
        return result

    def _read_word_from_block(self, block_data, offset):
        return int.from_bytes(block_data[offset:offset + 4], byteorder="little", signed=False)

    def _write_word_to_block(self, block_data, offset, value):
        block_data[offset:offset + 4] = (value & 0xFFFFFFFF).to_bytes(
            4, byteorder="little", signed=False
        )

    def _find_victim(self, cache_set):
        for i, block in enumerate(cache_set):
            if not block.valid:
                return i

        if self.replacement_policy == "LFU":
            min_freq = float("inf")
            victim_index = 0
            for i, block in enumerate(cache_set):
                if block.frequency < min_freq:
                    min_freq = block.frequency
                    victim_index = i
            return victim_index

        min_time = float("inf")
        victim_index = 0
        for i, block in enumerate(cache_set):
            if block.access_time < min_time:
                min_time = block.access_time
                victim_index = i
        return victim_index

    def _evicted_address(self, block, set_index):
        return (block.tag << (self.block_offset_bits + self.set_index_bits)) | (
            set_index << self.block_offset_bits
        )

    def read(self, address):
        self.total_accesses += 1
        self.access_counter += 1

        tag = self._get_tag(address)
        set_index = self._get_set_index(address)
        cache_set = self.cache[set_index]

        for block in cache_set:
            if block.valid and block.tag == tag:
                self.cache_hits += 1
                block.access_time = self.access_counter
                block.frequency += 1
                return True, self.latency, bytes(block.data), None

        self.cache_misses += 1
        return False, self.latency, None, None

    def write(self, address, value):
        self.total_accesses += 1
        self.access_counter += 1

        tag = self._get_tag(address)
        set_index = self._get_set_index(address)
        offset = self._get_block_offset(address)
        cache_set = self.cache[set_index]

        for block in cache_set:
            if block.valid and block.tag == tag:
                self.cache_hits += 1
                self._write_word_to_block(block.data, offset, value)
                block.dirty = True
                block.access_time = self.access_counter
                block.frequency += 1
                return True, self.latency, bytes(block.data), None

        self.cache_misses += 1
        return False, self.latency, None, None

    def fill_line(self, address, block_data, write_value=None):
        tag = self._get_tag(address)
        set_index = self._get_set_index(address)
        offset = self._get_block_offset(address)
        cache_set = self.cache[set_index]

        victim_index = self._find_victim(cache_set)
        victim = cache_set[victim_index]

        evicted_info = None
        if victim.valid:
            evicted_info = {
                "address": self._evicted_address(victim, set_index),
                "data": bytes(victim.data),
                "dirty": victim.dirty,
            }

        victim.tag = tag
        victim.data = self._normalize_block_data(block_data)
        victim.valid = True
        victim.dirty = False
        victim.access_time = self.access_counter
        victim.frequency = 1

        if write_value is not None:
            self._write_word_to_block(victim.data, offset, write_value)
            victim.dirty = True

        return evicted_info

    def invalidate(self, address):
        tag = self._get_tag(address)
        set_index = self._get_set_index(address)
        cache_set = self.cache[set_index]

        for block in cache_set:
            if block.valid and block.tag == tag:
                block.valid = False
                block.tag = None
                block.dirty = False
                block.data = bytearray(self.block_size)
                block.access_time = 0
                block.frequency = 0
                return True
        return False

    def flush(self):
        for cache_set in self.cache:
            for block in cache_set:
                block.valid = False
                block.tag = None
                block.dirty = False
                block.data = bytearray(self.block_size)
                block.access_time = 0
                block.frequency = 0

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
            "hit_rate": self.get_hit_rate(),
        }