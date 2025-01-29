
from .setup import *

from io import BytesIO
from elftools.elf.elffile import ELFFile
from elftools.elf.relocation import RelocationSection
from elftools.elf.enums import ENUM_RELOC_TYPE_AARCH64
from elftools.elf.sections import SymbolTableSection


import m1n1.asm

class Symbol(object):
    def __init__(self, name, addr):
        self.name = name
        self.addr = addr

class Assembler(m1n1.asm.ARMAsm):
    PREF = "aarch64-linux-gnu-"
    CC = PREF + "gcc"
    LD = PREF + "ld"
    OBJCOPY = PREF + "objcopy"
    OBJDUMP = PREF + "objdump"
    NM = PREF + "nm"

    LINKERSCRIPT = """
SECTIONS
{{
    .text.prologue :
    {{
    }}
    .text.content :
    {{
    }}
    .text.epilogue :
    {{
    }}
}}
"""
    HEADER = """

.macro labeled_pad_branch tgt_expr
_pad_branch_\\@:
    b \\tgt_expr
.endm

.macro labeled_pad_branch_align aalign=2, talign=2
.p2align \\aalign
_pad_branch_addr_\\@:
    b 0f
.p2align \\talign
_pad_branch_tgt_\\@:
0:
.endm

.macro labeled_prepad_branch
_prepad_branch_\\@:
    b #4
.endm

.macro set_bit x:req, more:vararg
	.rept (1 << (\\x - 2))
		nop
	.endr
	.ifnb \\more
	set_bit \\more
	.endif
.endm


.macro mix_history reg_rand, reg_scratch, num
    .rept \\num
        and \\reg_scratch, \\reg_rand #1
        ror \\reg_rand, \\reg_rand, #1
        cbnz \\reg_scratch, #4
        isb
    .endr
.endm

.macro start_pmc6 reg_scratch
    mov \\reg_scratch, #0x40
    msr s3_1_c15_c0_0, \\reg_scratch
    isb
.endm

.macro read_pmc6 reg_scratch
    mrs \\reg_scratch, s3_2_c15_c6_0
    isb
.endm

"""
    FOOTER = """
"""
    def compile(self, source):
        self.sfile = self._tmp + "b.S"
        with open(self.sfile, "w") as fd:
            fd.write(self.HEADER + "\n")
            fd.write(source + "\n")
            fd.write(self.FOOTER + "\n")

        self.ldfile = self._tmp + "linkerscript.ld"
        with open(self.ldfile, "w") as fd:
            fd.write(self.LINKERSCRIPT.format(content_addr=self.addr) + "\n")

        self.ofile = self._tmp + "b.o"
        self.elffile = self._tmp + "b.elf"
        self.elffile2 = self._tmp + "b.elf.2"
        self.bfile = self._tmp + "b.b"
        self.nfile = self._tmp + "b.n"


        self._call(self.CC, f"{self.CFLAGS} -pie -c -o {self.ofile} {self.sfile}")
        #with open(self.ofile, "rb") as f:
        #    d = f.read()
        #    with open("/tmp/wow.o", "wb") as g:
        #        g.write(d)

        self.prologue_sz = 0
        self.content_sz  = 0
        self.epilogue_sz = 0
        with open(self.ofile, "rb") as fd:
            e   = ELFFile(BytesIO(fd.read()))
            prologue = e.get_section_by_name(".text.prologue")
            content  = e.get_section_by_name(".text.content")
            epilogue = e.get_section_by_name(".text.epilogue")
            self.prologue_sz = prologue.data_size
            self.content_sz  = content.data_size
            self.epilogue_sz = epilogue.data_size

        self.content_addr  = self.addr
        self.prologue_addr = self.content_addr - self.prologue_sz
        self.epilogue_addr = self.content_addr + self.content_sz


        #ld_args  = f"{self.LDFLAGS} --nmagic -M "
        ld_args  = f"{self.LDFLAGS} --nmagic "
        ld_args += f"--section-start .text.prologue={self.prologue_addr:#x} "
        ld_args += f"--section-start .text.content={self.content_addr:#x} "
        ld_args += f"--section-start .text.epilogue={self.epilogue_addr:#x} "
        ld_args += f"-T {self.ldfile} "
        ld_args += f"-o {self.elffile} {self.ofile}"
        self._call(self.LD, ld_args)

        oc_args  = "-j .text.prologue "
        oc_args += "-j .text.content "
        oc_args += "-j .text.epilogue "
        oc_args += f"-O binary {self.elffile} {self.bfile}"
        self._call(self.OBJCOPY, oc_args)

        self._call(self.NM, f"{self.elffile} > {self.nfile}")

        with open(self.bfile, "rb") as fd:
            self.data = fd.read()

        self.symbols = []
        with open(self.nfile) as fd:
            for line in fd:
                line = line.replace("\n", "")
                addr, type, name = line.split()
                addr = int(addr, 16)
                self.symbols.append(Symbol(name, addr))
                setattr(self, name, addr)
        self.start = self._start
        self.len = len(self.data)
        self.end = self.start + self.len

    def dump_elf(self, path):
        with open(self.elffile, "rb") as f:
            data = f.read()
        with open(path, "wb") as g:
            g.write(data)

    def dump_bin(self, path):
        with open(path, "wb") as g:
            g.write(self.data)


class AssemblerTemplate(object):
    template_prologue_pmc6 = """
    _early_clear_ghist:
        {early_clear_ghist}
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
    _write_pmcr0:
        nop
        nop
        nop
        nop
        nop
        mov x7, #0x40
        msr s3_1_c15_c0_0, x7
        isb
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






