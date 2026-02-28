import sys
from config import Config
from parser import Parser
from cpu import Cpu
#from stats import Stats
#from pipeline import PipelineCpu

def execute(cpu,instruction):
  if instruction.opcode=="ADD":
    val=cpu.read_reg(instruction.rs1)+cpu.read_reg(instruction.rs2)
    cpu.write_reg(instruction.rd,val)
    cpu.next_pc()
    
  elif instruction.opcode=="SUB":
    val=cpu.read_reg(instruction.rs1)-cpu.read_reg(instruction.rs2)
    cpu.write_reg(instruction.rd,val)
    cpu.next_pc()
    
  elif instruction.opcode=="ADDI":
    val=cpu.read_reg(instruction.rs1)+instruction.imm
    cpu.write_reg(instruction.rd,val)
    cpu.next_pc()
    
  elif instruction.opcode=="LW":
    addr=cpu.read_reg(instruction.rs1)+instruction.imm
    val=cpu.load(addr)
    cpu.write_reg(instruction.rd,val)
    cpu.next_pc()
    
  elif instruction.opcode=="SW":
    addr=cpu.read_reg(instruction.rs1)+instruction.imm
    val=cpu.read_reg(instruction.rd)
    cpu.store(addr,val)
    cpu.next_pc()
    
  elif instruction.opcode=="BEQ":
    cond=(cpu.read_reg(instruction.rs1)==cpu.read_reg(instruction.rs2))
    cpu.branch(cond,instruction.target)
    
  elif instruction.opcode=="BNE":
    cond=(cpu.read_reg(instruction.rs1)!=cpu.read_reg(instruction.rs2))
    cpu.branch(cond,instruction.target)
    
  elif instruction.opcode=="JAL":
    ret_addr=cpu.pc+4
    cpu.write_reg(instruction.rd,ret_addr)
    cpu.jump(instruction.target)
    
def main():
  print("Starting RISC-V Simulator...")
  if len(sys.argv) < 3:
    print("Usage: python main.py <assembly_file> <config_file>")
    return
  
  assembly_file = sys.argv[1]
  config_file = sys.argv[2]
  
  config=Config(config_file)
  print("Memory Size:", config.memory_size)
  print("Forwarding Enabled:", config.forwarding)
  print("Instruction Latencies:", config.latency)
  
  var=config.get_latency("ADD")
  print("Latency for ADD instruction:", var)
  
  parser=Parser()
  instructions=parser.instr(assembly_file)
  print(f"Parsed {len(instructions)} instructions from {assembly_file}")
  
  cpu=Cpu(memory_size=config.memory_size)
  
  while cpu.pc < len(instructions):
    instr = instructions[cpu.pc]
    execute(cpu, instr)
    
  print(cpu.registers)
  print(cpu.memory[:16])
  
  '''stats=Stats()
  
  simulator=PipelineCpu(cpu,config,parser.instructions,stats)
  
  print("\nRunning simulation...\n")
  simulator.run()
  
  stats.report()'''
  
  
if __name__ == "__main__":
  main()