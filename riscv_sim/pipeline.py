def will_write_rd(instr):
    if instr is None:
        return False
    return instr.opcode in ("ADD", "SUB", "ADDI", "LW", "JAL") and instr.rd is not None


def instr_str(instr):
    if instr is None:
        return "-"
    return instr.opcode


def run_pipeline(cpu, instructions, config, max_cycles=100000, verbose=False):

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

        if verbose:
            print(f"\nCycle {cycles}")
            print("IF  :", instr_str(if_id))
            print("ID  :", instr_str(id_ex["instr"]) if id_ex else "-")
            print("EX  :", instr_str(ex_mem["instr"]) if ex_mem else "-")
            print("MEM :", instr_str(mem_wb["instr"]) if mem_wb else "-")
            print("--------------------------------")

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
        ex_busy = False

        if id_ex:

            if "remaining_ex" not in id_ex:
                id_ex["remaining_ex"] = config.get_latency(id_ex["instr"].opcode)

            id_ex["remaining_ex"] -= 1

            if id_ex["remaining_ex"] > 0:
                ex_busy = True

            else:

                instr = id_ex["instr"]

                rs1 = cpu.read_reg(id_ex["rs1_reg"]) if id_ex["rs1_reg"] is not None else 0

                if instr.opcode == "SW":
                    rs2 = cpu.read_reg(instr.rd)
                else:
                    rs2 = cpu.read_reg(id_ex["rs2_reg"]) if id_ex["rs2_reg"] is not None else 0
                imm = id_ex["imm"]

                if config.forwarding:

                    store_reg = instr.rd if instr.opcode == "SW" else instr.rs2

                    # MEM/WB forwarding
                    if mem_wb and mem_wb.get("instr") and will_write_rd(mem_wb["instr"]):

                        rd = mem_wb["instr"].rd
                        val = mem_wb["val"]

                        if instr.rs1 == rd and rd != 0:
                            rs1 = val

                        if store_reg == rd and rd != 0:
                            rs2 = val

                    # EX/MEM forwarding
                    if ex_mem and ex_mem.get("instr") and will_write_rd(ex_mem["instr"]):

                        rd = ex_mem["instr"].rd
                        val = ex_mem["alu"]

                        if instr.rs1 == rd and rd != 0:
                            rs1 = val

                        if store_reg == rd and rd != 0:
                            rs2 = val

                # -------- ALU --------

                if instr.opcode == "ADD":
                    alu = rs1 + rs2

                elif instr.opcode == "SUB":
                    alu = rs1 - rs2

                elif instr.opcode == "ADDI":
                    alu = rs1 + imm

                elif instr.opcode in ("LW", "SW"):
                    alu = rs1 + imm

                elif instr.opcode == "JAL":
                    alu = id_ex["pc"] + 4

                else:
                    alu = None

                if instr.opcode == "SW":
                    new_ex_mem = {"instr": instr, "alu": alu, "store": rs2}

                elif will_write_rd(instr):
                    new_ex_mem = {"instr": instr, "alu": alu}

                else:
                    new_ex_mem = {"instr": None}

                id_ex = None

        # ---------------- ID ----------------
        stall = False
        new_id_ex = None
        branch_taken = False
        branch_target = None

        if if_id:

            instr = if_id
            srcs = []

            if instr.rs1 is not None:
                srcs.append(instr.rs1)

            if instr.opcode == "SW":
                srcs.append(instr.rd)

            elif instr.rs2 is not None and instr.opcode not in ("ADDI", "JAL"):
                srcs.append(instr.rs2)

            if not config.forwarding:

                for stage in [id_ex, ex_mem, mem_wb]:

                    if stage and stage.get("instr") and will_write_rd(stage["instr"]):

                        rd = stage["instr"].rd

                        if rd != 0 and rd in srcs:
                            stall = True
                            break

            else:

                # load-use hazard
                if id_ex and id_ex["instr"].opcode == "LW":

                    rd = id_ex["instr"].rd

                    if rd != 0 and rd in srcs:
                        stall = True

                # producer still computing
                if id_ex and will_write_rd(id_ex["instr"]):

                    rd = id_ex["instr"].rd

                    if rd != 0 and rd in srcs and id_ex.get("remaining_ex", 0) > 0:
                        stall = True

            if not stall and not ex_busy:

                rs1_val = cpu.read_reg(instr.rs1) if instr.rs1 is not None else 0

                if instr.opcode == "SW":
                    rs2_val = cpu.read_reg(instr.rd)
                else:
                    rs2_val = cpu.read_reg(instr.rs2) if instr.rs2 is not None else 0

                if instr.opcode == "BEQ":
                    if rs1_val == rs2_val:
                        branch_taken = True
                        branch_target = instr.target

                elif instr.opcode == "BNE":
                    if rs1_val != rs2_val:
                        branch_taken = True
                        branch_target = instr.target

                new_id_ex = {
                    "instr": instr,
                    "pc": pc,
                    "rs1_reg": instr.rs1,
                    "rs2_reg": instr.rs2,
                    "imm": instr.imm
                }

        if stall:
            stalls += 1

        # ---------------- IF ----------------
        new_if_id = if_id

        if not stall and not ex_busy:

            fetched = fetch(pc)

            if fetched:
                pc += 4

            new_if_id = fetched

        # ---------------- Branch Flush ----------------
        if branch_taken:

            pc = branch_target
            new_if_id = None
            id_ex = None
            flushes += 1

        # ---------------- Pipeline Update ----------------

        if not ex_busy:
            id_ex = new_id_ex

        if not stall and not ex_busy:
            if_id = new_if_id

        ex_mem = new_ex_mem
        mem_wb = new_mem_wb

        done = (
            if_id is None and
            id_ex is None and
            ex_mem is None and
            mem_wb is None and
            pc >= len(instructions) * 4
        )

        if done:
            break

    cpu.pc = pc

    if verbose:
        print("\nFinal Stats")
        print("Cycles:", cycles)
        print("Stalls:", stalls)
        print("Flushes:", flushes)

    return {"cycles": cycles, "stalls": stalls, "flushes": flushes}