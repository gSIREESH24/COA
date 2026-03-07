def will_write_rd(instr):
    if instr is None:
        return False
    return instr.opcode in ("ADD","SUB","ADDI","LW","JAL") and instr.rd is not None


def run_pipeline(cpu, instructions, max_cycles=100000, verbose=False):

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
            return instructions[pc//4]
        return None


    while cycles < max_cycles:

        cycles += 1

        # ---------------- WB ----------------
        if mem_wb:
            instr = mem_wb.get("instr")
            if instr and will_write_rd(instr):
                cpu.write_reg(instr.rd, mem_wb.get("val"))


        # ---------------- MEM ----------------
        new_mem_wb = None

        if ex_mem:

            instr = ex_mem.get("instr")

            if instr:

                if instr.opcode == "LW":

                    addr = ex_mem["alu"]
                    val = cpu.load(addr)

                    new_mem_wb = {"instr":instr,"val":val}

                elif instr.opcode == "SW":

                    cpu.store(ex_mem["alu"],ex_mem["store"])
                    new_mem_wb = {"instr":None}

                else:

                    new_mem_wb = {"instr":instr,"val":ex_mem["alu"]}


        # ---------------- EX ----------------
        new_ex_mem = None

        if id_ex:

            instr = id_ex["instr"]

            rs1 = id_ex["rs1"]
            rs2 = id_ex["rs2"]
            imm = id_ex["imm"]

            if instr.opcode == "ADD":
                alu = rs1 + rs2

            elif instr.opcode == "SUB":
                alu = rs1 - rs2

            elif instr.opcode == "ADDI":
                alu = rs1 + imm

            elif instr.opcode in ("LW","SW"):
                alu = rs1 + imm

            elif instr.opcode == "JAL":
                alu = id_ex["pc"] + 4

            else:
                alu = None

            if instr.opcode == "SW":
                new_ex_mem = {"instr":instr,"alu":alu,"store":rs2}

            elif instr.opcode in ("ADD","SUB","ADDI","LW","JAL"):
                new_ex_mem = {"instr":instr,"alu":alu}

            else:
                new_ex_mem = {"instr":None}


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
                if instr.rd is not None:
                    srcs.append(instr.rd)
            else:
                if instr.rs2 is not None and instr.opcode not in ("ADDI","JAL"):
                    srcs.append(instr.rs2)


            # -------- hazard detection --------
            if id_ex and will_write_rd(id_ex["instr"]):
                if id_ex["instr"].rd in srcs:
                    stall = True

            if ex_mem and ex_mem.get("instr") and will_write_rd(ex_mem["instr"]):
                if ex_mem["instr"].rd in srcs:
                    stall = True


            # -------- decode --------
            if not stall:

                rs1_val = cpu.read_reg(instr.rs1) if instr.rs1 is not None else 0

                if instr.opcode == "SW":
                    rs2_val = cpu.read_reg(instr.rd) if instr.rd is not None else 0
                else:
                    rs2_val = cpu.read_reg(instr.rs2) if instr.rs2 is not None else 0


                # ---------- branch compare ----------
                if instr.opcode == "BEQ":

                    if rs1_val == rs2_val:
                        branch_taken = True
                        branch_target = instr.target

                elif instr.opcode == "BNE":

                    if rs1_val != rs2_val:
                        branch_taken = True
                        branch_target = instr.target


                new_id_ex = {
                    "instr":instr,
                    "pc":pc,
                    "rs1":rs1_val,
                    "rs2":rs2_val,
                    "imm":instr.imm
                }


        if stall:
            stalls += 1


        # ---------------- IF ----------------

        new_if_id = None

        if not stall:

            fetched = fetch(pc)

            if fetched:
                pc += 4

            new_if_id = fetched

        else:

            new_if_id = if_id


        # ---------------- branch flush ----------------

        if branch_taken:
            if pc+4!= branch_target:
              pc = branch_target
              new_if_id = None
              flushes += 1
            else:
              pc=branch_target
              new_if_id = None


        # ---------------- pipeline update ----------------

        if stall:
            id_ex = None
        else:
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
        print("Cycles:",cycles)
        print("Stalls:",stalls)
        print("Flushes:",flushes)

    return {"cycles":cycles,"stalls":stalls,"flushes":flushes}