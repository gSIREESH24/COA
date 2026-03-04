import sys
from parser import Parser
from cpu import Cpu
from executor import run_program


def main():

    print("Starting RISC-V Simulator")

    if len(sys.argv) < 2:
        print("Usage: python main.py <assembly_file>")
        return

    assembly_file = sys.argv[1]

    parser = Parser()
    instructions = parser.instr(assembly_file)

    print("Instructions parsed:", len(instructions))

    cpu = Cpu()

    run_program(cpu, instructions)

    print("\nFinal CPU state:")
    print(cpu)

    print("\nFirst 32 bytes of memory:")
    print(list(cpu.memory[:32]))


if __name__ == "__main__":
    main()