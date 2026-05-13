from cache import Cache
from virtual_memory import VirtualMemorySubsystem
from tlb import TLB


class MemorySystem:
    def __init__(self, l1i_config, l1d_config, l2_config, main_memory_latency,
                 memory_size: int = 4096, vm_config: dict = None,
                 tlb_config: dict = None, l2_enabled: bool = True):

        self.main_memory         = bytearray(memory_size)
        self.main_memory_latency = main_memory_latency
        self.l2_enabled          = l2_enabled

        self.l1i = Cache(l1i_config['size'], l1i_config['block_size'],
                         l1i_config['associativity'], l1i_config['latency'],
                         l1i_config.get('replacement_policy', 'LRU'), 'L1I')

        self.l1d = Cache(l1d_config['size'], l1d_config['block_size'],
                         l1d_config['associativity'], l1d_config['latency'],
                         l1d_config.get('replacement_policy', 'LRU'), 'L1D')

        self.l2 = Cache(l2_config['size'], l2_config['block_size'],
                        l2_config['associativity'], l2_config['latency'],
                        l2_config.get('replacement_policy', 'LRU'), 'L2')

        self.vm  = VirtualMemorySubsystem(vm_config)  if vm_config  else None
        self.tlb = TLB(num_entries=tlb_config.get('num_entries', 16),
                       replacement_policy=tlb_config.get('replacement_policy', 'lru')) \
                   if tlb_config else None

        self._vm_stats = {
            "tlb_hits":           0,
            "tlb_misses":         0,
            "page_walks":         0,
            "page_faults":        0,
            "evictions":          0,
            "dirty_evictions":    0,
            "translation_cycles": 0,
        }

    def get_memory(self):
        return self.main_memory

    def access(self, address: int, access_type: str, value=None):
        if access_type == "IF":
            return self._handle_read(address & ~3, self.l1i)

        if access_type == "LOAD":
            paddr, vm_penalty = self._translate(address, is_write=False)
            cache_lat, hit    = self._handle_read(paddr & ~3, self.l1d)
            return vm_penalty + cache_lat, hit

        if access_type == "STORE":
            paddr, vm_penalty = self._translate(address, is_write=True)
            cache_lat, hit    = self._handle_write(paddr & ~3, value)
            return vm_penalty + cache_lat, hit

        return 1, False

    def _translate(self, vaddr: int, is_write: bool) -> tuple:
        if self.vm is None or self.tlb is None:
            return vaddr, 0

        paddr, penalty, events = self.vm.translate(vaddr, is_write, self.tlb)

        self._vm_stats["translation_cycles"] += penalty
        if events["tlb_hit"]:        self._vm_stats["tlb_hits"]        += 1
        if events["tlb_miss"]:       self._vm_stats["tlb_misses"]      += 1
        if events["page_walk"]:      self._vm_stats["page_walks"]      += 1
        if events["page_fault"]:     self._vm_stats["page_faults"]     += 1
        if events["eviction"]:       self._vm_stats["evictions"]       += 1
        if events["dirty_eviction"]: self._vm_stats["dirty_evictions"] += 1

        return paddr, penalty

    def _handle_read(self, address, l1_cache):
        hit_l1, lat1, _ = l1_cache.read(address)
        if hit_l1:
            return lat1, True

        if self.l2_enabled:
            hit_l2, lat2, l2_data = self.l2.read(address)
            total_lat = lat1 + lat2
        else:
            hit_l2, lat2, l2_data = False, 0, None
            total_lat = lat1

        if hit_l2:
            fetched_data = l2_data
        else:
            fetched_data  = self._read_from_memory(address)
            total_lat    += self.main_memory_latency
            if self.l2_enabled:
                evict_addr, dirty, evict_data = self.l2.allocate(address, fetched_data, is_dirty=False)
                if evict_addr is not None:
                    self._handle_l2_eviction(evict_addr, dirty, evict_data)

        evict_addr, dirty, evict_data = l1_cache.allocate(address, fetched_data, is_dirty=False)
        if evict_addr is not None and dirty:
            self._write_back_to_l2(evict_addr, evict_data)

        return total_lat, False

    def _handle_write(self, address, value):
        value = value & 0xFFFFFFFF if value is not None else 0

        hit_l1, lat1 = self.l1d.write(address, value)
        if hit_l1:
            return lat1, True

        if self.l2_enabled:
            hit_l2, lat2, l2_data = self.l2.read(address)
            total_lat = lat1 + lat2
        else:
            hit_l2, lat2, l2_data = False, 0, None
            total_lat = lat1

        if not hit_l2:
            l2_data    = self._read_from_memory(address)
            total_lat += self.main_memory_latency
            if self.l2_enabled:
                evict_addr, dirty, evict_data = self.l2.allocate(address, l2_data, is_dirty=False)
                if evict_addr is not None:
                    self._handle_l2_eviction(evict_addr, dirty, evict_data)

        evict_addr, dirty, evict_data = self.l1d.allocate(address, value, is_dirty=True)
        if evict_addr is not None and dirty:
            self._write_back_to_l2(evict_addr, evict_data)

        return total_lat, False

    def _write_back_to_l2(self, address, data):
        if not self.l2_enabled:
            self._write_to_memory(address, data)
            return
        hit_l2, _ = self.l2.write(address, data)
        if not hit_l2:
            evict_addr, dirty, evict_data = self.l2.allocate(address, data, is_dirty=True)
            if evict_addr is not None:
                self._handle_l2_eviction(evict_addr, dirty, evict_data)

    def _handle_l2_eviction(self, evict_l2_addr, l2_was_dirty, l2_evict_data):
        i_valid, i_dirty, i_data = self.l1i.invalidate(evict_l2_addr)
        d_valid, d_dirty, d_data = self.l1d.invalidate(evict_l2_addr)

        is_dirty   = l2_was_dirty or i_dirty or d_dirty
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
        self.main_memory[addr]                                = value & 0xFF
        self.main_memory[(addr + 1) % len(self.main_memory)] = (value >> 8)  & 0xFF
        self.main_memory[(addr + 2) % len(self.main_memory)] = (value >> 16) & 0xFF
        self.main_memory[(addr + 3) % len(self.main_memory)] = (value >> 24) & 0xFF

    def get_miss_rate(self):
        return {
            "L1I_miss_rate": self.l1i.get_miss_rate(),
            "L1D_miss_rate": self.l1d.get_miss_rate(),
            "L2_miss_rate":  self.l2.get_miss_rate(),
        }

    def get_stats(self):
        return {
            "L1I": self.l1i.get_stats(),
            "L1D": self.l1d.get_stats(),
            "L2":  self.l2.get_stats(),
        }

    def get_vm_stats(self) -> dict:
        if self.vm is None:
            return {}
        stats = dict(self._vm_stats)
        stats["frame_stats"] = self.vm.frame_allocator.get_stats()
        if self.tlb:
            stats["tlb_detail"] = self.tlb.get_stats()
        return stats