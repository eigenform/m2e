#!/usr/bin/env python3
# SPDX-License-Identifier: MIT

""" lap.py
See Listing #1 from [https://predictors.fail/files/SLAP.pdf].

This is plagarized from marcan, see: 
[https://gist.github.com/marcan/b228f0ec239df2dc4971f574e19ad002]
[https://social.treehouse.systems/@marcan/113911770201326894]
"""


import random
import itertools
import array
import statistics
from hexdump import *
from pym2e.asm import *
from pym2e.experiment import *
from pym2e.setup import *
from pym2e.event import *
from pym2e.util import *

from m1n1.asm import ARMAsm

def lap_test(num_words: int, word_stride: int, randomized=False): 
    # Number of loads to-be-performed
    num_accesses = num_words // word_stride

    print(f"[*] num_words={num_words}, word_stride={word_stride}, num_accesses={num_accesses}")

    # Array of 32-bit words
    BUF = [0] * num_words

    if randomized: 
        shuffled = list(range(1, num_words))
        random.shuffle(shuffled)
        for word_idx in range(0, num_words-1):
            BUF[word_idx] = shuffled[word_idx] * 4
            #BUF[word_idx] = shuffled[word_idx]
    else:
        for word_idx in range(0, num_words, word_stride):
            next_word_idx = (word_idx + word_stride)
            BUF[word_idx] = next_word_idx * 4
            #BUF[word_idx] = next_word_idx

    #print(BUF)
    BUF_DATA = array.array('I', BUF).tobytes()
    #print("[*] Buffer size: {}B".format(len(BUF_DATA)))

    buf = tgt.u.malloc(len(BUF_DATA))
    tgt.iface.writemem(buf, BUF_DATA)
    tgt.p.dc_cvau(buf, len(BUF_DATA))
    tgt.p.ic_ivau(buf, len(BUF_DATA))

    pmcr0_el1 = tgt.mrs(PMCR0_EL1)
    if pmcr0_el1 == 0:
        tgt.msr(PMCR0_EL1, 0x0000_0000_4000_0001)

    pmcr1_el1 = tgt.mrs(PMCR1_EL1)
    if pmcr1_el1 == 0:
        tgt.msr(PMCR1_EL1, 0xffff_ffff_ffff_ffff)

    code = tgt.u.malloc(0x1000)
    snip = ARMAsm(f"""
    .macro read_pmc0 reg_scratch
        dsb ish
        isb
        mrs \\reg_scratch, s3_2_c15_c0_0
        isb
    .endm

    start:
        mov x4, #{num_accesses}
        mov x3, #0

    // Prepare the cache
    1:
        ldr w3, [x1, x3]
        sub x4, x4, #1
        cbnz x4, 1b

        mov x4, #{num_accesses}
        mov x3, #0
        read_pmc0 x8

    // Timed access
    2:
        ldr w3, [x1, x3]
        sub x4, x4, #1
        cbnz x4, 2b

        read_pmc0 x9
        sub x0, x9, x8
        ret
    """, code)

    tgt.iface.writemem(code, snip.data)
    tgt.p.dc_cvau(code, len(snip.data))
    tgt.p.ic_ivau(code, len(snip.data))

    x0 = 0
    x1 = buf
    results = []
    for _ in range(32):
        res = tgt.smp_call_sync(snip.start, x0, x1)
        results.append(res)
    median = int(statistics.median(results))
    print(f"   median: {median} cyc")


# =============================================================================

tgt = TargetMachine()

#hid11 = tgt.mrs((3, 0, 15, 11, 0))
#print(f"HID11={hid11:016x}")
#tgt.msr((3, 0, 15, 11, 0), hid11 | (1 << 30))

print("Sequential offsets:")
for num_words in [8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192]:
    lap_test(num_words, 4, randomized=False)

print()
print("Randomized offsets:")
for num_words in [8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192]:
    lap_test(num_words, 4, randomized=True)


