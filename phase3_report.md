# Phase 3 Report

## 1. Design Overview

This phase extends the RISC-V simulator with a full virtual memory subsystem and a trace-replay execution mode.

### Components

| File | Role |
|---|---|
| `riscv_sim/trace_runner.py` | Parses `.trace` files; drives the in-order timing model |
| `riscv_sim/virtual_memory.py` | `VirtualMemorySubsystem`: flat page table, frame allocator, FIFO/LRU page replacement |
| `riscv_sim/tlb.py` | Fully-associative data TLB with FIFO or LRU replacement |
| `riscv_sim/memory_system.py` | Wires TLB → VM → L1D cache (PIPT ordering); accumulates stats |
| `riscv_sim/config.py` | Reads INI config; exposes `get_vm_config()` and `get_tlb_config()` |
| `config_phase3.ini` | The config file used for all Phase 3 runs |

### Execution Model

The trace runner maintains a simple 32-register file and steps through each trace instruction in order:

- **L / S** — call `MemorySystem.access(vaddr, 'LOAD'|'STORE')`.  
  The memory system first translates the virtual address through the VM subsystem (TLB → page table walk → page fault as needed), then accesses the physical-address cache hierarchy.  
  Latency = VM-translation penalty + L1D cache latency (+ DRAM latency on L1D miss).  
  Stall cycles per instruction = max(0, latency − 1).

- **ADD** — latency 1 cycle; 0 stall cycles.

- **MUL** — latency 3 cycles; 2 stall cycles.

### Virtual Memory Subsystem

- 32-bit virtual addresses, 4 KB pages, flat one-level page table.
- `FrameAllocator` manages all physical frames from a free list.
- On a TLB miss: the page table is walked (page-walk latency charged).
- On a page fault (VPN not mapped): frame allocated, page-fault latency charged.
- On physical memory full: victim selected by **FIFO** or **LRU**; frame freed, page-table entry invalidated, **and the victim's stale TLB entry is invalidated (TLB shootdown)**.
- Dirty pages are tracked via the dirty bit in the page-table entry; dirty evictions trigger a writeback count.

### Cache Hierarchy (PIPT)

Physical address translation is completed before any cache lookup, ensuring correct PIPT semantics.

- L1D: 4 KB, direct-mapped (associativity = 1), 64-byte blocks, latency = 1 cycle.
- L1I: same configuration (not exercised in trace-replay mode; zero accesses).
- L2: disabled (`L2_enabled = false`) as per Phase 3 requirements.
- DRAM: 100-cycle latency (charged on L1D miss).

### Translation Latency Model

| Event | Cycles charged |
|---|---|
| TLB hit | +1 (tlb_hit_latency) |
| TLB miss → page walk (mapping found) | +1 + 10 |
| TLB miss → page walk → page fault | +1 + 10 + 50 |

"Total translation penalty" = sum of all per-access latencies above.

---

## 2. Changes from Phase 2

- Added `riscv_sim/trace_runner.py` for trace-replay mode.
- Added `riscv_sim/virtual_memory.py`: `FrameAllocator`, `PageTable`, `PageTableEntry`, `VirtualMemorySubsystem`.
- Added `riscv_sim/tlb.py`: fully-associative `TLB` with FIFO/LRU replacement.
- Extended `riscv_sim/memory_system.py`: wires VM + TLB into `access()`; exposes `get_vm_stats()`.
- Extended `riscv_sim/config.py`: INI parser for `[memory]` and `[vm]` sections.
- Added `config_phase3.ini` with all Phase 3 parameters.
- **Bug fix**: added TLB shootdown on page eviction — when a physical frame is reclaimed, the stale TLB entry for the evicted VPN is now explicitly invalidated. Without this, subsequent accesses to the evicted VPN would incorrectly hit the TLB and receive the wrong (now reused) physical frame number.

---

## 3. Trace Format

Trace files are in `riscv_sim/phase3_traces/trace01.trace` … `trace10.trace`.

Each non-blank, non-comment line is one instruction:

```
L 0x10000000 x5      ; load from virtual address into dest reg
S 0x10004000 x6      ; store src reg value to virtual address
ADD x7 x5 x6         ; integer add, latency 1
MUL x8 x7 x9         ; integer multiply, latency 3
```

Comments start with `;`. Virtual addresses are 32-bit hex.

---

## 4. Configuration Used for Reporting

