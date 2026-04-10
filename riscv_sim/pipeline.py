def will_write_rd(instr):
    if instr is None:
        return False
    return instr.opcode in ("ADD", "SUB", "ADDI", "LW", "JAL", "SLLI") and instr.rd is not None

def store_data_reg(instr):
    if instr is None or instr.opcode != "SW":
        return None
    return instr.rs2 if instr.rs2 is not None else instr.rd

def forward_value(reg, ex_mem, mem_wb):
    if reg is None or reg == 0:
        return False, None

    if ex_mem and ex_mem.get("instr"):
        instr = ex_mem["instr"]
        if instr.opcode != "LW" and will_write_rd(instr) and instr.rd == reg:
            return True, ex_mem["alu"]

    if mem_wb and mem_wb.get("instr"):
        instr = mem_wb["instr"]
        if will_write_rd(instr) and instr.rd == reg:
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
    instructions_executed = 0

    if_stalls = 0
    cache_stalls = 0

    if_fetching = False
    if_latency = 0

    BRANCH_OPS = ("BEQ", "BNE", "BGE", "BLE")

    def fetch(target_pc):
        idx = target_pc // 4
        if 0 <= idx < len(instructions):
            return instructions[idx]
        return None

    def get_src_regs(instr):
        if instr is None:
            return []

        srcs = []
        if instr.rs1 is not None:
            srcs.append(instr.rs1)

        if instr.opcode in ("ADD", "SUB", "BEQ", "BNE", "BGE", "BLE"):
            if instr.rs2 is not None:
                srcs.append(instr.rs2)

        if instr.opcode == "SW":
            sreg = store_data_reg(instr)
            if sreg is not None:
                srcs.append(sreg)

        return srcs

    while cycles < max_cycles:
        cycles += 1

        # ---------------- WB stage ----------------
        if mem_wb and mem_wb.get("instr"):
            instr = mem_wb["instr"]
            instructions_executed += 1
            if will_write_rd(instr):
                cpu.write_reg(instr.rd, mem_wb["val"])

        new_mem_wb = None
        mem_busy = False

        # ---------------- MEM stage ----------------
        if ex_mem:
            if "latency" not in ex_mem:
                instr = ex_mem["instr"]
                if instr:
                    if instr.opcode == "LW":
                        val = cpu.load(ex_mem["alu"])
                        ex_mem["val"] = val
                        ex_mem["latency"] = max(1, getattr(cpu, "_last_access_latency", 1))
                    elif instr.opcode == "SW":
                        cpu.store(ex_mem["alu"], ex_mem["store"])
                        ex_mem["latency"] = max(1, getattr(cpu, "_last_access_latency", 1))
                    else:
                        ex_mem["latency"] = 1
                else:
                    ex_mem["latency"] = 1

            ex_mem["latency"] -= 1

            if ex_mem["latency"] > 0:
                mem_busy = True
            else:
                instr = ex_mem["instr"]
                if instr:
                    if instr.opcode == "LW":
                        new_mem_wb = {"instr": instr, "val": ex_mem["val"]}
                    elif instr.opcode == "SW":
                        new_mem_wb = {"instr": instr, "val": None}
                    else:
                        new_mem_wb = {"instr": instr, "val": ex_mem["alu"]}

        if mem_busy:
            cache_stalls += 1

        new_ex_mem = None
        ex_busy = False

        # ---------------- EX stage ----------------
        if not mem_busy:
            if id_ex:
                id_ex["latency"] -= 1

                if id_ex["latency"] > 0:
                    ex_busy = True
                else:
                    instr = id_ex["instr"]

                    rs1 = cpu.read_reg(id_ex["rs1_reg"]) if id_ex["rs1_reg"] is not None else 0
                    rs2 = cpu.read_reg(id_ex["rs2_reg"]) if id_ex["rs2_reg"] is not None else 0

                    if config.forwarding:
                        f, v = forward_value(id_ex["rs1_reg"], ex_mem, mem_wb)
                        if f: rs1 = v

                        f, v = forward_value(id_ex["rs2_reg"], ex_mem, mem_wb)
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
                    elif instr.opcode in ("LW", "SW"):
                        alu = rs1 + imm
                    elif instr.opcode == "JAL":
                        alu = id_ex["pc"] + 4
                    else:
                        alu = None

                    if instr.opcode == "SW":
                        sreg = store_data_reg(instr)
                        store_val = cpu.read_reg(sreg) if sreg is not None else 0

                        if config.forwarding and sreg is not None:
                            f, v = forward_value(sreg, ex_mem, mem_wb)
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
        else:
            if id_ex:
                ex_busy = True

        global_stall = mem_busy or ex_busy
        stall = False

        control_taken = False
        control_target = None
        control_kind = None

        new_id_ex = None

        # ---------------- ID stage ----------------
        if if_id and not global_stall:
            instr = if_id["instr"]
            instr_pc = if_id["pc"]

            srcs = get_src_regs(instr)

            if config.forwarding:
                if id_ex and id_ex.get("instr") and id_ex["instr"].opcode == "LW":
                    if id_ex["instr"].rd in srcs and id_ex["instr"].rd != 0:
                        stall = True

                if instr.opcode in BRANCH_OPS:
                    if id_ex and id_ex.get("instr") and will_write_rd(id_ex["instr"]):
                        if id_ex["instr"].rd in srcs and id_ex["instr"].rd != 0:
                            stall = True
                    if ex_mem and ex_mem.get("instr") and ex_mem["instr"].opcode == "LW":
                        if ex_mem["instr"].rd in srcs and ex_mem["instr"].rd != 0:
                            stall = True
            else:
                for stage in [id_ex, ex_mem, mem_wb]:
                    if stage and stage.get("instr") and will_write_rd(stage["instr"]):
                        if stage["instr"].rd in srcs and stage["instr"].rd != 0:
                            stall = True
                            break

            if ex_busy or mem_busy:
                stall = True

            if not stall:
                rs1_val = cpu.read_reg(instr.rs1) if instr.rs1 is not None else 0
                rs2_val = cpu.read_reg(instr.rs2) if instr.rs2 is not None else 0

                if config.forwarding:
                    f, v = forward_value(instr.rs1, ex_mem, mem_wb)
                    if f: rs1_val = v

                    f, v = forward_value(instr.rs2, ex_mem, mem_wb)
                    if f: rs2_val = v

                if instr.opcode == "BEQ":
                    instructions_executed += 1
                    if rs1_val == rs2_val:
                        control_taken = True
                        control_target = instr.target
                        control_kind = "BRANCH"
                elif instr.opcode == "BNE":
                    instructions_executed += 1
                    if rs1_val != rs2_val:
                        control_taken = True
                        control_target = instr.target
                        control_kind = "BRANCH"
                elif instr.opcode == "BGE":
                    instructions_executed += 1
                    if rs1_val >= rs2_val:
                        control_taken = True
                        control_target = instr.target
                        control_kind = "BRANCH"
                elif instr.opcode == "BLE":
                    instructions_executed += 1
                    if rs1_val <= rs2_val:
                        control_taken = True
                        control_target = instr.target
                        control_kind = "BRANCH"

                lat = max(1, config.get_latency(instr.opcode))

                new_id_ex = {
                    "instr": instr,
                    "pc": instr_pc,
                    "rs1_reg": instr.rs1,
                    "rs2_reg": instr.rs2,
                    "imm": instr.imm,
                    "latency": lat,
                }

                if instr.opcode == "JAL":
                    control_taken = True
                    control_target = instr.target
                    control_kind = "JAL"

        else:
            if global_stall and id_ex:
                new_id_ex = id_ex

        # ---------------- IF stage ----------------
        new_if_id = if_id

        if control_taken:
            pc = control_target
            if_fetching = False
            if_latency = 0

            new_if_id = None
            flushes += 1

            if control_kind == "BRANCH":
                new_id_ex = None

        elif stall or global_stall:
            new_if_id = if_id
            stalls += 1
            if if_fetching and if_latency > 0:
                if_latency -= 1
        else:
            if not if_fetching:
                fetched_instr = fetch(pc)
                if fetched_instr:
                    cpu.fetch_instruction(pc)
                    if_latency = max(1, getattr(cpu, "_last_instruction_latency", 1))
                    if_fetching = True
                else:
                    new_if_id = None

            if if_fetching:
                if_latency -= 1

                if if_latency <= 0:
                    new_if_id = {"instr": fetch(pc), "pc": pc}
                    pc += 4
                    if_fetching = False
                else:
                    new_if_id = None
                    stalls += 1
                    if_stalls += 1

        # ---------------- Pipeline Registers Advance ----------------
        if not mem_busy:
            mem_wb = new_mem_wb
            ex_mem = new_ex_mem
        else:
            mem_wb = None

        if not ex_busy and not mem_busy:
            id_ex = new_id_ex

        if not control_taken:
            if not stall and not global_stall:
                if_id = new_if_id
        else:
            if_id = None

        done = (
            if_id is None and
            id_ex is None and
            ex_mem is None and
            mem_wb is None and
            not if_fetching and
            pc >= len(instructions) * 4
        )

        if done:
            break

    cpu.pc = pc
    ipc = (instructions_executed / cycles) if cycles > 0 else 0

    if verbose:
        print("\nFinal Stats")
        print(f"Cycles: {cycles}")
        print(f"Stalls: {stalls}")
        print(f"Flushes: {flushes}")
        print(f"IPC: {ipc:.3f}")

    return {
        "cycles": cycles,
        "stalls": stalls,
        "flushes": flushes,
        "ipc": ipc,
        "cache_stalls": cache_stalls,
        "if_stalls": if_stalls,
    }