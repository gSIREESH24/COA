from cache import Cache
class MemorySystem:
    def __init__(self, l1i_config, l1d_config, l2_config, main_memory_latency, memory_size=4096):
        self.main_memory = bytearray(memory_size)
        self.main_memory_latency = main_memory_latency
        
        self.l1i = Cache(
            l1i_config['size'],
            l1i_config['block_size'],
            l1i_config['associativity'],
            l1i_config['latency'],
            l1i_config.get('replacement_policy', 'LRU'),
            'L1I'
        )
        
        self.l1d = Cache(
            l1d_config['size'],
            l1d_config['block_size'],
            l1d_config['associativity'],
            l1d_config['latency'],
            l1d_config.get('replacement_policy', 'LRU'),
            'L1D'
        )
        
        self.l2 = Cache(
            l2_config['size'],
            l2_config['block_size'],
            l2_config['associativity'],
            l2_config['latency'],
            l2_config.get('replacement_policy', 'LRU'),
            'L2'
        )
   
    def get_memory(self):
        return self.main_memory

    def access(self, address, access_type, value=None):
        address = address & ~3
        total_lat = 0
        
        if access_type == "IF":
            return self._handle_read(address, self.l1i)
        elif access_type == "LOAD":
            return self._handle_read(address, self.l1d)
        elif access_type == "STORE":
            return self._handle_write(address, value)

    def _handle_read(self, address, l1_cache):
        hit_l1, lat1, _ = l1_cache.read(address)
        if hit_l1:
            return lat1, True
            
        hit_l2, lat2, l2_data = self.l2.read(address)
        total_lat = lat1 + lat2
        
        fetched_data = None
        if hit_l2:
            fetched_data = l2_data
        else:
            fetched_data = self._read_from_memory(address)
            total_lat += self.main_memory_latency
            
            evict_l2_addr, l2_dirty, l2_evict_data = self.l2.allocate(address, fetched_data, is_dirty=False)
            if evict_l2_addr is not None:
                self._handle_l2_eviction(evict_l2_addr, l2_dirty, l2_evict_data)
                
        evict_l1_addr, l1_dirty, l1_evict_data = l1_cache.allocate(address, fetched_data, is_dirty=False)
        if evict_l1_addr is not None and l1_dirty:
            self._write_back_to_l2(evict_l1_addr, l1_evict_data)
            
        return total_lat, False

    def _handle_write(self, address, value):
        value = value & 0xFFFFFFFF
        
        hit_l1, lat1 = self.l1d.write(address, value)
        if hit_l1:
            return lat1, True
            
        hit_l2, lat2, l2_data = self.l2.read(address)
        total_lat = lat1 + lat2
        
        if not hit_l2:
            l2_data = self._read_from_memory(address)
            total_lat += self.main_memory_latency
            
            evict_l2_addr, l2_dirty, l2_evict_data = self.l2.allocate(address, l2_data, is_dirty=False)
            if evict_l2_addr is not None:
                self._handle_l2_eviction(evict_l2_addr, l2_dirty, l2_evict_data)

        evict_l1_addr, l1_dirty, l1_evict_data = self.l1d.allocate(address, value, is_dirty=True)
        if evict_l1_addr is not None and l1_dirty:
            self._write_back_to_l2(evict_l1_addr, l1_evict_data)
            
        return total_lat, False
        
    def _write_back_to_l2(self, address, data):
        hit_l2, lat2 = self.l2.write(address, data)
        if not hit_l2:
            evict_l2_addr, l2_dirty, l2_evict_data = self.l2.allocate(address, data, is_dirty=True)
            if evict_l2_addr is not None:
                self._handle_l2_eviction(evict_l2_addr, l2_dirty, l2_evict_data)

    def _handle_l2_eviction(self, evict_l2_addr, l2_was_dirty, l2_evict_data):
        i_valid, i_dirty, i_data = self.l1i.invalidate(evict_l2_addr)
        d_valid, d_dirty, d_data = self.l1d.invalidate(evict_l2_addr)
        
        is_dirty = l2_was_dirty or i_dirty or d_dirty
        final_data = l2_evict_data
        
        if d_dirty:
            final_data = d_data
        elif i_dirty:
            final_data = i_data
            
        if is_dirty and final_data is not None:
            self._write_to_memory(evict_l2_addr, final_data)

    def _read_from_memory(self, address):
        addr = address % len(self.main_memory)
        b0 = self.main_memory[addr]
        b1 = self.main_memory[(addr + 1) % len(self.main_memory)]
        b2 = self.main_memory[(addr + 2) % len(self.main_memory)]
        b3 = self.main_memory[(addr + 3) % len(self.main_memory)]
        return b0 | (b1 << 8) | (b2 << 16) | (b3 << 24)
   
    def _write_to_memory(self, address, value):
        addr = address % len(self.main_memory)
        self.main_memory[addr] = value & 0xFF
        self.main_memory[(addr + 1) % len(self.main_memory)] = (value >> 8) & 0xFF
        self.main_memory[(addr + 2) % len(self.main_memory)] = (value >> 16) & 0xFF
        self.main_memory[(addr + 3) % len(self.main_memory)] = (value >> 24) & 0xFF
   
    def get_miss_rate(self):
        return {
            "L1I_miss_rate": self.l1i.get_miss_rate(),
            "L1D_miss_rate": self.l1d.get_miss_rate(),
            "L2_miss_rate": self.l2.get_miss_rate()
        }
   
    def get_stats(self):
        return {
            "L1I": self.l1i.get_stats(),
            "L1D": self.l1d.get_stats(),
            "L2": self.l2.get_stats()
        }