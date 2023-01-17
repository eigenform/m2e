#!/usr/bin/env python3

""" run-elf.py
"""

from io import BytesIO
from hexdump import hexdump
from elftools.elf.elffile import ELFFile
from construct import *
import sys, pathlib
sys.path.append(str(pathlib.Path("./m1n1/proxyclient")))

TARGET_CPU     = 4
RUST_HEAP_SIZE = 256 * (1024 * 1024)
RUST_CODE_SIZE = (1024 * 1024)

class TargetELF(object):
    def __init__(self, path: str):
        self.path = path
        with open(path, "rb") as f:
            self.elf   = ELFFile(BytesIO(f.read()))
            self.entry = self.elf.header.e_entry

# See 'm2e-rs/src/common.rs' for the definition of this struct.
ResultContext = Struct(
    "result"  / Hex(Int64ul),
    "payload" / Hex(Int64ul),
    "len"     / Hex(Int64ul),
)

def exec_elf():
    img = TargetELF("./m2e-rs/target/t8112/release/m2e-rs")
    with GuardedHeap(u.heap) as heap:
        rust_code = heap.memalign((1024 * 1024), RUST_CODE_SIZE)
        rust_heap = heap.memalign((1024 * 1024), RUST_HEAP_SIZE)
        print(f"[*] Allocated for code @ {rust_code:016x}")
        print(f"[*] Allocated for heap @ {rust_heap:016x}")

        for seg in img.elf.iter_segments():
            if seg.header['p_type'] == 'PT_LOAD':
                seg_data = seg.data()
                seg_len  = len(seg_data)
                paddr = seg.header['p_paddr']
                dst_addr = rust_code + paddr
                print(f"[*] Writing segment to {dst_addr:016x} ({seg_len:016x})")
                iface.writemem(dst_addr, seg_data)
                p.dc_cvau(dst_addr, seg_len)
                p.ic_ivau(dst_addr, seg_len)

        entrypt = rust_code + img.entry 
        print(f"[*] Entrypoint: {entrypt:016x}")

        res = p.smp_call_sync(TARGET_CPU, entrypt, rust_heap)
        print(f"[!] Returned with res={res:016x}")
        ctx = iface.readstruct(res, ResultContext)
        print(ctx)

# ==========================================================================
# In case it's not obvious, m1n1 runs on cpu0. If you're trying to interact 
# with other cores, you need to initialize them:
#
# - You *need* to enable the secondary cores if you're using them
# - You *need* to enable the MMU on secondary cores if you expect your machine 
#   to not hard-reset every time you access RAM


from m1n1.setup import *
p.smp_start_secondaries()
p.mmu_init_secondary(TARGET_CPU)

exec_elf()


