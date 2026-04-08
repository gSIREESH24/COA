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

    try:
        config = Config(config_file)
    except FileNotFoundError:
        print(f"Config file '{config_file}' not found.")
        return

    print(f"Config loaded: Memory Size={config.memory_size} bytes, Forwarding={config.forwarding}")
    print(f"L1I Cache: {config.l1i_config}")
    print(f"L1D Cache: {config.l1d_config}")
    print(f"L2 Cache: {config.l2_config}")
    print(f"Main Memory Latency: {config.main_memory_latency} cycles")

    parser = Parser()
    instructions, data_memory, data_labels = parser.instr(assembly_file)

    print(f"\nInstructions parsed: {len(instructions)}")
    print(f"Data words parsed: {len(data_memory)}")

    memory_system = MemorySystem(
        config.l1i_config,
        config.l1d_config,
        config.l2_config,
        main_memory_latency=config.main_memory_latency,
        memory_size=config.memory_size,
    )

    memory_system.load_program(instructions, data_memory)

    cpu = Cpu(config.memory_size, memory_system)

    pipeline_stats = run_pipeline(cpu, instructions, config, verbose=True)

    print("\n" + "=" * 60)
    print("FINAL SIMULATION RESULTS")
    print("=" * 60)

    print("\nFinal CPU state:")
    print(cpu)

    print("\nFirst 32 bytes of memory:")
    print(list(memory_system.get_memory()[:32]))

    print("\n" + "=" * 60)
    print("CACHE STATISTICS")
    print("=" * 60)

    cache_stats = memory_system.get_stats()

    for cache_level in ["L1I", "L1D", "L2"]:
        stats = cache_stats[cache_level]
        print(f"\n{stats['name']} Cache:")
        print(f"  Total Accesses: {stats['total_accesses']}")
        print(f"  Cache Hits: {stats['cache_hits']}")
        print(f"  Cache Misses: {stats['cache_misses']}")
        print(f"  Hit Rate: {stats['hit_rate']:.4f} ({stats['hit_rate'] * 100:.2f}%)")
        print(f"  Miss Rate: {stats['miss_rate']:.4f} ({stats['miss_rate'] * 100:.2f}%)")

    print("\n" + "=" * 60)
    print("OVERALL PERFORMANCE METRICS")
    print("=" * 60)

    total_instructions = len(instructions)
    total_cycles = pipeline_stats["cycles"]
    total_stalls = pipeline_stats["stalls"]
    cache_stalls = pipeline_stats.get("cache_stalls", 0)
    if_stalls = pipeline_stats.get("if_stalls", 0)

    ipc = total_instructions / total_cycles if total_cycles > 0 else 0

    print(f"\nTotal Instructions: {total_instructions}")
    print(f"Total Cycles: {total_cycles}")
    print(f"Total Stalls: {total_stalls}")
    print(f"Cache-Related Stalls (data): {cache_stalls}")
    print(f"Instruction Fetch Stalls: {if_stalls}")
    print(f"IPC (Instructions Per Cycle): {ipc:.4f}")

    print("\nCache Miss Rate:", cpu.memory_system.get_miss_rate())


if __name__ == "__main__":
    main()