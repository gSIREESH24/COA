import sys
from config import Config
from memory_system import MemorySystem
from tlb import TLB

def parse_trace(filepath):
    instructions = []
    with open(filepath) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith(';'):
                continue
            parts = line.split()
            instructions.append(parts)
    return instructions

def run_trace(trace_file, config_file):
    cfg = Config(config_file)

    mem = MemorySystem(
        cfg.l1i_config, cfg.l1d_config, cfg.l2_config,
        cfg.main_memory_latency, cfg.memory_size,
        vm_config=cfg.get_vm_config(),
        tlb_config=cfg.get_tlb_config(),
        l2_enabled=cfg.l2_enabled
    )

    regs = [0] * 32       # x0..x31
    cycle = 0
    instructions_retired = 0
    stall_cycles = 0

    for parts in parse_trace(trace_file):
        op = parts[0]

        if op == 'L':
            vaddr   = int(parts[1], 16)
            rd      = int(parts[2][1:])           # "x5" → 5
            lat, _  = mem.access(vaddr, 'LOAD')   # lat includes VM penalty
            regs[rd] = 0                           # value not simulated
            cycle   += lat
            stall_cycles += max(0, lat - 1)

        elif op == 'S':
            vaddr   = int(parts[1], 16)
            rs      = int(parts[2][1:])
            lat, _  = mem.access(vaddr, 'STORE', regs[rs])
            cycle   += lat
            stall_cycles += max(0, lat - 1)

        elif op == 'ADD':
            rd  = int(parts[1][1:])
            rs1 = int(parts[2][1:])
            rs2 = int(parts[3][1:])
            regs[rd] = (regs[rs1] + regs[rs2]) & 0xFFFFFFFF
            cycle += cfg.get_latency('ADD')       # = 1

        elif op == 'MUL':
            rd  = int(parts[1][1:])
            rs1 = int(parts[2][1:])
            rs2 = int(parts[3][1:])
            regs[rd] = (regs[rs1] * regs[rs2]) & 0xFFFFFFFF
            lat = cfg.get_latency('MUL')          # = 3
            cycle += lat
            stall_cycles += lat - 1

        instructions_retired += 1

    ipc = instructions_retired / cycle if cycle > 0 else 0
    vm  = mem.get_vm_stats()

    print_stats(cycle, instructions_retired, ipc, stall_cycles, vm, mem)

def print_stats(cycles, retired, ipc, stalls, vm, mem):
    print("=" * 55)
    print("PHASE 3 SIMULATION RESULTS")
    print("=" * 55)
    print(f"Total Cycles              : {cycles}")
    print(f"Instructions Retired      : {retired}")
    print(f"IPC                       : {ipc:.4f}")
    print(f"Stall Cycles              : {stalls}")
    print()
    print(f"TLB Hits                  : {vm.get('tlb_hits', 0)}")
    print(f"TLB Misses                : {vm.get('tlb_misses', 0)}")
    print(f"Page Walks                : {vm.get('page_walks', 0)}")
    print(f"Page Faults               : {vm.get('page_faults', 0)}")
    print(f"Page Evictions            : {vm.get('evictions', 0)}")
    print(f"Dirty Evictions/Writebacks: {vm.get('dirty_evictions', 0)}")
    print(f"Total Translation Penalty : {vm.get('translation_cycles', 0)} cycles")
    print()
    fs = vm.get('frame_stats', {})
    print(f"Physical Frames Used      : {fs.get('used_frames', '?')} / {fs.get('num_frames', '?')}")
    print()
    cache = mem.get_stats()
    for name in ['L1I', 'L1D', 'L2']:
        s = cache[name]
        print(f"{name}: accesses={s['total_accesses']}  hits={s['cache_hits']}  "
              f"misses={s['cache_misses']}  hit_rate={s['hit_rate']:.3f}")

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python trace_runner.py <trace_file> <config_file>")
        sys.exit(1)
    run_trace(sys.argv[1], sys.argv[2])