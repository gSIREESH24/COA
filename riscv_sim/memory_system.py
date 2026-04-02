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
        
        if access_type == "IF":
            hit_l1, lat1, data = self.l1i.access(address)
            if hit_l1:
                return lat1, True
            
            hit_l2, lat2, data = self.l2.access(address)
            if hit_l2:
                self.l1i.access(address, data)
                return lat1 + lat2, True
                
            data = self._read_from_memory(address)
            self.l2.access(address, data)
            self.l1i.access(address, data)
            
            return lat1 + lat2 + self.main_memory_latency, False
            
        elif access_type == "LOAD":
            hit_l1, lat1, data = self.l1d.access(address)
            if hit_l1:
                return lat1, True
            
            hit_l2, lat2, data = self.l2.access(address)
            if hit_l2:
                self.l1d.access(address, data)
                return lat1 + lat2, True
            
            data = self._read_from_memory(address)
            self.l2.access(address, data)
            self.l1d.access(address, data)
            
            return lat1 + lat2 + self.main_memory_latency, False
            
        elif access_type == "STORE":
            value = value & 0xFFFFFFFF
            hit_l1, lat1, _ = self.l1d.access(address, value, is_write=True)
            
            if hit_l1:
                self._write_to_memory(address, value)
                return lat1, True
            
            hit_l2, lat2, _ = self.l2.access(address, value, is_write=True)
            
            if hit_l2:
                self.l1d.access(address, value, is_write=True)
                self._write_to_memory(address, value)
                return lat1 + lat2, True
            
            self._write_to_memory(address, value)
            self.l2.access(address, value)
            self.l1d.access(address, value)
            
            return lat1 + lat2 + self.main_memory_latency, False
    
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