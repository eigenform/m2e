#!/usr/bin/env python3

import random
import itertools
import array
from hexdump import *
from pym2e.asm import *
from pym2e.experiment import *
from pym2e.setup import *
from pym2e.event import *
from pym2e.util import *

from m1n1.asm import ARMAsm

def lap_test(num_words: int, word_stride: int, randomized=False): 
    """
    Listing 1. from [https://predictors.fail/files/SLAP.pdf]

    Mostly plagarized from marcan, see: 
    [https://social.treehouse.systems/@marcan/113911770201326894]
    """

    # Maximum number of loop iterations when visiting the elements
    max_iters = num_words // word_stride

    # Array of 32-bit words
    BUF = [0] * num_words

    if randomized: 
        shuffled = list(range(1, num_words))
        random.shuffle(shuffled)
        for word_idx in range(0, num_words-1):
            BUF[word_idx] = shuffled[word_idx]
    else:
        for word_idx in range(0, num_words, word_stride):
            next_word_idx = (word_idx + word_stride)
            BUF[word_idx] = next_word_idx * 4

    BUF_DATA = array.array('I', BUF).tobytes()

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
        mov x4, #{max_iters}

    // Prepare the cache
    1:
        ldr w3, [x1, x3]
        sub x4, x4, #1
        cbnz x4, 1b

        mov x4, #{max_iters}
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
    res = tgt.smp_call_sync(snip.start, x0, x1)
    print(f"num_words={num_words}, word_stride={word_stride}, cycles={res}")


# =============================================================================

tgt = TargetMachine()
for num_words in [8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096]:
    lap_test(num_words, 4, randomized=False)
print()
for num_words in [8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096]:
    lap_test(num_words, 4, randomized=True)

