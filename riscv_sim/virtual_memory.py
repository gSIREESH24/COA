from collections import OrderedDict, deque


class FrameAllocator:
    def __init__(self, num_frames: int):
        if num_frames <= 0:
            raise ValueError("num_frames must be positive")
        self.num_frames = num_frames
        self._free: deque = deque(range(num_frames))
        self._used: set = set()
        self.total_allocations = 0
        self.total_frees = 0

    def allocate(self) -> int:
        if not self._free:
            raise PhysicalMemoryFullError("No free physical frames available")
        frame = self._free.popleft()
        self._used.add(frame)
        self.total_allocations += 1
        return frame

    def free(self, frame_number: int):
        if frame_number not in self._used:
            return
        self._used.discard(frame_number)
        self._free.append(frame_number)
        self.total_frees += 1

    def is_full(self) -> bool:
        return len(self._free) == 0

    @property
    def free_frames(self) -> int:
        return len(self._free)

    @property
    def used_frames(self) -> int:
        return len(self._used)

    def get_stats(self) -> dict:
        return {
            "num_frames":        self.num_frames,
            "free_frames":       self.free_frames,
            "used_frames":       self.used_frames,
            "total_allocations": self.total_allocations,
            "total_frees":       self.total_frees,
        }


class PhysicalMemoryFullError(Exception):
    pass


class PageTableEntry:
    __slots__ = ("frame_number", "valid", "dirty", "referenced", "vpn")

    def __init__(self, vpn: int, frame_number: int):
        self.vpn          = vpn
        self.frame_number = frame_number
        self.valid        = True
        self.dirty        = False
        self.referenced   = False

    def __repr__(self):
        return (f"PTE(vpn=0x{self.vpn:x}, frame={self.frame_number}, "
                f"valid={self.valid}, dirty={self.dirty})")


class PageTable:
    def __init__(self):
        self._entries: dict[int, PageTableEntry] = {}

    def lookup(self, vpn: int) -> "PageTableEntry | None":
        pte = self._entries.get(vpn)
        if pte is not None and pte.valid:
            pte.referenced = True
            return pte
        return None

    def map(self, vpn: int, frame_number: int) -> PageTableEntry:
        pte = self._entries.get(vpn)
        if pte is None:
            pte = PageTableEntry(vpn, frame_number)
            self._entries[vpn] = pte
        else:
            pte.frame_number = frame_number
            pte.valid        = True
            pte.referenced   = True
            pte.dirty        = False
        return pte

    def mark_dirty(self, vpn: int):
        pte = self._entries.get(vpn)
        if pte and pte.valid:
            pte.dirty = True

    def invalidate(self, vpn: int):
        pte = self._entries.get(vpn)
        if pte:
            pte.valid = False

    def get_valid_entries(self) -> list:
        return [p for p in self._entries.values() if p.valid]

    def get_all_entries(self) -> dict:
        return dict(self._entries)

    def __len__(self):
        return sum(1 for p in self._entries.values() if p.valid)


