class PipelineCpu:

```
def __init__(self, cpu, config, instructions, stats):
    self.cpu = cpu
    self.config = config
    self.instructions = instructions
    self.stats = stats

    self.IF = None
    self.ID = None
    self.EX = None
    self.MEM = None
    self.WB = None

    self.halted = False


def step(self):
    """Execute one pipeline cycle"""

    # count cycle
    self.stats.inc_cycle()

    # ----- WRITE BACK -----
    if self.WB is not None:
        self.stats.inc_instruction()

    # ----- SHIFT PIPELINE -----
    self.WB = self.MEM
    self.MEM = self.EX
    self.EX = self.ID
    self.ID = self.IF
    self.IF = None

    # ----- FETCH STAGE -----
    if self.cpu.pc < len(self.instructions):
        self.IF = self.instructions[self.cpu.pc]
        self.cpu.pc += 1


def execute_stage(self):
    """Execute instruction currently in EX stage"""

    instr = self.EX
    if instr is None:
        return

    op = instr.opcode

    if op == "ADD":
        val = self.cpu.read_reg(instr.rs1) + self.cpu.read_reg(instr.rs2)
        self.cpu.write_reg(instr.rd, val)

    elif op == "SUB":
        val = self.cpu.read_reg(instr.rs1) - self.cpu.read_reg(instr.rs2)
        self.cpu.write_reg(instr.rd, val)

    elif op == "ADDI":
        val = self.cpu.read_reg(instr.rs1) + instr.imm
        self.cpu.write_reg(instr.rd, val)

    elif op == "LW":
        addr = self.cpu.read_reg(instr.rs1) + instr.imm
        val = self.cpu.load(addr)
        self.cpu.write_reg(instr.rd, val)

    elif op == "SW":
        addr = self.cpu.read_reg(instr.rs1) + instr.imm
        val = self.cpu.read_reg(instr.rd)
        self.cpu.store(addr, val)

    elif op == "BEQ":
        if self.cpu.read_reg(instr.rs1) == self.cpu.read_reg(instr.rs2):
            self.cpu.pc = instr.target

    elif op == "BNE":
        if self.cpu.read_reg(instr.rs1) != self.cpu.read_reg(instr.rs2):
            self.cpu.pc = instr.target

    elif op == "JAL":
        self.cpu.write_reg(instr.rd, self.cpu.pc)
        self.cpu.pc = instr.target


def run(self):

    while not self.halted:

        self.execute_stage()
        self.step()

        # stop condition
        if (
            self.cpu.pc >= len(self.instructions)
            and self.IF is None
            and self.ID is None
            and self.EX is None
            and self.MEM is None
            and self.WB is None
        ):
            self.halted = True
```
