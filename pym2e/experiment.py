
from .asm import *

class MyExperiment(object):
    def __init__(self, template: AssemblerTemplate, desc=""):
        self.template = template
        self.desc = desc

    def compile(self, pmesr1, 
                addr=0x09_0000_0000, offset=0x0_0000_0000, 
                early_clear_ghist=False, **kwargs):
        """ Compile an experiment given some parameters.
        addr: The base address for compiled code
        offset: Some offset from the base address
        """

        # Unfortunately, the optimal layout here is something like:
        # 0x08_fb00_0000 - early clear (0x00_0400_0000 bytes)
        # 0x08_ff00_0000 - nops        (0x00_00ff_ff80 bytes)
        # 0x08_ffff_ff80 - prologue    (0x00_0000_0080 bytes)
        # 0x09_0000_0000 - content
        if early_clear_ghist == True:
            clear_ghist = """
            .rept 256
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


class GhistTemplate(object):
    """ We may not want to use 'AssemblerTemplate' because we might need some 
    finer-grained control over when the measurement starts. 
    This just avoids starting the measurement in the prologue. 
    You're expected to use the macro 'start_pmc6 <scratch reg>'.
    """

    template_prologue_pmc6 = """
    _prologue_clear_pmcs:
        msr s3_1_c15_c0_0, xzr // PMCR0
        msr s3_1_c15_c1_0, xzr // PMCR1
        msr s3_1_c15_c5_0, xzr // PMESR0
        msr s3_1_c15_c6_0, xzr // PMESR1
        msr s3_2_c15_c6_0, xzr // PMC6_EL1
        isb
        mov x6, lr
        nop
    _write_pmcr1:
        movk x7, #0x0040, lsl 16 
        msr s3_1_c15_c1_0, x7
        isb
        nop
        nop
        nop
        nop
        nop
    _write_pmesr1:
        mov x7, #0x{pmesr1:04x}
        msr s3_1_c15_c6_0, x7
        isb
        nop
        nop
        nop
        nop
        nop

        nop
        nop
        nop
        nop
        nop
        nop
        nop
        nop
    """

    template_epilogue_pmc6 = """
    _clear_pmcr0:
        msr s3_1_c15_c0_0, xzr
        isb
    _read_pmc6:
        mrs x0, s3_2_c15_c6_0
        isb
    _epilogue_clear_pmcs:
        msr s3_1_c15_c0_0, xzr // PMCR0
        msr s3_1_c15_c1_0, xzr // PMCR1
        msr s3_1_c15_c5_0, xzr // PMESR0
        msr s3_1_c15_c6_0, xzr // PMESR1
        msr s3_2_c15_c6_0, xzr // PMC6_EL1
        isb
    _exit:
        ret
    """
    top_template = """
    .section .text.prologue
    .globl _start
    _start:
    {prologue}
    .section .text.content
    _content:
    {content}
    .section .text.epilogue
    {epilogue}
    """

    def __init__(self, user_content):
        self.template = self.top_template.format(
            prologue=self.template_prologue_pmc6,
            content=user_content,
            epilogue=self.template_epilogue_pmc6,
        )
    def render(self, **kwargs):
        return self.template.format(**kwargs)

class GhistExperiment(object):
    def __init__(self, template: GhistTemplate, desc=""):
        self.template = template
        self.desc = desc

    def compile(self, pmesr1, 
                addr=0x09_0000_0000, offset=0x0_0000_0000, **kwargs):
        code = Assembler(
            self.template.render(pmesr1=pmesr1, **kwargs), 
            addr + offset
        )
        return code


