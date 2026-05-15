# Phase 3 Report

## 1. Design Overview

This phase builds on the existing RISC-V simulator by replaying instruction traces through the memory subsystem and collecting timing and VM statistics.

- `riscv_sim/trace_runner.py` parses `.trace` files and simulates each instruction.
- The simulator uses `MemorySystem.access()` for all loads/stores, so every virtual memory access is translated through the VM subsystem and cached by L1/L2 as configured.
- `Config` provides VM and TLB configuration, plus instruction latencies for `ADD` and `MUL`.
- The trace runner maintains a simple register file (`regs[0..31]`), applies integer semantics for `ADD` and `MUL`, and tracks cycles, retired instructions, and stall cycles.
- VM statistics are obtained from `mem.get_vm_stats()`, and cache statistics are obtained from `mem.get_stats()`.

## 2. Changes from Phase 2

- Added `riscv_sim/trace_runner.py` to replay full `.trace` instruction traces.
- Integrated pipeline timing for `ADD` and `MUL` using latencies from `Config`.
- Implemented memory-access timing for `LOAD` and `STORE` through `MemorySystem.access()`.
- Collected detailed statistics including IPC, stalls, TLB hits/misses, page walks, page faults, evictions, and translation penalty.
- Added a results-printing summary for VM and cache statistics.

## 3. Trace Format

The trace files are located in `riscv_sim/phase3_traces/trace01.trace` through `trace10.trace`.

Each line is one instruction:

- `L 0x10000000 x5` — load from virtual address into destination register
- `S 0x10004000 x6` — store source register value to virtual address
- `ADD x7 x5 x6` — integer add with latency 1
- `MUL x8 x7 x9` — integer multiply with latency 3

Comments and blank lines are ignored.

## 4. Results Table

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

## 5. Observations

- The workload is heavily memory-bound. IPC values are very low due to long memory access latencies and VM translation penalties.
- Traces 06, 08, and 09 show the most severe page-fault and eviction behavior: they exercised nearly all page frames and generated almost one page fault per load/store.
- Trace 10 has the best overall TLB performance, with 285,083 hits and only 72,773 misses, producing a much lower translation penalty than the worst traces.
- Traces 03 and 05 also show extremely poor TLB locality, with nearly every access missing in the TLB.
- L1D cache behavior is mostly cold for many traces; only trace 04 and trace 10 show nonzero L1D cache hits with the current configuration.

---

### Notes

- The simulator was executed from `COA` using:
  - `python riscv_sim/trace_runner.py riscv_sim/phase3_traces/traceXX.trace config_phase3.ini`
- `trace_runner.py` does not modify the existing VM, TLB, memory, or config modules.
