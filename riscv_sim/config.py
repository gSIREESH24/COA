"""
config.py  –  Phase 3 extension
================================
Backward-compatible with the old flat key=value format AND the new
INI-style [section] format required by Phase 3.

New fields exposed:
    config.vm_virtual_size      (bytes)
    config.vm_physical_size     (bytes)
    config.vm_page_size         (bytes)
    config.vm_num_frames        (int)    derived: physical_size // page_size
    config.vm_dtlb_entries      (int)
    config.vm_tlb_hit_latency   (int)
    config.vm_page_walk_latency (int)
    config.vm_page_fault_latency(int)
    config.vm_replacement_policy(str)    "fifo" | "lru"
"""

import configparser
import os


class Config:
    def __init__(self, config_file):
        # ── Legacy defaults ────────────────────────────────────────────
        self.memory_size  = 4096
        self.forwarding   = False
        self.latency      = {}

        self.l1i_config = {
            'size': 32 * 1024,
            'block_size': 64,
            'associativity': 4,
            'latency': 1,
            'replacement_policy': 'LRU',
        }
        self.l1d_config = {
            'size': 32 * 1024,
            'block_size': 64,
            'associativity': 4,
            'latency': 1,
            'replacement_policy': 'LRU',
        }
        self.l2_config = {
            'size': 256 * 1024,
            'block_size': 64,
            'associativity': 8,
            'latency': 10,
            'replacement_policy': 'LRU',
        }
        self.main_memory_latency = 100
        self.l2_enabled = True          # set False via config to disable L2

        # ── Phase-3 VM defaults ────────────────────────────────────────
        self.vm_virtual_size       = 4 * 1024 * 1024 * 1024   # 4 GB
        self.vm_physical_size      = 64 * 4096                 # 64 frames × 4 KB
        self.vm_page_size          = 4096
        self.vm_num_frames         = 64
        self.vm_dtlb_entries       = 16
        self.vm_tlb_hit_latency    = 1
        self.vm_page_walk_latency  = 10
        self.vm_page_fault_latency = 50
        self.vm_replacement_policy = "lru"

        # ── Detect file format and parse ───────────────────────────────
        self._parse(config_file)

        # Derive num_frames from physical_size / page_size (can be overridden)
        self.vm_num_frames = self.vm_physical_size // self.vm_page_size

    # ------------------------------------------------------------------
    def _parse(self, config_file: str):
        """Auto-detect INI vs flat format and dispatch."""
        with open(config_file, 'r') as f:
            content = f.read()

        if '[' in content:          # INI-style
            self._parse_ini(content)
        else:                       # old flat key=value format
            self._parse_flat(content)

    # ------------------------------------------------------------------
    # INI parser
    # ------------------------------------------------------------------

    def _parse_ini(self, content: str):
        parser = configparser.ConfigParser(inline_comment_prefixes=('#', ';'))
        parser.read_string(content)

        # [pipeline]
        if parser.has_section('pipeline'):
            sec = parser['pipeline']
            if 'forwarding_enabled' in sec:
                self.forwarding = sec.getboolean('forwarding_enabled')
            if 'forwarding' in sec:
                self.forwarding = sec.getboolean('forwarding')

        # [latencies]
        if parser.has_section('latencies'):
            for key, val in parser['latencies'].items():
                self.latency[key.upper()] = int(val)

        # [memory]
        if parser.has_section('memory'):
            sec = parser['memory']
            if 'virtual_size_bytes'  in sec:
                self.vm_virtual_size  = int(sec['virtual_size_bytes'])
            if 'physical_size_bytes' in sec:
                self.vm_physical_size = int(sec['physical_size_bytes'])
            if 'page_size_bytes'     in sec:
                self.vm_page_size     = int(sec['page_size_bytes'])
            if 'memory_size'         in sec:
                self.memory_size      = int(sec['memory_size'])

        # [vm]
        if parser.has_section('vm'):
            sec = parser['vm']
            if 'dtlb_entries'        in sec:
                self.vm_dtlb_entries       = int(sec['dtlb_entries'])
            if 'tlb_hit_latency'     in sec:
                self.vm_tlb_hit_latency    = int(sec['tlb_hit_latency'])
            if 'page_walk_latency'   in sec:
                self.vm_page_walk_latency  = int(sec['page_walk_latency'])
            if 'page_fault_latency'  in sec:
                self.vm_page_fault_latency = int(sec['page_fault_latency'])
            if 'replacement_policy'  in sec:
                self.vm_replacement_policy = sec['replacement_policy'].lower()

        # [cache]  (Phase-3 INI alternative to the old flat keys)
        if parser.has_section('cache'):
            sec = parser['cache']
            self._apply_cache_key('L1I_Size',              sec, 'l1i_config', 'size',               int)
            self._apply_cache_key('L1I_BlockSize',         sec, 'l1i_config', 'block_size',          int)
            self._apply_cache_key('L1I_Associativity',     sec, 'l1i_config', 'associativity',       int)
            self._apply_cache_key('L1I_Latency',           sec, 'l1i_config', 'latency',             int)
            self._apply_cache_key('L1I_ReplacementPolicy', sec, 'l1i_config', 'replacement_policy',  str.upper)
            self._apply_cache_key('L1D_Size',              sec, 'l1d_config', 'size',               int)
            self._apply_cache_key('L1D_BlockSize',         sec, 'l1d_config', 'block_size',          int)
            self._apply_cache_key('L1D_Associativity',     sec, 'l1d_config', 'associativity',       int)
            self._apply_cache_key('L1D_Latency',           sec, 'l1d_config', 'latency',             int)
            self._apply_cache_key('L1D_ReplacementPolicy', sec, 'l1d_config', 'replacement_policy',  str.upper)
            self._apply_cache_key('L2_Size',               sec, 'l2_config',  'size',               int)
            self._apply_cache_key('L2_BlockSize',          sec, 'l2_config',  'block_size',          int)
            self._apply_cache_key('L2_Associativity',      sec, 'l2_config',  'associativity',       int)
            self._apply_cache_key('L2_Latency',            sec, 'l2_config',  'latency',             int)
            self._apply_cache_key('L2_ReplacementPolicy',  sec, 'l2_config',  'replacement_policy',  str.upper)
            if 'l2_enabled' in sec:
                self.l2_enabled = sec.getboolean('l2_enabled')
            if 'mainmemory_latency' in sec:
                self.main_memory_latency = int(sec['mainmemory_latency'])

    def _apply_cache_key(self, cfg_key, section, cfg_dict_name, dict_key, converter):
        lower = cfg_key.lower()
        if lower in section:
            target = getattr(self, cfg_dict_name)
            raw = section[lower]
            target[dict_key] = converter(raw) if converter is not str.upper else raw.upper()

    # ------------------------------------------------------------------
    # Flat (legacy) parser
    # ------------------------------------------------------------------

    def _parse_flat(self, content: str):
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
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

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def get_latency(self, instruction: str) -> int:
        return self.latency.get(instruction.upper(), 1)

    def get_vm_config(self) -> dict:
        """Return a dict suitable for VirtualMemorySubsystem.__init__()."""
        return {
            "page_size_bytes":    self.vm_page_size,
            "num_frames":         self.vm_num_frames,
            "tlb_hit_latency":    self.vm_tlb_hit_latency,
            "page_walk_latency":  self.vm_page_walk_latency,
            "page_fault_latency": self.vm_page_fault_latency,
            "replacement_policy": self.vm_replacement_policy,
        }

    def get_tlb_config(self) -> dict:
        """Return a dict suitable for TLB.__init__()."""
        return {
            "num_entries":        self.vm_dtlb_entries,
            "replacement_policy": self.vm_replacement_policy,
        }

    def __repr__(self):
        return (f"Config(forwarding={self.forwarding}, "
                f"vm_frames={self.vm_num_frames}, "
                f"tlb_entries={self.vm_dtlb_entries}, "
                f"policy={self.vm_replacement_policy})")