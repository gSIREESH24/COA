# COA - Computer Organization and Architecture
 DIRECTIONS ON HOW TO USE RUN THE SIMULATOR:
use this terminal command below :)
- make sure u are in the correct directory i.e , the riscv_sim  directory
cmd:-python riscv_sim/trace_runner.py riscv_sim/phase3_traces/traceXX.trace config_phase3.ini

## 📋 Meeting Minutes

---
---

### 📝 Meeting 11
**Date:** April 5, 2026
* **Members:** G Sireesh Reddy, G Siddhardha
* **Decisions:** Final submission of Phase 2 project.
* **Tasks Assigned:**
    * [x] **Both:** Final review and submission
* **Accomplishments from Previous Meeting:**
    * Completed full integration of cache hierarchy and performance metrics including IPC, stall cycles, and cache miss rates.

---

### 📝 Meeting 10
**Date:** April 4, 2026
* **Members:** G Sireesh Reddy, G Siddhardha
* **Decisions:** Completed testing and validation of Phase 2. Finalized output metrics and ensured correctness of execution.
* **Tasks Assigned:**
    * [x] **G Sireesh Reddy:** Final verification of results and edge case testing (Deadline: April 5)
    * [x] **G Siddhardha:** Documentation and README update for Phase 2 (Deadline: April 5)
* **Accomplishments from Previous Meeting:**
    * Successfully implemented cache-based memory system with variable latency and pipeline stall handling.

---

### 📝 Meeting 9
**Date:** April 3, 2026
* **Members:** G Sireesh Reddy, G Siddhardha
* **Decisions:** Finalized pipeline modifications to handle cache latency and ensured correct stall propagation across stages.
* **Tasks Assigned:**
    * [x] **G Sireesh Reddy:** Test cache performance and validate miss rate calculations (Deadline: April 4)
    * [x] **G Siddhardha:** Compute IPC and total stall cycles, integrate performance metrics (Deadline: April 4)
* **Accomplishments from Previous Meeting:**
    * Successfully connected cache hierarchy (L1I, L1D, L2) with pipeline and memory system.

---

### 📝 Meeting 8
**Date:** April 1, 2026
* **Members:** G Sireesh Reddy, G Siddhardha
* **Decisions:** Integrated cache with memory system and defined data flow for instruction fetch and load/store operations.
* **Tasks Assigned:**
    * [x] **G Sireesh Reddy:** Verify cache hit/miss behavior and implement eviction handling (Deadline: April 3)
    * [x] **G Siddhardha:** Modify pipeline to support variable latency and introduce stall cycles (Deadline: April 3)
* **Accomplishments from Previous Meeting:**
    * Successfully implemented cache structure with configurable parameters and replacement policies.

---

### 📝 Meeting 7
**Date:** March 30, 2026
* **Members:** G Sireesh Reddy, G Siddhardha
* **Decisions:** Finalized cache configurations including L1I, L1D, and unified L2. Decided to implement LRU as primary replacement policy and LFU as secondary.
* **Tasks Assigned:**
    * [x] **G Sireesh Reddy:** Implement cache class with read/write operations and replacement policies (Deadline: April 1)
    * [x] **G Siddhardha:** Develop memory system to connect cache hierarchy with main memory (Deadline: April 1)
* **Accomplishments from Previous Meeting:**
    * Completed cache design planning and defined configuration parameters.

---

### 📝 Meeting 6
**Date:** March 28, 2026
* **Members:** G Sireesh Reddy, G Siddhardha
* **Decisions:** Started Phase 2 implementation focusing on cache integration and memory hierarchy design. Finalized approach for adding multi-level cache without modifying core Phase 1 structure.
* **Tasks Assigned:**
    * [x] **G Sireesh Reddy:** Design cache structure and define parameters for L1 and L2 caches (Deadline: March 30)
    * [x] **G Siddhardha:** Plan integration of cache with pipeline and memory access flow (Deadline: March 30)
* **Accomplishments from Previous Meeting:**
    * Successfully completed pipelined architecture with forwarding and verified execution.

---

### 📝 Meeting 5
**Date:** March 8, 2026
* **Members:** G Sireesh Reddy, G Siddhardha
* **Decisions:** Final project completion and verification.
* **Tasks Assigned:**
    * [x] **G Sireesh Reddy:** Checked everything is working fine (Deadline: March 8)
    * [x] **G Siddhardha:** Checked everything is working fine (Deadline: March 8)
* **Accomplishments from Previous Meeting:**
    * Successfully started implementing the pipeline.

---

### 📝 Meeting 4
**Date:** March 4, 2026
* **Members:** G Sireesh Reddy, G Siddhardha
* **Decisions:** Planned the transition to Pipelined architecture.
* **Tasks Assigned:**
    * [x] **G Sireesh Reddy:** Pipeline without Forwarding implementation (Deadline: March 8)
    * [x] **G Siddhardha:** Pipeline with Forwarding implementation (Deadline: March 8)
* **Accomplishments from Previous Meeting:**
    * Completed the implementation of the non-pipelined architecture.

---

### 📝 Meeting 3
**Date:** February 28, 2026
* **Members:** G Sireesh Reddy, G Siddhardha
* **Decisions:** Finalized core design and component breakdown.
* **Tasks Assigned:**
    * [x] **G Sireesh Reddy:** Parser development (Deadline: March 2)
    * [x] **G Siddhardha:** Executor and CPU logic (Deadline: March 2)
* **Accomplishments from Previous Meeting:**
    * Defined step-by-step project roadmap.
    * Established configuration file, main file, and folder structure.

---

### 📝 Meeting 2
**Date:** February 23, 2026
* **Members:** G Sireesh Reddy, G Siddhardha
* **Decisions:** Official start of project implementation.
* **Tasks Assigned:**
    * [x] **G Sireesh Reddy:** Implementation of Config and Main files (Deadline: Feb 25)
    * [x] **G Siddhardha:** Folder structure design and step-wise implementation plan (Deadline: Feb 24)
* **Accomplishments from Previous Meeting:**
    * Full understanding of project requirements.
    * Initial project planning completed.

---

### 📝 Meeting 1
**Date:** February 20, 2026
* **Members:** G Sireesh Reddy, G Siddhardha
* **Decisions:** Requirement analysis and project scoping.
* **Tasks Assigned:**
    * [x] **Both:** Deep dive into project requirements (Deadline: Feb 22)
    * [x] **G Siddhardha:** Procedural planning and milestones (Deadline: Feb 22)
