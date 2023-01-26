#!/usr/bin/env python3

""" run-elf.py
I'm using this to load and run an ELF on a particular core.
"""

from elftools.elf.elffile import ELFFile
from elftools.elf.relocation import RelocationSection
from elftools.elf.enums import ENUM_RELOC_TYPE_AARCH64

from io import BytesIO
from hexdump import hexdump
from construct import *
from struct import pack, unpack
import sys, pathlib
sys.path.append(str(pathlib.Path("./m1n1/proxyclient")))

def chunks(seq, size):
    return [seq[pos:pos + size] for pos in range(0, len(seq), size)]

TARGET_CPU = 4
HEAP_SIZE  = 512 * (1024 * 1024)
CODE_SIZE  = (1024 * 1024)

class TargetELF(object):
    """ Some ELF that we're going to load and execute """
    def __init__(self, path: str):
        self.path = path
        with open(path, "rb") as f:
            self.elf   = ELFFile(BytesIO(f.read()))

    def load(self, base: int) -> int:
        self.entry = base + self.elf.header.e_entry
        # Load all of the segments
        for seg in self.elf.iter_segments():
            if seg.header['p_type'] == 'PT_LOAD':
                data  = seg.data()
                dlen  = len(data)
                addr  = base + seg.header['p_paddr']
                print(f"[*] Writing segment to {addr:016x} ({dlen:016x})")
                iface.writemem(addr, data)
                p.dc_cvau(addr, dlen)
                p.ic_ivau(addr, dlen)

        # Handle relocations (did I do this right?? no clue!)
        rela_dyn = self.elf.get_section_by_name(".rela.dyn")
        for reloc in rela_dyn.iter_relocations():
            r_info = reloc['r_info']
            assert r_info == ENUM_RELOC_TYPE_AARCH64['R_AARCH64_RELATIVE']
            assert reloc.is_RELA()
            r_offset = reloc['r_offset']
            r_addend = reloc['r_addend']
            patch_addr = base + r_offset
            sym_addr   = base + r_addend 
            print(f"[*] RELA @ {patch_addr:016x} => {sym_addr:016x}")
            p.write64(patch_addr, sym_addr)
        return self.entry

# See 'm2e-rs/src/common.rs' for the definition of this struct.
ResultContext = Struct(
    "result"  / Hex(Int64ul),
    "payload" / Hex(Int64ul),
    "len"     / Hex(Int64ul),
)

def exec_elf(elf_file: str) -> ResultContext:
    """ Load and execute an ELF image on-top of m1n1.
    The target ELF is expected to return a pointer to a [ResultContext]
    which describes the address/length of some result data.
    """
    with GuardedHeap(u.heap) as heap:
        img = TargetELF(elf_file)
        code = heap.memalign((1024 * 1024), CODE_SIZE)
        heap = heap.memalign((1024 * 1024), HEAP_SIZE)
        print(f"[*] Allocated for code @ {code:016x}")
        print(f"[*] Allocated for heap @ {heap:016x}")

        entrypt = img.load(code)
        print(f"[*] Entrypoint: {entrypt:016x}")
        print("[*] Running payload ...")

        res = p.smp_call_sync(TARGET_CPU, entrypt, heap)
        print(f"[!] Returned with res={res:016x}")

        ctx = iface.readstruct(res, ResultContext)
        return ctx

# ==========================================================================
# In case it's not obvious, m1n1 runs on cpu0. If you're trying to interact 
# with other cores, you need to initialize them:
#
# - You *need* to enable the secondary cores if you're using them
# - You *need* to enable the MMU on secondary cores if you expect your machine 
#   to not hard-reset every time you access RAM

if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("usage: ./run-elf.py <path to ELF image>")
        exit()

    elf_path = str(pathlib.Path(sys.argv[1]).resolve())

    from m1n1.setup import *
    p.smp_start_secondaries()
    p.mmu_init_secondary(TARGET_CPU)
    print()

    ctx = exec_elf(elf_path)
    print(ctx)

    ResultStruct = Struct(
        "event" / Array(0x100, 
            Struct("test" / Array(0x100, Struct("ctr" / Array(8, Int64ul)))))
    )

    if (ctx.payload != 0) and (ctx.len != 0):
        res_data = iface.readmem(ctx.payload, ctx.len)
        results = ResultStruct.parse(res_data)
        for (eidx, event) in enumerate(results.event):

            by_ctr = [ [], [], [], [], [], [], [], [] ]
            for test in event.test:
                for (ctr_idx, ctr_val) in enumerate(test.ctr):
                    by_ctr[ctr_idx].append(ctr_val)

            ctr_data = {}
            for (ctr_idx, ctr_vals) in enumerate(by_ctr):
                if sum(ctr_vals) == 0: 
                    continue
                else:
                    ctr_data[ctr_idx] = {
                        'min': min(ctr_vals),
                        'avg': sum(ctr_vals) // len(ctr_vals),
                        'max': max(ctr_vals),
                    }

            if len(ctr_data) != 0:
                mins = [ data['min'] for (key, data) in ctr_data.items() ][0]
                avgs = [ data['avg'] for (key, data) in ctr_data.items() ][0]
                maxs = [ data['max'] for (key, data) in ctr_data.items() ][0]
                print(f"{eidx:02x}: ", 
                      f"min={mins:5}, avg={avgs:5} max={maxs:5}")



