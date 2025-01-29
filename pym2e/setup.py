
import os, struct, sys, time, pathlib
from construct import *

M1N1_PATH = str(
    pathlib.Path(__file__).parents[1].joinpath("m1n1/proxyclient")
)
sys.path.append(M1N1_PATH)

from m1n1.hv import HV
from m1n1.proxy import *
from m1n1.proxyutils import *
from m1n1.sysreg import *
from m1n1.tgtypes import *
from m1n1.utils import *
from m1n1.hw.pmu import PMU
from m1n1.asm import ARMAsm

class TargetMachine(object):
    """ Wrapper over a connection to the m1n1 proxy. 
    You only want to instantiate one of these objects at a time. 
    """
    TARGET_CPU = 4
    #CODE_SIZE  = 512 * (1024 * 1024)
    #HEAP_SIZE  = 16 * (1024 * 1024)
    #CODE_ALIGN = (1024 * 1024)
    #HEAP_ALIGN = (1024 * 1024)

    def __init__(self):
        self.iface = UartInterface()
        self.p     = M1N1Proxy(self.iface, debug=False)
        bootstrap_port(self.iface, self.p)
        self.u     = ProxyUtils(self.p, heap_size=(128 * 1024 * 1024))
        #self.hv    = HV(self.iface, self.p, self.u)
        PMU(self.u).reset_panic_counter()
        print(f"[*] m1n1 base:      0x{self.u.base:016x}")
        print(f"[*] m1n1 heap base: 0x{self.u.heap_base:016x}")
        print(f"[*] m1n1 heap size: 0x{self.u.heap_size:016x}")
        print(f"[*] m1n1 heap top:  0x{self.u.heap_top:016x}")
        self.u.heap.check()
        PMU(self.u).reset_panic_counter()

        # Only need to do this once after m1n1 is up
        val = self.p.read64(0x08_1000_0000)
        if val != 0xdeadbeef:
            self.p.smp_start_secondaries()
            self.p.mmu_init_secondary(self.TARGET_CPU)
            self.p.write64(0x08_1000_0000, 0xdeadbeef)
            print("[*] Started secondary cores")

    def write_payload(self, addr, data, debug=False):
        data_len = len(data)
        if debug == True:
            print(f"[*] Writing {data_len:08x} bytes to {addr:016x}")
        self.iface.writemem(addr, data)
        self.p.dc_cvau(addr, data_len)
        self.p.ic_ivau(addr, data_len)

    def smp_call_sync(self, addr, *args):
        res = self.p.smp_call_sync(self.TARGET_CPU, addr, *args)
        return res

    def msr(self, x, v):
        def cpu_call(x, *args):
            return self.smp_call_sync(x, *args)
        self.u.msr(x, v, call=lambda x, *args: cpu_call(x, *args))

    def mrs(self, x):
        def cpu_call(x, *args):
            return self.smp_call_sync(x, *args)
        return self.u.mrs(x, call=lambda x, *args: cpu_call(x, *args))


