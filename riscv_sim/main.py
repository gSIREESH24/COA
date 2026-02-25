import sys
from config import Config
#from parser import Parser
#from cpu import CPU
#from stats import Stats
#from pipeline import PipelineCpu

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
  
  '''parser = Parser(assembly_file)
  print("Program Loaded. instructions:", len(parser.instructions))
  
  cpu=CPU(config.memory_size)
  
  stats=Stats()
  
  simulator=PipelineCpu(cpu,config,parser.instructions,stats)
  
  print("\nRunning simulation...\n")
  simulator.run()
  
  stats.report()'''
  
  
if __name__ == "__main__":
  main()