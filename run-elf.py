#!/usr/bin/env python3

""" run-elf.py
"""

from io import BytesIO
from hexdump import hexdump
from elftools.elf.elffile import ELFFile
import sys, pathlib
sys.path.append(str(pathlib.Path("./m1n1/proxyclient")))

TARGET_CPU     = 4
RUST_HEAP_SIZE = 256 * (1024 * 1024)
RUST_CODE_SIZE = (1024 * 1024)
RUST_CTX_SIZE  = 0x100

class TargetELF(object):
    def __init__(self, path: str):
        self.path = path
        with open(path, "rb") as f:
            self.elf   = ELFFile(BytesIO(f.read()))
            self.entry = self.elf.header.e_entry


def exec_elf():
    img = TargetELF("./m2e-rs/target/t8112/release/m2e-rs")

    with GuardedHeap(u.heap) as heap:
        rust_code = heap.memalign((1024 * 1024), RUST_CODE_SIZE)
        rust_heap = heap.memalign((1024 * 1024), RUST_HEAP_SIZE)
        rust_ctx  = heap.malloc(RUST_CTX_SIZE);
        print(f"[*] Allocated for code @ {rust_code:016x}")
        print(f"[*] Allocated for heap @ {rust_heap:016x}")
        print(f"[*] Allocated for ctx  @ {rust_ctx:016x}")

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

        code_buf = iface.readmem(rust_code, 0x1000)
        print("[*] Context:")
        chexdump(code_buf)

        res = p.smp_call_sync(TARGET_CPU, entrypt, rust_heap, rust_ctx)
        print(f"[!] Exited with {res:016x}")

        res_ctx = iface.readmem(rust_ctx, RUST_CTX_SIZE)
        print("[*] Context:")
        chexdump(res_ctx)

# ==========================================================================

from m1n1.setup import *
p.smp_start_secondaries()


exec_elf()

