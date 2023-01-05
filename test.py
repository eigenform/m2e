#!/usr/bin/env python3

import sys, pathlib
sys.path.append(str(pathlib.Path("./m1n1/proxyclient")))
from m1n1.setup import *
from m1n1 import asm

# m1n1 is running on the primary core (cpu0). 
# You need to initialize the others by calling smp_start_secondaries().

p.smp_start_secondaries()

# Just making sure I can dispatch tasks to individual cores. 
# MPIDR_EL1 uniquely identifies an ARM PE.
#
# AFAICT: MPIDR_EL1.Aff0 is the core ID and .Aff1/.Aff2 are the cluster.
# Cluster 0 is E-core ("Blizzard") and cluster 1 is P-core ("Avalanche").

TARGET_CPU = 4

code = u.malloc(0x1000)
c = asm.ARMAsm("""
    mrs x0, MPIDR_EL1
    ret
""", code)
iface.writemem(code, c.data)
p.dc_cvau(code, len(c.data))
p.ic_ivau(code, len(c.data))
ret = p.smp_call_sync(TARGET_CPU, code)

#assert ret == 0x80010100
print("{:08x}".format(ret))

