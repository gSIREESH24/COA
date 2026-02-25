
class Config:
  def __init__(self, config_file):
    with open(config_file, 'r') as f:
      lines = f.readlines()
      self.memory_size = 0
      self.forwarding = False
      self.latency={}
      
      for line in lines:
        line=line.strip()
        if line.startswith("#") or not line:
          continue
        key, value = line.split('=')
        key=key.strip()
        value=value.strip()
        
        if key=="MemorySize":
          self.memory_size=int(value)
          
        elif key=="Forwarding":
          self.forwarding=(value.lower() == "true")
          
        elif key.lower().startswith("latency_"):
          instr = key.split('_', 1)[1].upper()
          try:
            self.latency[instr] = int(value)
          except ValueError:
            raise ValueError(f"Invalid latency value for {key}: {value}")
          
  def get_latency(self,instruction):
    return self.latency.get(instruction,1)