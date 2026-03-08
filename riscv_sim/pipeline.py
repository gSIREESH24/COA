def will_write_rd(instr):
    if instr is None:
        return False
    return instr.opcode in ("ADD","SUB","ADDI","LW","JAL","SLLI") and instr.rd is not None


def forward_value(reg, ex_mem, mem_wb):
    if reg is None:
        return False, None

    if ex_mem and ex_mem.get("instr"):
        instr = ex_mem["instr"]
        if instr.opcode != "LW" and will_write_rd(instr) and instr.rd == reg and reg != 0:
            return True, ex_mem["alu"]

    if mem_wb and mem_wb.get("instr"):
        instr = mem_wb["instr"]
        if will_write_rd(instr) and instr.rd == reg and reg != 0:
            return True, mem_wb["val"]

    return False, None


def run_pipeline(cpu, instructions, config, max_cycles=1000000, verbose=False):

    pc = cpu.pc

    if_id = None
    id_ex = None
    ex_mem = None
    mem_wb = None

    cycles = 0
    stalls = 0
    flushes = 0

    def fetch(pc):
        if pc // 4 < len(instructions):
            return instructions[pc // 4]
        return None

    while cycles < max_cycles:

        cycles += 1

        # ---------------- WB ----------------
        if mem_wb:
            instr = mem_wb["instr"]
            if instr and will_write_rd(instr):
                cpu.write_reg(instr.rd, mem_wb["val"])

        # ---------------- MEM ----------------
        new_mem_wb = None

        if ex_mem:
            instr = ex_mem["instr"]

            if instr:

                if instr.opcode == "LW":
                    val = cpu.load(ex_mem["alu"])
                    new_mem_wb = {"instr": instr, "val": val}

                elif instr.opcode == "SW":
                    cpu.store(ex_mem["alu"], ex_mem["store"])
                    new_mem_wb = {"instr": None}

                else:
                    new_mem_wb = {"instr": instr, "val": ex_mem["alu"]}

        # ---------------- EX ----------------
        new_ex_mem = None

        if id_ex:

            instr = id_ex["instr"]

            rs1 = cpu.read_reg(id_ex["rs1_reg"]) if id_ex["rs1_reg"] is not None else 0
            rs2 = cpu.read_reg(id_ex["rs2_reg"]) if id_ex["rs2_reg"] is not None else 0

            if config.forwarding:

                f,v = forward_value(id_ex["rs1_reg"], ex_mem, mem_wb)
                if f: rs1 = v

                f,v = forward_value(id_ex["rs2_reg"], ex_mem, mem_wb)
                if f: rs2 = v

            imm = id_ex["imm"]

            if instr.opcode == "ADD":
                alu = rs1 + rs2

            elif instr.opcode == "SUB":
                alu = rs1 - rs2

            elif instr.opcode == "ADDI":
                alu = rs1 + imm

            elif instr.opcode == "SLLI":
                alu = rs1 << imm

            elif instr.opcode in ("LW","SW"):
                alu = rs1 + imm

            elif instr.opcode == "JAL":
                alu = id_ex["pc"] + 4

            else:
                alu = None

            if instr.opcode == "SW":

                store_val = cpu.read_reg(instr.rd)

                if config.forwarding:
                    f,v = forward_value(instr.rd, ex_mem, mem_wb)
                    if f: store_val = v

                new_ex_mem = {
                    "instr": instr,
                    "alu": alu,
                    "store": store_val
                }

            elif will_write_rd(instr):

                new_ex_mem = {
                    "instr": instr,
                    "alu": alu
                }

            else:

                new_ex_mem = {"instr": None}

        # ---------------- ID ----------------
        stall = False
        branch_taken = False
        branch_target = None
        new_id_ex = None

        if if_id:

            instr = if_id["instr"]
            instr_pc = if_id["pc"]

            srcs = []

            if instr.rs1 is not None:
                srcs.append(instr.rs1)

            if instr.rs2 is not None:
                srcs.append(instr.rs2)

            if instr.opcode == "SW":
                srcs.append(instr.rd)

            if not config.forwarding:

                for stage in [id_ex, ex_mem, mem_wb]:
                    if stage and stage.get("instr") and will_write_rd(stage["instr"]):
                        if stage["instr"].rd in srcs and stage["instr"].rd != 0:
                            stall = True
                            break

            else:

                if instr.opcode in ("BEQ", "BNE", "BGE", "BLE"):
                    for stage in [id_ex, ex_mem, mem_wb]:
                        if stage and stage.get("instr") and will_write_rd(stage["instr"]):
                            if stage["instr"].rd in srcs and stage["instr"].rd != 0:
                                stall = True
                                break
                elif id_ex and id_ex["instr"].opcode == "LW":
                    if id_ex["instr"].rd in srcs and id_ex["instr"].rd != 0:
                        stall = True

            if not stall:

                rs1_val = cpu.read_reg(instr.rs1) if instr.rs1 is not None else 0
                rs2_val = cpu.read_reg(instr.rs2) if instr.rs2 is not None else 0

                if config.forwarding and instr.opcode not in ("BEQ", "BNE", "BGE", "BLE"):

                    f,v = forward_value(instr.rs1, ex_mem, mem_wb)
                    if f: rs1_val = v

                    f,v = forward_value(instr.rs2, ex_mem, mem_wb)
                    if f: rs2_val = v

                if instr.opcode == "BEQ":
                    if rs1_val == rs2_val:
                        branch_taken = True
                        branch_target = instr.target

                elif instr.opcode == "BNE":
                    if rs1_val != rs2_val:
                        branch_taken = True
                        branch_target = instr.target

                elif instr.opcode == "BGE":
                    if rs1_val >= rs2_val:
                        branch_taken = True
                        branch_target = instr.target

                elif instr.opcode == "BLE":
                    if rs1_val <= rs2_val:
                        branch_taken = True
                        branch_target = instr.target

                elif instr.opcode == "JAL":

                    branch_taken = True
                    branch_target = instr.target

                    if instr.rd == 0 and branch_target == instr_pc:
                        break

                new_id_ex = {
                    "instr": instr,
                    "pc": instr_pc,
                    "rs1_reg": instr.rs1,
                    "rs2_reg": instr.rs2,
                    "imm": instr.imm
                }

        if stall:
            stalls += 1

        # ---------------- IF ----------------
        new_if_id = if_id

        if not stall:

            instr_pc = pc
            fetched = fetch(pc)

            if fetched:
                pc += 4

            if fetched:
                new_if_id = {"instr": fetched, "pc": instr_pc}
            else:
                new_if_id = None

        # ---------------- Flush ----------------
        if branch_taken:

            pc = branch_target
            new_if_id = None
            flushes += 1

        # ---------------- Update ----------------
        id_ex = new_id_ex
        if_id = new_if_id

        ex_mem = new_ex_mem
        mem_wb = new_mem_wb

        done = (
            if_id is None and
            id_ex is None and
            ex_mem is None and
            mem_wb is None and
            pc >= len(instructions)*4
        )

        if done:
            break

    cpu.pc = pc
    
    if verbose:
        print("\nFinal Stats")
        print("Cycles:", cycles)
        print("Stalls:", stalls)
        print("Flushes:", flushes)

    return {
        "cycles": cycles,
        "stalls": stalls,
        "flushes": flushes
    }