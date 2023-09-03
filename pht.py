#!/usr/bin/env python3

import random
import itertools
from pym2e.asm import *
from pym2e.experiment import *
from pym2e.setup import *
from pym2e.event import *
from pym2e.util import *

class PhtEntry(object):
    def __init__(self, tdepth, ntdepth):
        self.tdepth = tdepth
        self.ntdepth = ntdepth
        self.direction = 0
    def predict(self):
        return self.direction
    def update(self, outcome):
        if outcome != self.direction:
            return
        else:
            return

class PhtState(object):
    def __init__(self):
        self.entries = []


SINGLE_CBNZ = MyExperiment(AssemblerTemplate(
"""
_test_brn:
    cbnz x0, _test_tgt
.p2align {tgt_align}
_test_tgt:
"""
))

SINGLE_CBZ = MyExperiment(AssemblerTemplate(
"""
_test_brn:
    cbz x0, _test_tgt
.p2align {tgt_align}
_test_tgt:
"""
))

def test_pht_simple_loop():
    code = SINGLE_CBNZ.compile(0xc5, addr=0x09_0000_0000, tgt_align=2)
    tgt.write_payload(code.start, code.data)

    # 0000000000000001...
    ctr = SingleCounter(16)

    results = []
    x0_vals = []
    for _ in range(0, 512):
        x0 = ctr.output()
        res = tgt.smp_call_sync(code.start, x0)
        results.append(res)
        x0_vals.append(x0)
        ctr.next()

    print("[*] mispredictions")
    print_samples_history(results)
    print("[*] x0 inputs")
    print_samples_history(x0_vals)
    print()

def test_pht_counters_1():
    code = SINGLE_CBNZ.compile(0xc5, addr=0x09_0000_0000, tgt_align=2)
    tgt.write_payload(code.start, code.data)

    # 0000000000000011...
    ctr = PatternCounter([
        0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1
    ])

    results = []
    x0_vals = []
    for _ in range(0, 512):
        x0 = ctr.output()
        res = tgt.smp_call_sync(code.start, x0)
        results.append(res)
        x0_vals.append(x0)
        ctr.next()

    print("[*] mispredictions")
    print_samples_history(results)
    print("[*] x0 inputs")
    print_samples_history(x0_vals)
    print()


def test_pht_counters():
    """
    3 mispredictions move from 'taken' to 'not-taken'
    5 mispredictions move from 'not-taken' to 'taken'
    """
    code = SINGLE_CBNZ.compile(0xc5, addr=0x09_0000_0000, tgt_align=2)
    tgt.write_payload(code.start, code.data)
    ctr = FlipCounter(16)

    results = []
    x0_vals = []
    for _ in range(0, 512):
        x0 = ctr.output()
        res = tgt.smp_call_sync(code.start, x0)
        results.append(res)
        x0_vals.append(x0)
        ctr.next()

    print("[*] mispredictions")
    print_samples_history(results)
    print("[*] x0 inputs")
    print_samples_history(x0_vals)
    print()


def test_pht_defeat():
    code = SINGLE_CBNZ.compile(0xc5, addr=0x09_0000_0000, tgt_align=2)
    tgt.write_payload(code.start, code.data)
    ctr = FlipCounter(16)

    results = []
    x0_vals = []
    for _ in range(0, 512):
        x0 = ctr.output()
        res = tgt.smp_call_sync(code.start, x0)
        results.append(res)
        x0_vals.append(x0)
        ctr.next()

    print("[*] mispredictions")
    print_samples_history(results)
    print("[*] x0 inputs")
    print_samples_history(x0_vals)
    print()

    ctr = PatternCounter([0,0,0] + [ 1,0 ] * 256)
    results = []
    x0_vals = []
    for _ in range(0, 512):
        x0 = ctr.output()
        res = tgt.smp_call_sync(code.start, x0)
        results.append(res)
        x0_vals.append(x0)
        ctr.next()

    print("[*] mispredictions {}".format(samples_to_dist(results)))
    print_samples_history(results)

    print("[*] x0 inputs")
    print_samples_history(x0_vals)

def test_uncorrelated():
    """ Using a random outcome, it's obvious that the branch in SINGLE_CBNZ
    is not correlated with any previous part of global history. 
    """
    code = SINGLE_CBNZ.compile(0xc5, addr=0x09_0000_0000, tgt_align=2)
    tgt.write_payload(code.start, code.data)

    results = []
    x0_vals = []
    for _ in range(0, 512):
        x0 = random.getrandbits(1)
        res = tgt.smp_call_sync(code.start, x0)
        results.append(res)
        x0_vals.append(x0)

    print("[*] mispredictions")
    print_samples_history(results)
    print("[*] x0 inputs")
    print_samples_history(x0_vals)
    print()

# =============================================================================

PHT_1 = MyExperiment(AssemblerTemplate(
"""
_train_brn:
    cbnz x0, #4

.p2align 19
set_bit {bits}
_test_brn:
    cbnz x1, #4
"""
))

def test_pht_alias():
    """ Try to discover where PHT entries might be aliasing? """
    n = 4
    bits = list(range(2, 19))
    comb = list(itertools.combinations(bits, n))
    num_tests = len(comb)
    print(f"[*] Trying {num_tests} combinations of {n} bits ...", flush=True)
    random.shuffle(comb)

    for (i, set_bits) in enumerate(comb):
        s = ",".join(str(x) for x in list(set_bits))

        code = PHT_1.compile(0xc5, addr=0x09_0000_0000, bits=s)
        tgt.write_payload(code.start, code.data)

        train_brn = code._train_brn
        test_brn  = code._test_brn

        results = []
        x0 = 1
        x1 = 1
        res = tgt.smp_call_sync(code.start, x0, x1)
        results.append(res)

        print(f"{i:08}/{num_tests:08}: train={train_brn:09x} test={test_brn:09x}:{test_brn:036b} misp={res}", flush=True)



# =============================================================================

tgt = TargetMachine()

#test_pht_alias()

test_pht_counters_1()


