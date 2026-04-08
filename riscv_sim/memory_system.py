from cache import Cache


class MemorySystem:
    def __init__(self, l1i_config, l1d_config, l2_config, main_memory_latency, memory_size=4096):
        self.memory_size = memory_size
        self.main_memory = bytearray(memory_size)
        self.text_memory = {}
        self.main_memory_latency = main_memory_latency

        self.l1i = Cache(
            l1i_config["size"],
            l1i_config["block_size"],
            l1i_config["associativity"],
            l1i_config["latency"],
            l1i_config.get("replacement_policy", "LRU"),
            "L1I",
        )

        self.l1d = Cache(
            l1d_config["size"],
            l1d_config["block_size"],
            l1d_config["associativity"],
            l1d_config["latency"],
            l1d_config.get("replacement_policy", "LRU"),
            "L1D",
        )

        self.l2 = Cache(
            l2_config["size"],
            l2_config["block_size"],
            l2_config["associativity"],
            l2_config["latency"],
            l2_config.get("replacement_policy", "LRU"),
            "L2",
        )

    def load_program(self, instructions, data_memory):
        self.text_memory.clear()
        for i, instr in enumerate(instructions):
            self.text_memory[i * 4] = instr

        for addr, val in data_memory.items():
            self._write_word_to_memory(addr, val)

    def get_memory(self):
        return self.main_memory

    def get_instruction(self, address):
        address = address & ~3
        return self.text_memory.get(address, None)

    def _read_block_from_memory(self, address, block_size):
        base_addr = address - (address % block_size)
        block = bytearray(block_size)
        for i in range(block_size):
            block[i] = self.main_memory[(base_addr + i) % len(self.main_memory)]
        return block

    def _write_word_to_memory(self, address, value):
        addr = address % len(self.main_memory)
        value = value & 0xFFFFFFFF
        self.main_memory[addr] = value & 0xFF
        self.main_memory[(addr + 1) % len(self.main_memory)] = (value >> 8) & 0xFF
        self.main_memory[(addr + 2) % len(self.main_memory)] = (value >> 16) & 0xFF
        self.main_memory[(addr + 3) % len(self.main_memory)] = (value >> 24) & 0xFF

    def _write_block_to_memory(self, address, block_data):
        base_addr = address % len(self.main_memory)
        for i, b in enumerate(block_data):
            self.main_memory[(base_addr + i) % len(self.main_memory)] = b

    def _read_word_from_block(self, block_data, address, block_size):
        offset = address & (block_size - 1)
        return int.from_bytes(block_data[offset:offset + 4], byteorder="little", signed=False)

    def _write_back_if_dirty(self, evicted_info):
        if evicted_info is None:
            return 0

        if evicted_info["dirty"]:
            self._write_block_to_memory(evicted_info["address"], evicted_info["data"])
            return self.main_memory_latency

        return 0

    def _dummy_instruction_block(self, block_size):
        return bytearray(block_size)

    def access(self, address, access_type, value=None):

        address = address & ~3

        if access_type == "IF":
            instr = self.get_instruction(address)
            if instr is None:
                return self.main_memory_latency, False

            hit_l1, lat1, _, _ = self.l1i.read(address)
            if hit_l1:
                return lat1, True

            hit_l2, lat2, l2_block, _ = self.l2.read(address)
            if hit_l2:
                evicted_l1 = self.l1i.fill_line(address, l2_block)
                extra_lat = self._write_back_if_dirty(evicted_l1)
                return lat1 + lat2 + extra_lat, True

            block = self._dummy_instruction_block(self.l2.block_size)

            evicted_l2 = self.l2.fill_line(address, block)
            extra_lat = self._write_back_if_dirty(evicted_l2)

            evicted_l1 = self.l1i.fill_line(address, block)
            extra_lat += self._write_back_if_dirty(evicted_l1)

            return lat1 + lat2 + self.main_memory_latency + extra_lat, False

        elif access_type == "LOAD":
            hit_l1, lat1, _, _ = self.l1d.read(address)
            if hit_l1:
                return lat1, True

            hit_l2, lat2, l2_block, _ = self.l2.read(address)
            if hit_l2:
                evicted_l1 = self.l1d.fill_line(address, l2_block)
                extra_lat = self._write_back_if_dirty(evicted_l1)
                return lat1 + lat2 + extra_lat, True

            block = self._read_block_from_memory(address, self.l2.block_size)

            evicted_l2 = self.l2.fill_line(address, block)
            extra_lat = self._write_back_if_dirty(evicted_l2)

            evicted_l1 = self.l1d.fill_line(address, block)
            extra_lat += self._write_back_if_dirty(evicted_l1)

            return lat1 + lat2 + self.main_memory_latency + extra_lat, False

        elif access_type == "STORE":
            if value is None:
                raise ValueError("STORE access requires a value")

            value = value & 0xFFFFFFFF

            hit_l1, lat1, _, _ = self.l1d.write(address, value)
            if hit_l1:
                self.l2.invalidate(address)
                return lat1, True

            hit_l2, lat2, l2_block, _ = self.l2.read(address)
            if hit_l2:
                evicted_l1 = self.l1d.fill_line(address, l2_block, write_value=value)
                extra_lat = self._write_back_if_dirty(evicted_l1)

                self.l2.invalidate(address)

                return lat1 + lat2 + extra_lat, True

            block = self._read_block_from_memory(address, self.l1d.block_size)
            evicted_l1 = self.l1d.fill_line(address, block, write_value=value)
            extra_lat = self._write_back_if_dirty(evicted_l1)

            self.l2.invalidate(address)

            return lat1 + lat2 + self.main_memory_latency + extra_lat, False

        else:
            raise ValueError(f"Unknown access_type: {access_type}")

    def get_miss_rate(self):
        return {
            "L1I_miss_rate": self.l1i.get_miss_rate(),
            "L1D_miss_rate": self.l1d.get_miss_rate(),
            "L2_miss_rate": self.l2.get_miss_rate(),
        }

    def get_stats(self):
        return {
            "L1I": self.l1i.get_stats(),
            "L1D": self.l1d.get_stats(),
            "L2": self.l2.get_stats(),
        }