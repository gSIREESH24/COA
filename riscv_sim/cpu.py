class Cpu:
    def __init__(self, memory_size=4096, memory_system=None):
        self.registers = [0] * 32
        self.pc = 0
        self.memory_system = memory_system
        self.memory = bytearray(memory_size) if memory_system is None else memory_system.get_memory()
        
        self._last_access_latency = 1
        self._last_instruction_latency = 1
        
    def read_reg(self, reg_num):
        if reg_num == 0:
            return 0
        return self.registers[reg_num]

    def write_reg(self, reg_num, value):
        if reg_num != 0:
            self.registers[reg_num] = value & 0xFFFFFFFF

    def load(self, address):
        if self.memory_system:
            latency, hit = self.memory_system.access(address, "LOAD")
            self._last_access_latency = latency
        else:
            self._last_access_latency = 1
            
        b0 = self.memory[address]
        b1 = self.memory[address + 1]
        b2 = self.memory[address + 2]
        b3 = self.memory[address + 3]
        return b0 | (b1 << 8) | (b2 << 16) | (b3 << 24)

    def store(self, address, value):
        if self.memory_system:
            latency, hit = self.memory_system.access(address, "STORE", value)
            self._last_access_latency = latency
        else:
            self._last_access_latency = 1
            
        value &= 0xFFFFFFFF
        self.memory[address] = value & 0xFF
        self.memory[address + 1] = (value >> 8) & 0xFF
        self.memory[address + 2] = (value >> 16) & 0xFF
        self.memory[address + 3] = (value >> 24) & 0xFF
    
    def fetch_instruction(self, address):
        if self.memory_system:
            latency, hit = self.memory_system.access(address, "IF")
            self._last_instruction_latency = latency
        else:
            self._last_instruction_latency = 1
            
        b0 = self.memory[address]
        b1 = self.memory[address + 1]
        b2 = self.memory[address + 2]
        b3 = self.memory[address + 3]
        return b0 | (b1 << 8) | (b2 << 16) | (b3 << 24)

    def next_pc(self):
        self.pc += 4

    def jump(self, target):
        self.pc = target

    def branch(self, condition, target):
        if condition:
            self.pc = target
        else:
            self.next_pc()

    def __str__(self):
        reg_str = " ".join([f"x{i}={self.registers[i]}" for i in range(32)])
        return f"PC={self.pc} {reg_str}"