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

        with open(file_path) as f:
            for line in f:

                line = line.strip()

                if "#" in line:
                    line = line.split("#")[0].strip()

                if not line:
                    continue

                if line.endswith(":"):
                    lbl = line[:-1].strip().upper()
                    labels[lbl] = len(raw_lines) * 4
                    continue

                raw_lines.append(line)

        for idx, line in enumerate(raw_lines):

            parts = line.replace(",", " ").replace("(", " ").replace(")", " ").split()
            opcode = parts[0].upper()

            pc = idx * 4

            if opcode in ["ADD", "SUB"]:

                rd = Instruction.reg_num(parts[1])
                rs1 = Instruction.reg_num(parts[2])
                rs2 = Instruction.reg_num(parts[3])

                instructions.append(Instruction(opcode, rd, rs1, rs2))

            elif opcode == "ADDI":

                rd = Instruction.reg_num(parts[1])
                rs1 = Instruction.reg_num(parts[2])
                imm = int(parts[3])

                instructions.append(Instruction(opcode, rd, rs1, imm=imm))

            elif opcode == "LW":

                rd = Instruction.reg_num(parts[1])
                imm = int(parts[2])
                rs1 = Instruction.reg_num(parts[3])

                instructions.append(
                    Instruction(opcode, rd=rd, rs1=rs1, imm=imm)
                )

            elif opcode == "SW":

                rs2 = Instruction.reg_num(parts[1])
                imm = int(parts[2])
                rs1 = Instruction.reg_num(parts[3])

                instructions.append(
                    Instruction(opcode, rs1=rs1, rs2=rs2, imm=imm)
                )
            elif opcode in ["BEQ", "BNE"]:
              rs1 = Instruction.reg_num(parts[1])
              rs2 = Instruction.reg_num(parts[2])
              target_str = parts[3]

              if target_str.lstrip("-").isdigit():

                  offset = int(target_str)
                  target = pc + offset

              else:

                  lbl = target_str.upper()
                  if lbl not in labels:
                      raise ValueError(f"Unknown label: {target_str}")

                  target = labels[lbl]

              instructions.append(
                  Instruction(opcode, rs1=rs1, rs2=rs2, target=target)
              )
            elif opcode == "JAL":

                rd = Instruction.reg_num(parts[1])
                target_str = parts[2]

                if target_str.lstrip("-").isdigit():
                    offset = int(target_str)
                    target = pc + offset * 4
                else:
                    target = labels[target_str.upper()]

                instructions.append(Instruction(opcode, rd=rd, target=target))

            else:
                raise ValueError(f"Unknown instruction: {opcode}")

        return instructions


class Parser:

    def __init__(self):
        self.instructions = []

    def instr(self, file_path):
        self.instructions = Instruction.parser_file(file_path)
        return self.instructions
