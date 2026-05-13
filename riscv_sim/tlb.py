from collections import OrderedDict, deque


class TLBEntry:
    __slots__ = ("vpn", "frame_number", "valid")

    def __init__(self, vpn: int, frame_number: int):
        self.vpn          = vpn
        self.frame_number = frame_number
        self.valid        = True

    def __repr__(self):
        return f"TLBEntry(vpn=0x{self.vpn:x}, frame={self.frame_number})"


class TLB:
    def __init__(self, num_entries: int = 16, replacement_policy: str = "lru"):
        if num_entries <= 0:
            raise ValueError("num_entries must be positive")

        self.num_entries        = num_entries
        self.replacement_policy = replacement_policy.lower()

        if self.replacement_policy not in ("fifo", "lru"):
            raise ValueError(f"Unknown TLB replacement policy: {replacement_policy!r}")

        self._entries: dict[int, TLBEntry] = {}

        if self.replacement_policy == "fifo":
            self._order: deque = deque()
        else:
            self._order: OrderedDict = OrderedDict()

        self.stat_hits          = 0
        self.stat_misses        = 0
        self.stat_evictions     = 0
        self.stat_invalidations = 0

    def lookup(self, vpn: int) -> tuple:
        entry = self._entries.get(vpn)
        if entry and entry.valid:
            self.stat_hits += 1
            self._touch(vpn)
            return entry.frame_number, True
        self.stat_misses += 1
        return None, False

    def install(self, vpn: int, frame_number: int):
        if vpn in self._entries:
            self._entries[vpn].frame_number = frame_number
            self._entries[vpn].valid        = True
            self._touch(vpn)
            return

        if len(self._entries) >= self.num_entries:
            self._evict()

        entry = TLBEntry(vpn, frame_number)
        self._entries[vpn] = entry
        self._add_to_order(vpn)

    def invalidate(self, vpn: int):
        if vpn in self._entries:
            del self._entries[vpn]
            self._remove_from_order(vpn)
            self.stat_invalidations += 1

    def flush(self):
        self._entries.clear()
        self._order.clear()
        self.stat_invalidations += 1

    def _evict(self):
        victim_vpn = self._pick_victim()
        del self._entries[victim_vpn]
        self._remove_from_order(victim_vpn)
        self.stat_evictions += 1

    def _pick_victim(self) -> int:
        if self.replacement_policy == "fifo":
            return self._order[0]
        else:
            return next(iter(self._order))

    def _touch(self, vpn: int):
        if self.replacement_policy == "lru":
            if vpn in self._order:
                self._order.move_to_end(vpn)

    def _add_to_order(self, vpn: int):
        if self.replacement_policy == "fifo":
            self._order.append(vpn)
        else:
            self._order[vpn] = None
            self._order.move_to_end(vpn)

    def _remove_from_order(self, vpn: int):
        if self.replacement_policy == "fifo":
            try:
                self._order.remove(vpn)
            except ValueError:
                pass
        else:
            self._order.pop(vpn, None)

    def get_stats(self) -> dict:
        total     = self.stat_hits + self.stat_misses
        hit_rate  = self.stat_hits  / total if total else 0.0
        miss_rate = self.stat_misses / total if total else 0.0
        return {
            "num_entries":   self.num_entries,
            "policy":        self.replacement_policy,
            "tlb_hits":      self.stat_hits,
            "tlb_misses":    self.stat_misses,
            "tlb_evictions": self.stat_evictions,
            "invalidations": self.stat_invalidations,
            "hit_rate":      hit_rate,
            "miss_rate":     miss_rate,
            "current_size":  len(self._entries),
        }

    def __len__(self):
        return len(self._entries)

    def __repr__(self):
        return f"TLB(entries={self.num_entries}, policy={self.replacement_policy}, used={len(self)})"
