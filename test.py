#!/usr/bin/env python3

import sys, pathlib
sys.path.append(str(pathlib.Path("./m1n1/proxyclient")))
from m1n1.setup import *
from m1n1 import asm


ASM_CLEAR_COUNTERS = """
_clear_counters:
    msr s3_2_c15_c0_0, xzr
    msr s3_2_c15_c1_0, xzr
    msr s3_2_c15_c2_0, xzr
    msr s3_2_c15_c3_0, xzr

    msr s3_2_c15_c4_0, xzr
    msr s3_2_c15_c5_0, xzr
    msr s3_2_c15_c6_0, xzr
    msr s3_2_c15_c7_0, xzr

    msr s3_2_c15_c9_0, xzr
    msr s3_2_c15_c10_0, xzr
    nop
    isb

    nop
    nop
    nop
    nop

    nop
    nop
    nop
    nop
"""

ASM_SET_PMCR0 = """
_set_pmcr0:
    nop
    mov x0, #{imm}
    msr s3_1_c15_c0_0, x0
    isb
"""
ASM_CLEAR_PMCR0 = """
_clear_pmcr0:
    msr s3_1_c15_c0_0, xzr
    isb
"""
ASM_SET_PMCR1 = """
_set_pmcr1:
    mov x0, xzr
    orr x0, x0, #{imm}
    msr s3_1_c15_c1_0, x0
    isb
"""
ASM_SET_PMESR0 = """
_set_pmesr0:
    movz x0, #{imm_15_00}
    movk x0, #{imm_32_16}, lsl 16
    msr s3_1_c15_c5_0, x0
    isb
"""
ASM_SET_PMESR1 = """
_set_pmesr1:
    movz x0, #{imm_15_00}
    movk x0, #{imm_32_16}, lsl 16
    msr s3_1_c15_c6_0, x0
    isb
"""
ASM_CLEAR_PMU_CFG = """
_clear_pmu_config:
    msr s3_1_c15_c1_0, xzr
    msr s3_1_c15_c5_0, xzr
    msr s3_1_c15_c6_0, xzr
    isb
"""
ASM_READ_PMC2 = """
_return_pmc2:
    mrs x0, s3_2_c15_c2_0
    ret
"""
ASM_READ_PMC3 = """
_return_pmc3:
    mrs x0, s3_2_c15_c3_0
    ret
"""
ASM_READ_PMC4 = """
_return_pmc4:
    mrs x0, s3_2_c15_c4_0
    ret
"""
ASM_READ_PMC5 = """
_return_pmc5:
    mrs x0, s3_2_c15_c5_0
    ret
"""
ASM_READ_PMC6 = """
_return_pmc6:
    mrs x0, s3_2_c15_c6_0
    ret
"""
ASM_READ_PMC7 = """
_return_pmc7:
    mrs x0, s3_2_c15_c7_0
    ret
"""
ASM_READ_PMC8 = """
_return_pmc8:
    mrs x0, s3_2_c15_c9_0
    ret
"""
ASM_READ_PMC9 = """
_return_pmc9:
    mrs x0, s3_2_c15_c10_0
    ret
"""


class TestEmitter():
    """ Template for a test gadget """
    def __init__(self):
        return

    def emit(self, pmc_idx: int, evt_idx: int, body="\n") -> str:
        if evt_idx > 0xff:
            raise Exception(f"Invalid event idx 0x{evt_idx:02x}")
        if pmc_idx not in [ 2, 3, 4, 5, 6, 7, 8, 9 ]:
            raise Exception("Invalid PMC index f{pmc_idx}")

        if pmc_idx in [2, 3, 4, 5, 6, 7]:
            pmcr0_imm = (1 << pmc_idx)
            pmcr1_imm = (1 << pmc_idx) << 16
        elif pmc_idx == 8:
            pmcr0_imm = (1 << 32)
            pmcr1_imm = (1 << 48)
        elif pmc_idx == 9:
            pmcr0_imm = (1 << 33)
            pmcr1_imm = (1 << 49)
        else:
            raise Exception("Unreachable")

        asm = ""
        asm += ASM_CLEAR_COUNTERS
        asm += ASM_SET_PMCR1.format(imm=hex(pmcr1_imm))

        if pmc_idx in [ 2, 3, 4, 5 ]:
            val = 0x00000000
            val |= evt_idx << (8 * (pmc_idx - 2))
            lo = (val >> 0) & 0xffff
            hi = (val >> 16) & 0xffff
            asm += ASM_SET_PMESR0.format(
                    imm_15_00=hex(lo), 
                    imm_32_16=hex(hi)
            )
        elif pmc_idx in [ 6, 7, 8, 9 ]:
            val = 0x00000000
            val |= evt_idx << (8 * (pmc_idx - 6))
            lo = (val >> 0) & 0xffff
            hi = (val >> 16) & 0xffff
            asm += ASM_SET_PMESR1.format(
                    imm_15_00=hex(lo), 
                    imm_32_16=hex(hi)
            )
        else:
            raise Exception("Unreachable")

        asm += ASM_SET_PMCR0.format(imm=hex(pmcr0_imm))
        asm += body
        asm += ASM_CLEAR_PMCR0
        asm += ASM_CLEAR_PMU_CFG
        match pmc_idx:
            case 2: asm += ASM_READ_PMC2
            case 3: asm += ASM_READ_PMC3
            case 4: asm += ASM_READ_PMC4
            case 5: asm += ASM_READ_PMC5
            case 6: asm += ASM_READ_PMC6
            case 7: asm += ASM_READ_PMC7
            case 8: asm += ASM_READ_PMC8
            case 9: asm += ASM_READ_PMC9
            case _:
                raise Exception("Unreachable")
        return asm


# m1n1 is running on the primary core (cpu0). 
# You need to initialize the others by calling smp_start_secondaries().
p.smp_start_secondaries()

# This is not particularly efficient, but I guess it's fine for now.

target_cpu = 4
emitter = TestEmitter()
code = u.malloc(0x0800)

for pmc_idx in [ 2, 3, 4, 5 ]:
    print("===================================")
    results = {}
    for evt_idx in range(0x01, 0x100):
        print(f"[*] Emitting test PMC{pmc_idx}, evt_idx={evt_idx:02x} ...")
        emitted_asm = emitter.emit(pmc_idx, evt_idx)
        prog = asm.ARMAsm(emitted_asm, code)
        iface.writemem(code, prog.data)
        p.dc_cvau(code, len(prog.data))
        p.ic_ivau(code, len(prog.data))
        ret = p.smp_call_sync(target_cpu, code)
        results[evt_idx] = ret

    print(f"[*] Results for PMC{pmc_idx}")
    for idx, val in results.items():
        print(f"evt={idx:02x}: {val:016x} ({val})")
    print("")


