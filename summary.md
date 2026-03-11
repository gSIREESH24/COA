# RISC-V Simulator - Complete Code Documentation

## Table of Contents
1. [Project Overview](#project-overview)
2. [Architecture Overview](#architecture-overview)
3. [Module Breakdown](#module-breakdown)
4. [Data Flow & Examples](#data-flow--examples)
5. [Pipeline Architecture](#pipeline-architecture)
6. [Execution Examples](#execution-examples)

---

## Project Overview

This is a **RISC-V Instruction Set Architecture (ISA) Simulator** that can execute RISC-V assembly programs in two modes:
- **Non-Pipelined Mode**: Sequential execution (one instruction at a time)
- **Pipelined Mode**: 5-stage pipeline execution with optional data forwarding

### Supported Instructions
- **Arithmetic (R-Type)**: `ADD`, `SUB`
- **Immediate (I-Type)**: `ADDI`, `SLLI` (Shift Left Logical Immediate)
- **Memory**: `LW` (Load Word), `SW` (Store Word)
- **Branch**: `BEQ` (Equal), `BNE` (Not Equal), `BGE` (Greater/Equal), `BLE` (Less/Equal)
- **Jump**: `JAL` (Jump and Link)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    RISC-V SIMULATOR                     │
├─────────────────────────────────────────────────────────┤
│  INPUT: Assembly File (.asm)                            │
│         Config File (Latencies, Forwarding)             │
├─────────────────────────────────────────────────────────┤
│  PARSER → Converts assembly to Instruction objects      │
│  CPU → Manages registers, memory, PC                    │
│  EXECUTOR → Executes instructions (non-pipelined)       │
│  PIPELINE → 5-stage pipeline execution (IF-ID-EX-MEM-WB)│
├─────────────────────────────────────────────────────────┤
│  OUTPUT: Final register/memory state, execution stats   │
└─────────────────────────────────────────────────────────┘
```

---

## Module Breakdown

### 1. **config.py** - Configuration Manager

**Purpose**: Loads and manages simulator configuration parameters.

**Key Features**:
- Memory size
- Forwarding enabled/disabled flag
- Instruction latencies

**Configuration File Example (`config_file.txt`)**:
```
MemorySize=4096
Forwarding=false

Latency_ADD=1
Latency_SUB=1
Latency_ADDI=1
Latency_LW=2
Latency_SW=1
Latency_BNE=1
Latency_BEQ=1
```

**Class: `Config`**
```python
class Config:
    memory_size: int          # Total memory in bytes
    forwarding: bool          # Enable/disable data forwarding
    latency: dict            # Instruction latency in cycles
    
    get_latency(instruction): int  # Returns cycles needed for instruction
```

**Example Usage**:
```python
config = Config("config_file.txt")
print(config.memory_size)        # 4096
print(config.forwarding)         # False
print(config.get_latency("ADD")) # 1
```

---

### 2. **parser.py** - Assembly Parser

**Purpose**: Converts RISC-V assembly code into `Instruction` objects and manages labels/data.

**Class: `Instruction`**
```python
class Instruction:
    opcode: str      # e.g., "ADD", "ADDI", "LW"
    rd: int          # Destination register (0-31)
    rs1: int         # Source register 1 (0-31)
    rs2: int         # Source register 2 (0-31)
    imm: int         # Immediate value
    target: int      # Branch/Jump target address
```

**Parsing Process** (Two-Pass):

**Pass 1**: Read assembly file, separate `.data` and `.text` sections, collect labels
- `.data` section: Variables stored in memory starting at address 1024
- `.text` section: Instructions parsed and labels collected
- Labels map to instruction addresses

**Pass 2**: Convert assembly instructions to `Instruction` objects

**Instruction Types Parsed**:

| Type | Example | Parsing |
|------|---------|---------|
| R-Type | `ADD x1, x2, x3` | Extract rd, rs1, rs2 |
| I-Type | `ADDI x1, x1, 100` | Extract rd, rs1, immediate |
| Load | `LW x1, 0(x2)` | Extract rd, offset, rs1 |
| Store | `SW x1, 0(x2)` | Extract rs and base register, offset |
| Branch | `BEQ x1, x2, LOOP` | Extract rs1, rs2, target label |
| Jump | `JAL x1, START` | Extract rd, target label |

**Example Parsing**:
```assembly
.data
    array: .word 10, 20, 30

.text
    ADDI x1, x0, 5    # x1 = 5
    ADD x2, x1, x1    # x2 = 10
```

**Parsed Result**:
```
instructions = [
    Instruction(opcode="ADDI", rd=1, rs1=0, imm=5),
    Instruction(opcode="ADD", rd=2, rs1=1, rs2=1)
]
data_memory = {1024: 10, 1028: 20, 1032: 30}
```

---

### 3. **cpu.py** - CPU State Management

**Purpose**: Represents the processor's internal state (registers, memory, program counter).

**Class: `Cpu`**
```python
class Cpu:
    registers: list[int]     # 32 general-purpose registers (x0-x31)
    memory: bytearray        # Main memory (default 4096 bytes)
    pc: int                  # Program counter
```

**Key Methods**:

| Method | Purpose |
|--------|---------|
| `read_reg(reg_num)` | Read register value (x0 always returns 0) |
| `write_reg(reg_num, value)` | Write to register (x0 cannot be written) |
| `load(address)` | Load 32-bit word from memory at address |
| `store(address, value)` | Store 32-bit word to memory at address |
| `next_pc()` | Increment PC by 4 (next instruction) |
| `jump(target)` | Set PC to target address |
| `branch(condition, target)` | Jump if condition is true, else next_pc() |

**Memory Organization**:
```
Address Range    Purpose
0-1023          Instructions (not directly addressed)
1024+           Data segment (variables, arrays)
```

**Example**:
```python
cpu = Cpu(memory_size=4096)

# Write values to registers
cpu.write_reg(1, 10)         # x1 = 10
cpu.write_reg(2, 20)         # x2 = 20
print(cpu.read_reg(1))       # 10

# Store and load from memory
cpu.store(1024, 100)         # Store 100 at address 1024
value = cpu.load(1024)       # Load from address 1024 → 100

# Program counter
cpu.pc = 0
cpu.next_pc()               # pc = 4
cpu.jump(12)                # pc = 12
```

---

### 4. **executor.py** - Non-Pipelined Executor

**Purpose**: Executes instructions sequentially without pipelining.

**Main Function**: `execute(cpu, instruction)`

**Execution Logic for Each Instruction**:

| Instruction | Operation | Example |
|------------|-----------|---------|
| `ADD rd, rs1, rs2` | rd = rs1 + rs2 | `ADD x1, x2, x3` → x1 = x2 + x3 |
| `SUB rd, rs1, rs2` | rd = rs1 - rs2 | `SUB x1, x2, x3` → x1 = x2 - x3 |
| `ADDI rd, rs1, imm` | rd = rs1 + imm | `ADDI x1, x2, 5` → x1 = x2 + 5 |
| `LW rd, offset(rs1)` | rd = memory[rs1 + offset] | `LW x1, 0(x2)` → x1 = memory[x2] |
| `SW rs, offset(rs1)` | memory[rs1 + offset] = rs | `SW x1, 0(x2)` → memory[x2] = x1 |
| `BEQ rs1, rs2, target` | if (rs1 == rs2) PC = target | Branch if equal |
| `BNE rs1, rs2, target` | if (rs1 ≠ rs2) PC = target | Branch if not equal |
| `JAL rd, target` | rd = PC + 4; PC = target | Jump and link (return address in rd) |

**Execution Flow**:
```
1. Fetch instruction at PC/4
2. Decode and extract operands
3. Execute operation (ALU, Memory, Branch)
4. Update PC (next_pc or jump/branch)
5. Repeat until PC >= last instruction
```

**Example Execution** (Simple ADD):
```python
# Instruction: ADD x1, x2, x3
# Before: x2=10, x3=20, PC=0
# After: x1=30, PC=4

instruction = Instruction(opcode="ADD", rd=1, rs1=2, rs2=3)
execute(cpu, instruction)
```

---

### 5. **pipeline.py** - 5-Stage Pipeline Executor

**Purpose**: Implements a classic 5-stage RISC pipeline with hazard detection and optional forwarding.

#### Pipeline Stages

```
┌──────┐     ┌──────┐     ┌──────┐     ┌──────┐     ┌──────┐
│ IF   │────→│ ID   │────→│ EX   │────→│ MEM  │────→│ WB   │
│Fetch │     │Decode│     │Execute│    │Memory│     │Write │
└──────┘     └──────┘     └──────┘     └──────┘     └──────┘
  Fetch      Decode      ALU/Shift    Load/Store   Register
            Register     Operation    Operation     Update
         Dependency Check
```

**Stage Details**:

| Stage | Cycle | Operation |
|-------|-------|-----------|
| **IF** (Instruction Fetch) | -4 | Fetch next instruction from memory |
| **ID** (Instruction Decode) | -3 | Decode instruction, read registers, check hazards, branch resolution |
| **EX** (Execute) | -2 | ALU operations, address calculation, respects latency |
| **MEM** (Memory) | -1 | Load/Store operations |
| **WB** (Write Back) | 0 | Write results to registers |

#### Hazard Detection & Resolution

**1. Data Hazards (RAW - Read After Write)**

**Problem**: Instruction needs data from previous instruction that hasn't finished

**Example**:
```assembly
ADDI x1, x0, 5      # x1 = 5
ADD x2, x1, x3      # x2 = x1 + x3
                    # x1 not ready yet!
```

**Solutions**:
- **Forwarding (Data Forwarding)**: Pass data directly between stages
- **Stalling**: Insert wait cycles

**Without Forwarding**:
```
Cycle  IF      ID      EX      MEM     WB
1      ADDI    -       -       -       -
2      ADD     ADDI    -       -       -
3      -       STALL   ADDI    -       -      ← Wait, ADDI not done
4      -       ADD     EX→      ADDI    -
5      -       -       MEM→    EX→      ADDI
6      -       -       -       MEM→    EX→
7      -       -       -       -       MEM→
```

**With Forwarding**:
```
Cycle  IF      ID      EX      MEM     WB
1      ADDI    -       -       -       -
2      ADD     ADDI    -       -       -
3      instr3  ADD(fwd)ADDI    -       -      ← Use data directly
4      instr4  -       EX→      ADDI    -
```

**2. Load-Use Hazard**

**Special case**: LW (Load Word) output not ready until MEM stage

```assembly
LW x1, 0(x2)    # x1 = memory[x2], ready in MEM stage
ADD x3, x1, x4  # Needs x1 now!
```

**Resolution**: 1-cycle stall needed (forwarding from MEM won't help)

**3. Branch Dependencies**

**Problem**: Branch instruction needs register values that are still being computed

```assembly
ADDI x1, x0, 10
BEQ x1, x2, LOOP    # x1 still computing
```

**Resolution**: Stall until dependencies resolved

**4. Execution Unit Latency**

**Problem**: Some instructions take multiple cycles (e.g., LW takes 2 cycles)

**Example** with LW latency=2:
```assembly
LW x1, 0(x2)    # Cycle 0-1: EX stage takes 2 cycles
ADD x3, x1, x4  # Blocked until LW finishes
```

#### Forwarding Logic

**When enabled** (`config.forwarding = true`):

```python
def forward_value(reg, ex_mem, mem_wb):
    """
    Check if a register value can be forwarded from previous stages.
    Returns (can_forward, value) tuple.
    """
    
    # Check EX→MEM stage (just finished ALU)
    if ex_mem and will_write_rd(ex_mem["instr"]):
        if ex_mem["instr"].rd == reg:
            return True, ex_mem["alu"]
    
    # Check MEM→WB stage (just finished memory op)
    if mem_wb and will_write_rd(mem_wb["instr"]):
        if mem_wb["instr"].rd == reg:
            return True, mem_wb["val"]
    
    return False, None
```

**Data Forwarding Paths**:
```
EX stage output ──→ EX input (for next instruction)
MEM stage output ──→ EX input (for 2nd next instruction)
WB stage output ──→ ID input (for branch instructions)
```

#### Pipeline State Variables

```python
if_id = {"instr": instruction, "pc": program_counter}
id_ex = {
    "instr": instruction, 
    "pc": program_counter,
    "rs1_reg": source_reg_1,
    "rs2_reg": source_reg_2,
    "imm": immediate,
    "latency": remaining_cycles
}
ex_mem = {"instr": instruction, "alu": alu_result, "store": value_to_store}
mem_wb = {"instr": instruction, "val": register_value}
```

---

## Data Flow & Examples

### Example 1: Simple ADD Operation

**Assembly Code**:
```assembly
ADDI x1, x0, 10    # x1 = 10
ADDI x2, x0, 20    # x2 = 20
ADD x3, x1, x2     # x3 = 30
```

**Non-Pipelined Execution**:
```
Cycle 1: PC=0, Execute ADDI x1, x0, 10
         → x1 = 10, PC = 4

Cycle 2: PC=4, Execute ADDI x2, x0, 20
         → x2 = 20, PC = 8

Cycle 3: PC=8, Execute ADD x3, x1, x2
         → x3 = 30, PC = 12
         → DONE (PC > last instruction)

Total: 3 cycles
```

**Pipelined Execution (No Forwarding)**:
```
Cycle  IF        ID        EX        MEM       WB
1      ADDI(0)   -         -         -         -
2      ADDI(4)   ADDI(0)   -         -         -
3      ADD(8)    ADDI(4)   ADDI(0)   -         -
4      -         ADD(8)    ADDI(4)   ADDI(0)   -
5      -         -         ADD(8)    ADDI(4)   ADDI(0)
6      -         -         -         ADD(8)    ADDI(4)
7      -         -         -         -         ADD(8)

Total: 7 cycles
```

**Pipelined Execution (With Forwarding)**:
```
Same as above because no data dependencies!
(ADDI(0) writes to x1, ADD reads x1 - different registers initially)
Actually, in this case there IS a dependency:
- ADDI x1 produces x1
- ADD uses x1

Cycle  IF        ID        EX        MEM       WB
1      ADDI(0)   -         -         -         -
2      ADDI(4)   ADDI(0)   -         -         -
3      ADD(8)    ADDI(4)   ADDI(0)   -         -
4      -         STALL     ADDI(4)   ADDI(0)   -   ← Hazard: x1 not ready
5      -         ADD(8)    EX→       ADDI(4)   ADDI(0)
6      -         -         MEM→      EX→       ADDI(4)
7      -         -         -         MEM→      EX→
8      -         -         -         -         MEM→
```

---

### Example 2: Load-Use Hazard

**Assembly Code**:
```assembly
LW x1, 0(x2)    # Load x1 from memory
ADD x3, x1, x4  # Add x1 (not ready!)
```

**With Forwarding Disabled**:
```
Cycle  IF        ID        EX        MEM       WB
1      LW(0)     -         -         -         -
2      ADD(4)    LW(0)     -         -         -
3      instr3    STALL     LW(0)     -         -      ← LW still in EX
4      -         STALL     EX→       LW(0)     -      ← LW still in MEM
5      -         STALL     EX→      MEM     LW(done)← LW completes
6      -         ADD       EX→       EX→      MEM
7      -         -         ADD       MEM       -
8      -         -         -         WB        -

Total: 8 cycles (2 stalls needed)
```

**With Forwarding Enabled**:
```
Cycle  IF        ID        EX        MEM       WB
1      LW(0)     -         -         -         -
2      ADD(4)    LW(0)     -         -         -
3      instr3    STALL     LW(0)     -         -      ← Still no bypass from MEM
4      -         STALL     EX→       LW(0)     -      ← Still waiting
5      -         STALL     EX→      MEM→      LW     ← LW result available from MEM
6      -         ADD(fwd)  EX→       EX→      MEM
7      -         -         ADD       MEM       -
8      -         -         -         WB        -

Total: 8 cycles (1 stall unavoidable - waiting for memory result)
```

---

### Example 3: Branch Instruction

**Assembly Code**:
```assembly
ADDI x1, x0, 10
ADDI x2, x0, 10
BEQ x1, x2, EQUAL   # Branch to EQUAL (x1==x2)
ADDI x3, x0, 0      # Skipped if branch taken
EQUAL: ADDI x3, x0, 1   # x3 = 1
```

**Execution with Branch**:
```
PC Values: EQUAL = 12 (instruction 3)

Cycle  PC    Instruction        Result
1      0     ADDI x1, 0, 10    → x1=10, PC=4
2      4     ADDI x2, 0, 10    → x2=10, PC=8
3      8     BEQ x1, x2, EQUAL → x1==x2? Yes! PC=12 (FLUSH pipeline)
4      12    ADDI x3, 0, 1     → x3=1, PC=16 (continue from target)

Total: 4 cycles
```

**Pipeline Flush on Branch**:
```
Before Branch Decision:
Cycle  IF        ID        EX        MEM       WB
3      instr?    BEQ(8)    prev_ex   prev_mem  prev_wb

Decision Moment: BEQ evaluates to TRUE → PC = 12

After Branch Decision:
Cycle  IF        ID        EX        MEM       WB
4      ADDI(12)  -         -         -         -      ← Flushed ID_EX
                (cleared)  (cleared)                   ← Flushed EX, MEM
```

---

### Example 4: Load and Store

**Assembly Code**:
```assembly
.data
    val: .word 42

.text
    LA x1, val          # x1 = address of val (1024)
    LW x2, 0(x1)        # x2 = memory[1024] = 42
    ADDI x2, x2, 8      # x2 = 50
    SW x2, 4(x1)        # memory[1028] = 50
```

**Parsing**:
```python
# LA expands to ADDI
Instruction(opcode="ADDI", rd=1, rs1=0, imm=1024)

# LW parsed as
Instruction(opcode="LW", rd=2, rs1=1, imm=0)

# ADDI parsed as
Instruction(opcode="ADDI", rd=2, rs1=2, imm=8)

# SW parsed as
Instruction(opcode="SW", rd=2, rs1=1, imm=4)
```

**Execution**:
```
Cycle 1: ADDI x1, x0, 1024  → x1=1024
Cycle 2: LW x2, 0(x1)       → x2=memory[1024]=42
Cycle 3: ADDI x2, x2, 8     → x2=50
Cycle 4: SW x2, 4(x1)       → memory[1028]=50

Memory State:
  Address 1024: 42 (unchanged)
  Address 1028: 50 (stored)
```

---

## Pipeline Architecture

### Complete Pipeline Flow Diagram

```
                            ┌─────────────────────────────┐
                            │   Instruction Memory        │
                            │  (Instructions Array)       │
                            └──────────────┬──────────────┘
                                          │
                                          ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │                      INSTRUCTION FETCH (IF)                    │
    │  pc = 0, 4, 8, ...                                             │
    │  fetched_instr = fetch(pc)                                     │
    │  if_id = {instr, pc}                                           │
    └────────────────────┬────────────────────────────────────────────┘
                         │ if_id
                         ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │                 INSTRUCTION DECODE (ID)                        │
    │  Extract operands: rs1, rs2, rd, imm                          │
    │  Read register values                                          │
    │                                                                 │
    │  ≡ HAZARD DETECTION ≡                                          │
    │  Check for RAW hazards:                                        │
    │    - Load-use hazards                                          │
    │    - Branch dependencies                                       │
    │    - Multi-cycle latency stalls                                │
    │                                                                 │
    │  ≡ BRANCH RESOLUTION ≡                                         │
    │  For BEQ/BNE/BGE/BLE: Evaluate condition                       │
    │    if condition_true: pc_next = target, FLUSH pipeline         │
    │    else: pc_next = pc + 4                                      │
    │                                                                 │
    │  ≡ DATA FORWARDING (Optional) ≡                                │
    │  Forward data from EX_MEM, MEM_WB stages if available          │
    │                                                                 │
    │  id_ex = {instr, pc, rs1_reg, rs2_reg, imm, latency}         │
    └────────────────────┬────────────────────────────────────────────┘
                         │ id_ex
                         ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │                    EXECUTE (EX)                                │
    │  Respects latency counter: latency -= 1                       │
    │                                                                 │
    │  ≡ DATA FORWARDING (Optional) ≡                                │
    │  Use forwarded values from EX_MEM, MEM_WB if needed           │
    │  Else use register file values                                 │
    │                                                                 │
    │  Compute ALU operations:                                       │
    │    add:   alu = rs1 + rs2                                      │
    │    sub:   alu = rs1 - rs2                                      │
    │    addi:  alu = rs1 + imm                                      │
    │    slli:  alu = rs1 << imm                                     │
    │    lw/sw: alu = rs1 + imm (address calc)                       │
    │    jal:   alu = pc + 4 (return addr)                           │
    │                                                                 │
    │  ex_mem = {instr, alu, store_value}                           │
    └────────────────────┬────────────────────────────────────────────┘
                         │ ex_mem
                         ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │                    MEMORY (MEM)                                │
    │  ≡ LOAD (LW) ≡                                                  │
    │    val = memory[alu]  (address from EX stage)                 │
    │    mem_wb = {instr, val}                                      │
    │                                                                 │
    │  ≡ STORE (SW) ≡                                                │
    │    memory[alu] = store_value                                  │
    │    mem_wb = {instr=None}  (no WB needed)                      │
    │                                                                 │
    │  ≡ OTHER OPS ≡                                                 │
    │    Pass ALU result to WB                                      │
    │    mem_wb = {instr, alu}                                      │
    └────────────────────┬────────────────────────────────────────────┘
                         │ mem_wb
                         ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │                  WRITE BACK (WB)                               │
    │  if instr writes rd:                                           │
    │    register[rd] = value                                        │
    │                                                                 │
    │  (x0 writes are ignored - x0 is always 0)                     │
    └─────────────────────────────────────────────────────────────────┘
```

### Hazard Detection Matrix

```
Scenario              Forwarding OFF   Forwarding ON    Resolution
──────────────────────────────────────────────────────────────────────
ADD result used 
in next instruction      STALL (1)      FORWARD        Forward from EX
                         cycle                        or MEM stage

LW result used 
in next instruction      STALL (1)      STALL (1)      Can't forward
                         cycle          cycle          from MEM until
                                                       MEM completes

Branch depends on
previous result          STALL (2)      STALL (1)      Forward if avail
                         cycles         cycle          else stall

Multi-cycle latency      STALL until    STALL until    Hardware waits
(e.g., LW latency=2)     latency=0      latency=0      for operation

Two consecutive
branches                 STALL (1)      STALL (1)      Flush on taken
                         cycle          cycle          branch
```

---

## Execution Examples

### Complete Program Execution: Bubble Sort

**Assembly Code**:
```assembly
.data
    arr: .word 5, 2, 8, 1, 9

.text
    LA x10, arr         # x10 = address of array
    ADDI x11, x0, 5     # x11 = array length
    ADDI x12, x0, 0     # x12 = outer loop counter
    
OUTER_LOOP:
    ADDI x13, x11, -1   # x13 = length - 1
    ADDI x14, x0, 0     # x14 = inner loop counter
    
INNER_LOOP:
    BEQ x14, x13, OUTER_CONTINUE  # if i == n-1, next outer iteration
    
    # Load arr[i]
    ADDI x15, x14, 0
    SLLI x15, x15, 2    # x15 = i * 4 (byte offset)
    ADD x15, x10, x15   # x15 = address of arr[i]
    LW x20, 0(x15)      # x20 = arr[i]
    
    # Load arr[i+1]
    ADDI x16, x14, 1
    SLLI x16, x16, 2
    ADD x16, x10, x16
    LW x21, 0(x16)      # x21 = arr[i+1]
    
    # if arr[i] <= arr[i+1], skip swap
    BLE x20, x21, SKIP_SWAP
    
    # Swap
    SW x21, 0(x15)      # arr[i] = arr[i+1]
    SW x20, 0(x16)      # arr[i+1] = arr[i]
    
SKIP_SWAP:
    ADDI x14, x14, 1
    BNE x14, x13, INNER_LOOP
    
OUTER_CONTINUE:
    ADDI x12, x12, 1
    BNE x12, x11, OUTER_LOOP
```

**Execution Flow** (Simplified, showing key steps):

```
Step 1: Initialize
  x10 = 1024 (array address)
  x11 = 5 (length)
  x12 = 0 (outer counter)

Step 2-N: Nested loop execution
  For each element pair:
    - Load both values
    - Compare
    - Conditionally swap
    - Advance inner counter
    - Check inner loop condition
  Next outer iteration

Final Result:
  memory[1024] = 1 (smallest)
  memory[1028] = 2
  memory[1032] = 5
  memory[1036] = 8
  memory[1040] = 9 (largest)
```

**Statistics** (with pipelining):
- Total instructions: ~50+
- Cycles (without forwarding): ~200+ (many stalls)
- Cycles (with forwarding): ~120+ (fewer stalls)
- Stalls: ~30+
- Branch flushes: ~20+

---

### Execution Statistics Breakdown

**Key Metrics Tracked**:

```python
{
    "cycles": 45,        # Total cycles to complete
    "stalls": 8,         # Number of stall cycles inserted
    "flushes": 3         # Number of pipeline flushes on branches
}
```

**Performance Calculations**:

```
Instructions: N
CPI (Cycles Per Instruction) = cycles / instructions

For pipelined without stalls: CPI ≈ 1
For pipelined with stalls: CPI > 1
For non-pipelined: CPI = N (worst case)

Speedup = Non-pipelined cycles / Pipelined cycles
```

---

## Configuration Parameters Explained

**`Forwarding`**:
- `true`: Enable data forwarding (fewer stalls, more complex hardware)
- `false`: Disable forwarding (more stalls, simpler hardware)

**`MemorySize`**:
- Total addressable memory in bytes (default 4096)
- Addresses 0-1023: typically for code (not directly addressed in RISC-V)
- Addresses 1024+: data segment

**`Latency_*`**:
- Number of cycles an instruction takes to complete its EX stage
- Most instructions: 1 cycle
- LW: 2 cycles (needs time for memory access)
- Higher latency → more potential stalls

---

## Summary: Key Concepts

| Concept | Explanation |
|---------|-------------|
| **Register x0** | Always zero, writes ignored |
| **PC** | Points to current instruction (byte address ÷ 4 = instruction index) |
| **Data Forwarding** | Pass data between adjacent pipeline stages to eliminate stalls |
| **Load-Use Hazard** | Special case requiring stall even with forwarding |
| **Branch Flush** | Clear IF/ID/EX stages when branch condition evaluated |
| **Latency** | Number of EX stage cycles needed for operation |
| **Stall** | Insert wait cycle to resolve dependencies |
| **Pipeline Stage** | One of 5 micro-steps: IF→ID→EX→MEM→WB |

---

## File Structure

```
riscv_sim/
├── config.py          # Configuration management
├── parser.py          # Assembly parser
├── cpu.py             # CPU state & registers
├── executor.py        # Non-pipelined executor
├── pipeline.py        # 5-stage pipeline executor
├── stats.py           # (Empty - for future stats)
├── main.py            # Entry point
│
└── testcases/
    ├── add.asm        # Simple addition
    ├── loop.asm       # Loop with branches
    ├── memory.asm     # Load/store operations
    ├── sw-ld.asm      # Store/load example
    ├── bubblesort.asm # Complex program
    └── ... (more test files)
```

---

## How to Run

```bash
python main.py testcases/add.asm ../config_file.txt

# Output:
# Config loaded: Memory Size=4096 bytes, Forwarding=false, Latencies={...}
# Instructions parsed: 4
# Final CPU state: PC=16, x0=0, x1=10, x2=20, x3=30, ...
# Final Stats: Cycles=7, Stalls=0, Flushes=0
```

---

*This documentation covers the RISC-V Simulator codebase completely with examples, flow diagrams, and execution traces for comprehensive understanding.*