```ini
[pipeline]
forwarding_enabled = true

[latencies]
ADD = 1
MUL = 3

[memory]
virtual_size_bytes  = 536870912   ; 512 MB virtual
physical_size_bytes = 262144      ; 64 frames * 4096 = 256 KB physical
page_size_bytes     = 4096        ; 4 KB pages

[cache]
L1D_Size              = 4096      ; 4 KB, direct-mapped
L1D_BlockSize         = 64
L1D_Associativity     = 1
L1D_Latency           = 1
L1D_ReplacementPolicy = LRU
L2_enabled            = false     ; no L2

MainMemory_Latency    = 100

[vm]
dtlb_entries        = 16
tlb_hit_latency     = 1
page_walk_latency   = 10
page_fault_latency  = 50
replacement_policy  = lru
```

---

## 5. Results

Command used:
```
python riscv_sim/trace_runner.py riscv_sim/phase3_traces/traceXX.trace config_phase3.ini
```

| Trace | Cycles | Retired | IPC | Stalls | TLB Hits | TLB Misses | Page Walks | Page Faults | Evictions | Dirty Evictions | Translation Cycles |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 01 | 37,218,128 | 715,724 | 0.0192 | 36,502,404 | 357,854 | 8 | 8 | 8 | 0 | 0 | 358,342 |
| 02 | 37,217,568 | 715,704 | 0.0192 | 36,501,864 | 357,836 | 16 | 16 | 16 | 0 | 0 | 358,812 |
| 03 | 40,798,714 | 715,752 | 0.0175 | 40,082,962 | 0 | 357,876 | 357,876 | 17 | 0 | 0 | 3,937,486 |
| 04 | 37,885,236 | 715,728 | 0.0189 | 37,169,508 | 178,516 | 179,348 | 179,348 | 32 | 0 | 0 | 2,152,944 |
| 05 | 40,661,424 | 715,732 | 0.0176 | 39,945,692 | 13,010 | 344,856 | 344,856 | 64 | 0 | 0 | 3,809,626 |
| 06 | 22,909,696 | 715,728 | 0.0312 | 22,193,968 | 0 | 357,864 | 357,864 | 357,864 | 357,800 | 107,798 | 21,829,704 |
| 07 | 41,029,552 | 715,736 | 0.0174 | 40,313,816 | 208,880 | 148,988 | 148,988 | 59,900 | 59,836 | 57,100 | 4,842,748 |
| 08 | 22,910,080 | 715,740 | 0.0312 | 22,194,340 | 0 | 357,870 | 357,870 | 357,870 | 357,806 | 71,269 | 21,830,070 |
| 09 | 58,691,664 | 715,752 | 0.0122 | 57,975,912 | 0 | 357,876 | 357,876 | 357,876 | 357,812 | 125,515 | 21,830,436 |
| 10 | 36,268,754 | 715,712 | 0.0197 | 35,553,042 | 285,083 | 72,773 | 72,773 | 1,716 | 1,652 | 1,652 | 1,171,386 |

---

## 6. Observations

- **Memory-bound workload**: IPC values are uniformly very low (0.012–0.031) because nearly every load/store incurs a multi-cycle translation penalty plus an L1D cache miss reaching DRAM.

- **Traces 01–02** show excellent TLB locality: only 8–16 unique pages are touched, fitting entirely in 64 physical frames. All subsequent accesses hit the TLB. Translation penalty is minimal.

- **Traces 03 and 05** stream through a large virtual address space with very poor spatial locality; the 16-entry TLB is thrashed. Almost every L/S is a TLB miss and page walk. However, the working set still fits in 64 frames, so no evictions occur.

- **Traces 06, 08, 09** are the worst cases: the working set exceeds physical memory. Nearly every load/store causes a page fault and an eviction, generating ~21.8 M translation penalty cycles each. Trace 09 is slightly slower because its DRAM accesses pile onto the eviction cost.

- **Trace 07** sits in between: significant evictions (59,836) with high dirty eviction rate (57,100), but the TLB retains partial locality (208,880 hits).

- **Trace 10** has the best TLB performance of all high-eviction traces: 285,083 TLB hits and only 1,716 page faults, yielding the lowest translation penalty among traces with evictions.

- The **TLB shootdown fix** ensures correctness when evicted pages are later re-accessed: the simulator now correctly generates a new page fault rather than silently reusing a stale TLB mapping that points to a recycled frame.

---

### Notes

- Run from the `COA/` directory:  
  `python riscv_sim/trace_runner.py riscv_sim/phase3_traces/traceXX.trace config_phase3.ini`
- The replacement policy is `lru` throughout, as required.
- L2 cache is disabled; DRAM latency = 100 cycles.
