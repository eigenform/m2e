
from enum import Enum

class EventUnit(Enum):
    CYCLES = 0
    UOPS   = 1


class EventDesc(object):
    """ Representing the definition of a particular PMC event """
    def __str__(self):
        return "evt={:02x} {}".format(self.idx, self.name)

    def __init__(self, idx: int, name: str, spec=False):
        assert idx  <= 0xff
        self.name = name
        self.idx  = idx
        self.spec = spec

class EventDb(object):
    """ A database of PMC events """
    def __init__(self):
        self.events_by_name = {}
        self.events_by_idx  = {}

    def add(self, desc: EventDesc):
        self.events_by_name[desc.name] = desc
        self.events_by_idx[desc.idx] = desc

    def idx_by_name(self, name: str) -> int:
        if self.events_by_name.get(name) == None:
            raise Exception(f"Event '{name}' is undefined")
        return self.events_by_name[name].idx

    def name_by_idx(self, idx: int) -> str:
        if self.events_by_idx.get(idx) == None:
            return f"unk_{idx:02x}"
        else:
            return self.events_by_idx[idx].name


class PmcConfig(object):
    """ Container for requested PMC configuration state """
    def __str__(self):
        return "{}".format(self.event)
    def __repr__(self):
        return "{}".format(self.event)

    def __init__(self, idx: int):
        assert idx <= 9
        self.static = (idx < 2)
        self.idx = idx
        self.event = None
        self.enabled = False

    def set_event(self, event: EventDesc):
        if self.static:
            raise Exception(f"PMC{self.idx} is a fixed counter")
        self.event = event

    def enable(self):
        self.enabled = True

    def disable(self):
        self.enabled = False

    def render_clear(self):
        match self.idx:
            case 0: msr = "s3_2_c15_c0_0"
            case 1: msr = "s3_2_c15_c1_0"
            case 2: msr = "s3_2_c15_c2_0"
            case 3: msr = "s3_2_c15_c3_0"
            case 4: msr = "s3_2_c15_c4_0"
            case 5: msr = "s3_2_c15_c5_0"
            case 6: msr = "s3_2_c15_c6_0"
            case 7: msr = "s3_2_c15_c7_0"
            case 8: msr = "s3_2_c15_c9_0"
            case 9: msr = "s3_2_c15_c10_0"
            case _: raise Exception(f"Invalid PMC index {self.idx}")
        return "msr {}, xzr // Clear PMC{}".format(msr, self.idx)

class PmuConfig(object):
    """ Representing the requested PMU configuration for some experiment """
    def __init__(self):
        self.pmc = [ PmcConfig(idx) for idx in range(0, 10) ]

    def enable(self, idx: int):
        """ Configure a counter """
        self.pmc[idx].enable()

    def set_event(self, idx: int, event: EventDesc):
        if isinstance(event, EventDesc):
            self.pmc[idx].set_event(event)
        elif isinstance(event, int):
            val = event & 0xff
            desc = EventDesc(val, "event_{:02x}".format(val))
            self.pmc[idx].set_event(desc)

    def disable(self, idx: int):
        """ Clear the configuration for a particular counter """
        self.pmc[idx].disable()

    def clear(self):
        self.pmc0_enabled = False
        self.pmc1_enabled = False
        for pmc in self.pmc:
            pmc.disable()

    def print(self):
        for idx, pmc in enumerate(self.pmc):
            print(f"PMC{idx}: {pmc}")

    def render_pmcr0_write(self, idt=0):
        """ Emit a write to PMCR0_EL1 (clobbering x0) """
        tgt_val = self.get_msr_bits()['pmcr0']
        asm = ""
        if tgt_val == 0: 
            asm += " "*idt + "// Skipped PMCR0_EL1\n"
        else:
            asm += " "*idt + "// Set PMCR0_EL1\n"
            asm += " "*idt + f"mov x0, #0x{tgt_val:x}\n"
            asm += " "*idt + f"msr s3_1_c15_c0_0, x0\n"
        return asm

    def render_pmcr1_write(self, idt=0):
        """ Emit a write to PMCR1_EL1 (clobbering x0) """
        tgt_val = self.get_msr_bits()['pmcr1']
        asm = ""
        if tgt_val == 0: 
            asm += " "*idt + "// Skipped PMCR1_EL1\n"
        else:
            asm += " "*idt + "// Set PMCR1_EL1\n"
            asm += " "*idt + f"mov x0, xzr\n"
            asm += " "*idt + f"orr x0, x0, #0x{tgt_val:x}\n"
            asm += " "*idt + f"msr s3_1_c15_c1_0, x0\n"
            asm += " "*idt + f"isb\n"
        return asm

    def render_pmesr0_write(self, idt=0):
        """ Emit a write to PMESR0_EL1 (clobbering x0) """
        tgt_val = self.get_msr_bits()['pmesr0']
        asm = ""
        if tgt_val == 0: 
            asm += " "*idt + "// Skipped PMESR0_EL1\n"
        else:
            asm += " "*idt + "// Set PMESR0_EL1\n"
            asm += " "*idt + f"mov x0, xzr\n"
            asm += " "*idt + f"orr x0, x0, #0x{tgt_val:x}\n"
            asm += " "*idt + f"msr s3_1_c15_c5_0, x0\n"
            asm += " "*idt + f"isb\n"
        return asm

    def render_pmesr1_write(self, idt=0):
        """ Emit a write to PMESR1_EL1 (clobbering x0) """
        tgt_val = self.get_msr_bits()['pmesr1']
        asm = ""
        if tgt_val == 0: 
            asm += " "*idt + "// Skipped PMESR1_EL1\n"
        else:
            asm += " "*idt + "// Set PMESR1_EL1\n"
            asm += " "*idt + f"mov x0, xzr\n"
            asm += " "*idt + f"orr x0, x0, #0x{tgt_val:x}\n"
            asm += " "*idt + f"msr s3_1_c15_c6_0, x0\n"
            asm += " "*idt + f"isb\n"
        return asm

    def get_msr_bits(self):
        """ Return the set of PMC register values for this configuration """
        res = { 'pmcr0': 0, 'pmcr1': 0, 'pmesr0': 0, 'pmesr1': 0, }
        for pmc in self.pmc:
            if pmc.enabled:
                match pmc.idx:
                    case val if val <= 7:
                        res['pmcr0']  |= (1 << pmc.idx)
                        res['pmcr1']  |= (1 << pmc.idx) << 16
                    case 8:
                        res['pmcr0']  |= (1 << 32)
                        res['pmcr1']  |= (1 << 48)
                    case 9:
                        res['pmcr0']  |= (1 << 33)
                        res['pmcr1']  |= (1 << 49)
                    case _: 
                        raise Exception("???")
        for pmc in self.pmc[2:]:
            if (pmc.event != None) and (pmc.enabled):
                match pmc.idx:
                    case 2: res['pmesr0'] |= (pmc.event.idx << 0)
                    case 3: res['pmesr0'] |= (pmc.event.idx << 8)
                    case 4: res['pmesr0'] |= (pmc.event.idx << 16)
                    case 5: res['pmesr0'] |= (pmc.event.idx << 24)
                    case 6: res['pmesr1'] |= (pmc.event.idx << 0)
                    case 7: res['pmesr1'] |= (pmc.event.idx << 8)
                    case 8: res['pmesr1'] |= (pmc.event.idx << 16)
                    case 9: res['pmesr1'] |= (pmc.event.idx << 24)
                    case _:
                        raise Exception("???")
        return res


