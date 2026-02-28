class Cpu:
  def __init__(self,memory_size=4096):
    self.registers=[0]*32
    self.memory=[0]*memory_size
    self.pc=0
    
  def read_reg(self,reg_num):
    if reg_num==0:
      return 0
    return self.registers[reg_num]
  
  def write_reg(self,reg_num,value):
    if reg_num==0:
      return
    self.registers[reg_num]=value & 0xFFFFFFFF
    
  def load(self,address):
    return self.memory[address]
  
  def store(self,address,value):
    self.memory[address]=value & 0xFFFFFFFF
    
  def next_pc(self):
    self.pc+=1
    
  def jump(self,target):
    self.pc=target
  
  def branch(self,condition,target):
    if condition:
      self.pc=target
    else:
      self.next_pc()
  
  