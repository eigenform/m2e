
from .asm import *

class MyExperiment(object):
    def __init__(self, template: AssemblerTemplate, desc=""):
        self.template = template
        self.desc = desc

    def compile(self, pmesr1, 
                addr=0x09_0000_0000, offset=0x0_0000_0000, 
                early_clear_ghist=False, **kwargs):

        # Unfortunately, the optimal layout here is something like:
        # 0x08_fb00_0000 - early clear (0x00_0400_0000 bytes)
        # 0x08_ff00_0000 - nops        (0x00_00ff_ff80 bytes)
        # 0x08_ffff_ff80 - prologue    (0x00_0000_0080 bytes)
        # 0x09_0000_0000 - content
        if early_clear_ghist == True:
            clear_ghist = """
            .rept 128
                b #4
                //.p2align 19
                //b 7f
                //.p2align 19
                //7:
            .endr
            """
        else:
            clear_ghist = ""

        code = Assembler(
            self.template.render(pmesr1=pmesr1, early_clear_ghist=clear_ghist, 
                **kwargs), 
            addr + offset
        )
        return code


class Experiment(object):
    def __init__(self, template: AsmTemplate, 
                 base_addr=0x08_ffff_0000, desc=""):
        """ Create a new experiment.
        """
        self.base_addr = base_addr
        self.desc = desc
        self.template = template

    def compile(self, **kwargs) -> MyAsm:
        """ Compile this experiment with given parameters.
        """
        content = self.template.render(**kwargs)
        asm = MyAsm(content, self.base_addr)
        return asm

    def run_rand(self, code: MyAsm, num_samples=1, debug=False):
        """ Write and run this experiment with random input. 
        NOTE: This passes a random 1-bit number into x0 for each run.
        """
        iface.writemem(self.base_addr, code.data)
        p.dc_cvau(self.base_addr, len(code.data))
        p.ic_ivau(self.base_addr, len(code.data))
        samples = []
        for i in range(0, num_samples):
            if debug == True:
                if i % (num_samples // 8) == 0: 
                    print(f"[*] Running test {i}/{num_samples}")
            rand = random.getrandbits(1)
            res = p.smp_call_sync(TARGET_CPU, code._start, rand)
            samples.append(res)
        return samples

    def run_periodic(self, period, code: MyAsm, num_samples=1, debug=False,
        strategy='single', x1=None):
        """ Write and run this experiment with periodic input. 

        'strategy' controls how the counter affects the branch outcome:
            'single' - When the counter overflows, the branch outcome changes
                       until the next test run. (ie. for a period of 8, the
                       pattern is '000000010000000100000001'...)

            'flip'   - When the counter overflows, the branch outcome changes
                       until the next time the counter overflows. (ie. for a 
                       period of 8, '00000000111111110000000011111111...')
        """
        iface.writemem(self.base_addr, code.data)
        p.dc_cvau(self.base_addr, len(code.data))
        p.ic_ivau(self.base_addr, len(code.data))
        samples = []
        values = [] 

        ctr = 1
        value = 0

        for i in range(0, num_samples):
            if debug == True:
                if i % 32 == 0: print(f"[*] Running test {i}/{num_samples}")

            if x1 != None:
                match x1:
                    case "rand": x1_val = random.getrandbits(1) 
                    case True: x1_val = 1
                    case False: x1_val = 0
                    case _: x1_val = 0
                res = p.smp_call_sync(TARGET_CPU, code._start, value, x1_val)
            else:
                res = p.smp_call_sync(TARGET_CPU, code._start, value)

            samples.append(res)
            values.append(value)

            match strategy:
                case 'single': 
                    if ctr == period:
                        ctr = 0
                        value = 1
                    else: 
                        ctr += 1
                        value = 0
                case 'flip':
                    if ctr == period:
                        value = value ^ 1
                        ctr = 0
                    ctr += 1


        return (samples, values)