class VirtualMemorySubsystem:
    def __init__(self, vm_config: dict):
        self.page_size        = vm_config.get("page_size_bytes",    4096)
        num_frames            = vm_config.get("num_frames",         64)
        self.tlb_hit_lat      = vm_config.get("tlb_hit_latency",    1)
        self.page_walk_lat    = vm_config.get("page_walk_latency",  10)
        self.page_fault_lat   = vm_config.get("page_fault_latency", 50)
        policy                = vm_config.get("replacement_policy", "lru").lower()

        if policy not in ("fifo", "lru"):
            raise ValueError(f"Unknown replacement policy: {policy!r}. Use 'fifo' or 'lru'.")

        self.replacement_policy = policy
        self.page_offset_bits   = self.page_size.bit_length() - 1

        self.frame_allocator = FrameAllocator(num_frames)
        self.page_table      = PageTable()

        if policy == "fifo":
            self._fifo_queue: deque = deque()
        else:
            self._lru_order: OrderedDict = OrderedDict()

        self.stat_tlb_hits           = 0
        self.stat_tlb_misses         = 0
        self.stat_page_walks         = 0
        self.stat_page_faults        = 0
        self.stat_evictions          = 0
        self.stat_dirty_evictions    = 0
        self.stat_translation_cycles = 0

    def translate(self, vaddr: int, is_write: bool, tlb) -> tuple:
        vpn    = self._vpn(vaddr)
        offset = self._offset(vaddr)

        events = {
            "tlb_hit":        False,
            "tlb_miss":       False,
            "page_walk":      False,
            "page_fault":     False,
            "eviction":       False,
            "dirty_eviction": False,
        }
        penalty = self.tlb_hit_lat

        frame, hit = tlb.lookup(vpn)

        if hit:
            self.stat_tlb_hits += 1
            events["tlb_hit"] = True
            if is_write:
                self.page_table.mark_dirty(vpn)
            self._update_lru(vpn)

        else:
            self.stat_tlb_misses += 1
            events["tlb_miss"] = True

            pte = self.page_table.lookup(vpn)
            self.stat_page_walks += 1
            events["page_walk"] = True
            penalty += self.page_walk_lat

            if pte is None:
                self.stat_page_faults += 1
                events["page_fault"] = True
                penalty += self.page_fault_lat

                frame, evicted, dirty_ev = self._handle_page_fault(vpn, is_write)

                if evicted:
                    self.stat_evictions += 1
                    events["eviction"] = True
                if dirty_ev:
                    self.stat_dirty_evictions += 1
                    events["dirty_eviction"] = True
            else:
                frame = pte.frame_number
                if is_write:
                    self.page_table.mark_dirty(vpn)

            tlb.install(vpn, frame)
            self._update_lru(vpn)

        self.stat_translation_cycles += penalty
        paddr = (frame << self.page_offset_bits) | offset
        return paddr, penalty, events

    def _vpn(self, vaddr: int) -> int:
        return (vaddr & 0xFFFFFFFF) >> self.page_offset_bits

    def _offset(self, vaddr: int) -> int:
        return (vaddr & 0xFFFFFFFF) & (self.page_size - 1)

    def _handle_page_fault(self, vpn: int, is_write: bool) -> tuple:
        evicted     = False
        dirty_evict = False

        if self.frame_allocator.is_full():
            victim_vpn = self._choose_victim()
            victim_pte = self.page_table.get_all_entries().get(victim_vpn)

            dirty_evict = (victim_pte is not None and victim_pte.dirty)
            evicted     = True

            if victim_pte is not None:
                frame = victim_pte.frame_number
                self.page_table.invalidate(victim_vpn)
                self.frame_allocator.free(frame)
                self._remove_from_tracking(victim_vpn)

        frame = self.frame_allocator.allocate()
        pte   = self.page_table.map(vpn, frame)

        if is_write:
            pte.dirty = True

        self._add_to_tracking(vpn)
        return frame, evicted, dirty_evict

    def _choose_victim(self) -> int:
        if self.replacement_policy == "fifo":
            return self._fifo_victim()
        else:
            return self._lru_victim()

    def _fifo_victim(self) -> int:
        while self._fifo_queue:
            candidate = self._fifo_queue[0]
            pte = self.page_table.get_all_entries().get(candidate)
            if pte and pte.valid:
                return candidate
            self._fifo_queue.popleft()
        raise RuntimeError("FIFO: no valid victim found")

    def _lru_victim(self) -> int:
        for vpn in self._lru_order:
            pte = self.page_table.get_all_entries().get(vpn)
            if pte and pte.valid:
                return vpn
        raise RuntimeError("LRU: no valid victim found")

    def _add_to_tracking(self, vpn: int):
        if self.replacement_policy == "fifo":
            self._fifo_queue.append(vpn)
        else:
            self._lru_order[vpn] = None
            self._lru_order.move_to_end(vpn)

    def _remove_from_tracking(self, vpn: int):
        if self.replacement_policy == "fifo":
            try:
                self._fifo_queue.remove(vpn)
            except ValueError:
                pass
        else:
            self._lru_order.pop(vpn, None)

    def _update_lru(self, vpn: int):
        if self.replacement_policy == "lru" and vpn in self._lru_order:
            self._lru_order.move_to_end(vpn)

    def get_stats(self) -> dict:
        return {
            "tlb_hits":           self.stat_tlb_hits,
            "tlb_misses":         self.stat_tlb_misses,
            "page_walks":         self.stat_page_walks,
            "page_faults":        self.stat_page_faults,
            "evictions":          self.stat_evictions,
            "dirty_evictions":    self.stat_dirty_evictions,
            "translation_cycles": self.stat_translation_cycles,
            "frame_stats":        self.frame_allocator.get_stats(),
        }
