import sys
from config import Config
from parser import Parser
from cpu import Cpu
from pipeline import run_pipeline
from memory_system import MemorySystem

def main():
    print("Starting RISC-V Simulator with Cache Hierarchy (Phase 2)")

    if len(sys.argv) < 2:
        print("Usage: python main.py <assembly_file> [config_file]")
        return

    assembly_file = sys.argv[1]
    config_file = sys.argv[2] if len(sys.argv) > 2 else "config.txt"
    
    config = Config(config_file)

    print(f"Config loaded: Memory Size={config.memory_size} bytes, Forwarding={config.forwarding}")
    print(f"L1I Cache: {config.l1i_config}")
    print(f"L1D Cache: {config.l1d_config}")
    print(f"L2 Cache: {config.l2_config}")
    print(f"Main Memory Latency: {config.main_memory_latency} cycles")

    parser = Parser()
    try:
        instructions, data_memory, data_labels = parser.instr(assembly_file)
    except Exception as e:
        print(f"\nAssembly Parsing Error: {e}")
        return

    print(f"\nInstructions parsed: {len(instructions)}")

    memory_system = MemorySystem(
        config.l1i_config,
        config.l1d_config,
        config.l2_config,
        config.main_memory_latency,
        config.memory_size
    )

    cpu = Cpu(config.memory_size, memory_system)

    mem_array = memory_system.get_memory()
    for addr, val in data_memory.items():
        val &= 0xFFFFFFFF
        mem_array[addr % len(mem_array)] = val & 0xFF
        mem_array[(addr + 1) % len(mem_array)] = (val >> 8) & 0xFF
        mem_array[(addr + 2) % len(mem_array)] = (val >> 16) & 0xFF
        mem_array[(addr + 3) % len(mem_array)] = (val >> 24) & 0xFF

    pipeline_stats = run_pipeline(cpu, instructions, config, verbose=True)

    print("\n" + "="*60)
    print("FINAL SIMULATION RESULTS")
    print("="*60)
    
    print("\nFinal CPU state:")
    print(cpu)

    print("\nFirst 32 bytes of Data Memory (Starting at 1024):")
    
    data_words = []
    for i in range(1024, 1056, 4):
        val = int.from_bytes(mem_array[i:i+4], 'little')
        data_words.append(val)
    print(data_words)

    print("\n" + "="*60)
    print("CACHE STATISTICS")
    print("="*60)
    
    cache_stats = memory_system.get_stats()
    for cache_level in ["L1I", "L1D", "L2"]:
        stats = cache_stats[cache_level]
        print(f"\n{stats['name']} Cache:")
        print(f"  Total Accesses: {stats['total_accesses']}")
        print(f"  Cache Hits: {stats['cache_hits']}")
        print(f"  Cache Misses: {stats['cache_misses']}")
        print(f"  Hit Rate: {stats['hit_rate']:.4f} ({stats['hit_rate']*100:.2f}%)")
        print(f"  Miss Rate: {stats['miss_rate']:.4f} ({stats['miss_rate']*100:.2f}%)")
    
    print("\n" + "="*60)
    print("OVERALL PERFORMANCE METRICS")
    print("="*60)
    
    total_cycles = pipeline_stats['cycles']
    total_stalls = pipeline_stats['stalls']
    cache_stalls = pipeline_stats.get('cache_stalls', 0)
    if_stalls = pipeline_stats.get('if_stalls', 0)
    ipc = pipeline_stats['ipc']
    
    static_instructions = len(instructions)
    dynamic_instructions = int(ipc * total_cycles) if total_cycles > 0 else 0
    
    print(f"\nStatic Program Size: {static_instructions} instructions")
    print(f"Dynamically Executed: {dynamic_instructions} instructions")
    print(f"Total Cycles: {total_cycles}")
    print(f"Total Stalls: {total_stalls}")
    print(f"Cache-Related Stalls (data): {cache_stalls}")
    print(f"Instruction Fetch Stalls: {if_stalls}")
    print(f"IPC (Instructions Per Cycle): {ipc:.4f}")
    
    print("\nOverall Miss Rates:", memory_system.get_miss_rate())

if __name__ == "__main__":
    main()