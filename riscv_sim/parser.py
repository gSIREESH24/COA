class Instruction:

    def __init__(self, opcode, rd=None, rs1=None, rs2=None, imm=None, target=None):
        self.opcode = opcode
        self.rd = rd
        self.rs1 = rs1
        self.rs2 = rs2
        self.imm = imm
        self.target = target

    @staticmethod
    def reg_num(reg):
        if not reg.startswith("x"):
            raise ValueError(f"Invalid register: {reg}")
        return int(reg[1:])

    @staticmethod
    def parser_file(file_path):

        instructions = []
        labels = {}
        raw_lines = []

        data_memory = {}
        data_labels = {}

        section = "text"
        data_address = 1024

        with open(file_path) as f:

            for line in f:

                line = line.strip()

                if "#" in line:
                    line = line.split("#")[0].strip()

                if not line:
                    continue

                if line == ".data":
                    section = "data"
                    continue

                if line == ".text":
                    section = "text"
                    continue

                # ---------------- DATA ----------------
                if section == "data":

                    if ":" in line:

                        label, value = line.split(":")
                        label = label.strip()
                        value = value.strip()

                        if value.startswith(".word"):

                            nums = value.replace(".word", "").split(",")

                            data_labels[label] = data_address

                            for n in nums:
                                val = int(n.strip())
                                data_memory[data_address] = val
                                data_address += 4

                    continue

                # ---------------- TEXT ----------------
                if section == "text":

                    if line.endswith(":"):
                        lbl = line[:-1].strip().upper()
                        labels[lbl] = len(raw_lines) * 4
                        continue

                    raw_lines.append(line)

        # ---------------- PASS 2 ----------------
        for idx, line in enumerate(raw_lines):

            parts = line.replace(",", " ").replace("(", " ").replace(")", " ").split()
            opcode = parts[0].upper()
            pc = idx * 4

            # -------- R TYPE --------
            if opcode in ["ADD", "SUB"]:

                rd = Instruction.reg_num(parts[1])
                rs1 = Instruction.reg_num(parts[2])
                rs2 = Instruction.reg_num(parts[3])

                instructions.append(Instruction(opcode, rd, rs1, rs2))

            # -------- I TYPE --------
            elif opcode == "ADDI":

                rd = Instruction.reg_num(parts[1])
                rs1 = Instruction.reg_num(parts[2])
                imm = int(parts[3])

                instructions.append(Instruction(opcode, rd, rs1, imm=imm))

            elif opcode == "SLLI":

                rd = Instruction.reg_num(parts[1])
                rs1 = Instruction.reg_num(parts[2])
                imm = int(parts[3])

                instructions.append(Instruction(opcode, rd, rs1, imm=imm))

            # -------- LOAD / STORE --------
            elif opcode in ["LW", "SW"]:

                rd = Instruction.reg_num(parts[1])

                if len(parts) == 3 and parts[2] in data_labels:
                    imm = data_labels[parts[2]]
                    rs1 = 0
                else:
                    imm = int(parts[2])
                    rs1 = Instruction.reg_num(parts[3])

                instructions.append(Instruction(opcode, rd, rs1, imm=imm))

            # -------- LA --------
            elif opcode == "LA":

                rd = Instruction.reg_num(parts[1])
                label = parts[2]

                if label not in data_labels:
                    raise ValueError(f"Unknown label {label}")

                addr = data_labels[label]

                instructions.append(
                    Instruction("ADDI", rd, 0, imm=addr)
                )

            # -------- BRANCH --------
            elif opcode in ["BEQ","BNE","BGE","BLE"]:

                rs1 = Instruction.reg_num(parts[1])
                rs2 = Instruction.reg_num(parts[2])
                target_str = parts[3]

                if target_str.lstrip("-").isdigit():
                    offset = int(target_str)
                    target = pc + offset * 4
                else:
                    target = labels[target_str.upper()]

                instructions.append(
                    Instruction(opcode, rs1=rs1, rs2=rs2, target=target)
                )

            # -------- JAL --------
            elif opcode == "JAL":

                rd = Instruction.reg_num(parts[1])
                target_str = parts[2]

                if target_str.lstrip("-").isdigit():
                    offset = int(target_str)
                    target = pc + offset * 4
                else:
                    target = labels[target_str.upper()]

                instructions.append(
                    Instruction(opcode, rd=rd, target=target)
                )

            else:
                raise ValueError(f"Unknown instruction: {opcode}")

        return instructions, data_memory, data_labels


class Parser:

    def __init__(self):
        self.instructions = []
        self.data_memory = {}
        self.data_labels = {}

    def instr(self, file_path):

        self.instructions, self.data_memory, self.data_labels = \
            Instruction.parser_file(file_path)

        return self.instructions, self.data_memory, self.data_labels