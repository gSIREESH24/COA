class Stats:
def **init**(self):
self.cycles = 0
self.instructions = 0
self.stalls = 0

```
def inc_cycle(self):
    self.cycles += 1

def inc_instruction(self):
    self.instructions += 1

def inc_stall(self):
    self.stalls += 1

def ipc(self):
    if self.cycles == 0:
        return 0
    return self.instructions / self.cycles

def report(self):
    print("\n===== Simulation Statistics =====")
    print("Total Cycles:", self.cycles)
    print("Instructions Executed:", self.instructions)
    print("Stalls:", self.stalls)
    print("IPC:", round(self.ipc(), 3))
```
