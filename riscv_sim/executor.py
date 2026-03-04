def execute(cpu, instruction):

    if instruction.opcode == "ADD":
        val = cpu.read_reg(instruction.rs1) + cpu.read_reg(instruction.rs2)
        cpu.write_reg(instruction.rd, val)
        cpu.next_pc()

    elif instruction.opcode == "SUB":
        val = cpu.read_reg(instruction.rs1) - cpu.read_reg(instruction.rs2)
        cpu.write_reg(instruction.rd, val)
        cpu.next_pc()

    elif instruction.opcode == "ADDI":
        val = cpu.read_reg(instruction.rs1) + instruction.imm
        cpu.write_reg(instruction.rd, val)
        cpu.next_pc()

    elif instruction.opcode == "LW":
        addr = cpu.read_reg(instruction.rs1) + instruction.imm
        val = cpu.load(addr)
        cpu.write_reg(instruction.rd, val)
        cpu.next_pc()

    elif instruction.opcode == "SW":
        addr = cpu.read_reg(instruction.rs1) + instruction.imm
        val = cpu.read_reg(instruction.rd)
        cpu.store(addr, val)
        cpu.next_pc()

    elif instruction.opcode == "BEQ":
        cond = cpu.read_reg(instruction.rs1) == cpu.read_reg(instruction.rs2)
        cpu.branch(cond, instruction.target)

    elif instruction.opcode == "BNE":
        cond = cpu.read_reg(instruction.rs1) != cpu.read_reg(instruction.rs2)
        cpu.branch(cond, instruction.target)

    elif instruction.opcode == "JAL":
        cpu.write_reg(instruction.rd, cpu.pc + 4)
        cpu.jump(instruction.target)


def run_program(cpu, instructions):

    while cpu.pc < len(instructions) * 4:

        instr_index = cpu.pc // 4
        instr = instructions[instr_index]

        execute(cpu, instr)