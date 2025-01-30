#!/usr/bin/env python3
# SPDX-License-Identifier: MIT

""" lap.py
This is plagarized from marcan's script, see:

[https://gist.github.com/marcan/b228f0ec239df2dc4971f574e19ad002]
[https://social.treehouse.systems/@marcan/113911770201326894]
"""

import random
import array
import statistics
from pym2e.asm import *
from pym2e.experiment import *
from pym2e.setup import *
from pym2e.event import *
from pym2e.util import *

from m1n1.asm import ARMAsm

def slap_listing1(num_words: int, word_stride: int,
                  randomized=False, ssbs=False):
    """ Try to observe the effects of the "load address predictor".

    num_words:
        The number of 32-bit entries in the array.
    word_stride:
        Number of entries skipped when performing each load.
    randomized:
        When true, perform randomized accesses (instead of sequential ones).
    ssbs:
        When true, set the SSBS bit (*permitting* speculative behavior).

    Test
    ====

    This is effectively the same as listing #1 from the
    [SLAP](https://predictors.fail/files/SLAP.pdf) paper (and the expected
    results are in figure #3).

    1. Create an array where each entry is an index that will be used to
       access some other entry in the array (effectively a linked-list).
       The pattern of accesses on the array looks like this:

           while (num_accesses != 0) {
              i = arr[i]
              num_accesses--;
           }

       The dependency on 'i' is carried through the entire loop, meaning
       that each access depends on the previous one.

       When 'randomized' is true, the entries are shuffled, and the set of
       load addresses is effectively random. Otherwise, each entry causes an
       access to some next-sequential entry, and the set of load addresses has
       an obvious pattern.

    2. Traverse some number of entries in the array, ensuring that each entry
       is resident in the L1D cache for the next set of accesses (note that
       this may not be the case if 'num_accesses * word_stride' is very large).
       Ideally this prevents us from measuring the effects of data prefetching
       that might occur in the sequential case.

    3. Measure the time it takes to traverse the same entries in the array.
       Since the accesses in all cases are guaranteed to be L1D cache hits,
       any observed speedup of the sequential case over the random case
       *must* be the result of some optimization that allows the dependency
       on the index 'i' to be resolved very early.

    """

    # Number of loads to-be-performed
    num_accesses = num_words // word_stride

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
            BUF[word_idx] = next_word_idx

    BUF_DATA = array.array('I', BUF).tobytes()
    #print("[*] Buffer size: {}B".format(len(BUF_DATA)))
    #print(BUF)

    buf = tgt.u.malloc(len(BUF_DATA))
    tgt.iface.writemem(buf, BUF_DATA)
    tgt.p.dc_cvau(buf, len(BUF_DATA))
    tgt.p.ic_ivau(buf, len(BUF_DATA))

    # Allow/prohibit speculatively-resolved loads
    if ssbs:
        tgt.msr(SSBS, 0x0000_0000_0000_1000)
    else:
        tgt.msr(SSBS, 0x0000_0000_0000_0000)

    # Enable use of PMC0 (which is always configured to count cycles)
    pmcr0_el1 = tgt.mrs(PMCR0_EL1)
    if pmcr0_el1 == 0:
        tgt.msr(PMCR0_EL1, 0x0000_0000_4000_0001)
    pmcr1_el1 = tgt.mrs(PMCR1_EL1)
    if pmcr1_el1 == 0:
        tgt.msr(PMCR1_EL1, 0xffff_ffff_ffff_ffff)

    code = tgt.u.malloc(0x1000)
    snip = ARMAsm(f"""
    // Read the cycle counter
    .macro read_pmc0 reg_scratch
        dsb ish
        isb
        mrs \\reg_scratch, s3_2_c15_c0_0
        isb
    .endm

    start:
        mov x4, #{num_accesses}
        mov x3, #0

    _prime_cache:
        ldr w3, [x1, x3, lsl #2]
        sub x4, x4, #1
        cbnz x4, _prime_cache

        // Reset loop counter and the array index
        mov x4, #{num_accesses}
        mov x3, #0

        // First measurement
        read_pmc0 x8

    _measured_accesses:
        ldr w3, [x1, x3, lsl #2]
        sub x4, x4, #1
        cbnz x4, _measured_accesses

        // Second measurement
        read_pmc0 x9

        // Return the difference
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
    print("   num_words={:5}, word_stride={:2}, num_accesses={:5}, cycles={:5}"
          .format(num_words, word_stride, num_accesses, median)
    )


# =============================================================================

tgt = TargetMachine()

print("[*] Sequential offsets (SSBS=1):")
for num_words in [8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192]:
    slap_listing1(num_words, 4, randomized=False, ssbs=True)
print("[*] Randomized offsets (SSBS=1):")
for num_words in [8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192]:
    slap_listing1(num_words, 4, randomized=True, ssbs=True)

print()

print("[*] Sequential offsets (SSBS=0):")
for num_words in [8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192]:
    slap_listing1(num_words, 4, randomized=False, ssbs=False)
print("[*] Randomized offsets (SSBS=0):")
for num_words in [8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192]:
    slap_listing1(num_words, 4, randomized=True, ssbs=False)

