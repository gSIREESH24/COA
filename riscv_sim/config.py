class Config:
    def __init__(self, config_file):
        self.memory_size = 4096
        self.forwarding = False
        self.latency = {}
        
        self.l1i_config = {
            'size': 32 * 1024,
            'block_size': 64,
            'associativity': 4,
            'latency': 1,
            'replacement_policy': 'LRU'
        }
        
        self.l1d_config = {
            'size': 32 * 1024,
            'block_size': 64,
            'associativity': 4,
            'latency': 1,
            'replacement_policy': 'LRU'
        }
        
        self.l2_config = {
            'size': 256 * 1024,
            'block_size': 64,
            'associativity': 8,
            'latency': 10,
            'replacement_policy': 'LRU'
        }
        
        self.main_memory_latency = 100
        
        with open(config_file, 'r') as f:
            for line in f:
                line = line.strip()
                
                if not line or line.startswith("#"):
                    continue
                
                if '=' not in line:
                    continue
                
                key, value = map(str.strip, line.split('=', 1))
                
                if key == "MemorySize":
                    self.memory_size = int(value)
                
                elif key == "Forwarding":
                    self.forwarding = (value.lower() == "true")
                
                elif key.lower().startswith("latency_"):
                    instr = key.split('_', 1)[1].upper()
                    self.latency[instr] = int(value)
                
                elif key == "L1I_Size":
                    self.l1i_config['size'] = int(value)
                elif key == "L1I_BlockSize":
                    self.l1i_config['block_size'] = int(value)
                elif key == "L1I_Associativity":
                    self.l1i_config['associativity'] = int(value)
                elif key == "L1I_Latency":
                    self.l1i_config['latency'] = int(value)
                elif key == "L1I_ReplacementPolicy":
                    self.l1i_config['replacement_policy'] = value.upper()
                
                elif key == "L1D_Size":
                    self.l1d_config['size'] = int(value)
                elif key == "L1D_BlockSize":
                    self.l1d_config['block_size'] = int(value)
                elif key == "L1D_Associativity":
                    self.l1d_config['associativity'] = int(value)
                elif key == "L1D_Latency":
                    self.l1d_config['latency'] = int(value)
                elif key == "L1D_ReplacementPolicy":
                    self.l1d_config['replacement_policy'] = value.upper()
                
                elif key == "L2_Size":
                    self.l2_config['size'] = int(value)
                elif key == "L2_BlockSize":
                    self.l2_config['block_size'] = int(value)
                elif key == "L2_Associativity":
                    self.l2_config['associativity'] = int(value)
                elif key == "L2_Latency":
                    self.l2_config['latency'] = int(value)
                elif key == "L2_ReplacementPolicy":
                    self.l2_config['replacement_policy'] = value.upper()
                
                elif key == "MainMemory_Latency":
                    self.main_memory_latency = int(value)

    def get_latency(self, instruction):
        return self.latency.get(instruction.upper(), 1)