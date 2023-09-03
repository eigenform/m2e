
from io import BytesIO
from elftools.elf.elffile import ELFFile
from elftools.elf.relocation import RelocationSection
from elftools.elf.enums import ENUM_RELOC_TYPE_AARCH64
from elftools.elf.sections import SymbolTableSection

# See 'm2e-rs/src/common.rs' for the definition of this struct.
# We're relying on this to shuffle data back to the host machine. 
ResultContext = Struct(
    "result"  / Hex(Int64ul),
    "payload" / Hex(Int64ul),
    "len"     / Hex(Int64ul),
)


class TargetELF(object):
    """ Some ELF that we're going to load and execute """
    def __init__(self, path: str):
        self.path = path
        with open(path, "rb") as f:
            self.elf   = ELFFile(BytesIO(f.read()))

    def resolve_symbol(self, name: str) -> int | None:
        """ Resolve the virtual address of a symbol in this image """
        symtab = self.elf.get_section_by_name(".symtab")
        if not isinstance(symtab, SymbolTableSection):
            return None
        for s in symtab.iter_symbols():
            if s.name == name:
                return s['st_value']
        return None

    def load(self, base: int) -> int:
        self.entry = base + self.elf.header.e_entry
        # Load all of the segments
        for seg in self.elf.iter_segments():
            if seg.header['p_type'] == 'PT_LOAD':
                data  = seg.data()
                dlen  = len(data)
                dlen_kb = dlen // 1024
                addr  = base + seg.header['p_paddr']
                print(f"[*] Writing segment to {addr:016x} ({dlen:016x}) ({dlen_kb}kB)")
                iface.writemem(addr, data)
                p.dc_cvau(addr, dlen)
                p.ic_ivau(addr, dlen)

        # Handle relocations (did I do this right?? no clue!)
        rela_dyn = self.elf.get_section_by_name(".rela.dyn")
        for reloc in rela_dyn.iter_relocations():
            r_info = reloc['r_info']
            assert r_info == ENUM_RELOC_TYPE_AARCH64['R_AARCH64_RELATIVE']
            assert reloc.is_RELA()
            r_offset = reloc['r_offset']
            r_addend = reloc['r_addend']
            patch_addr = base + r_offset
            sym_addr   = base + r_addend 
            print(f"[*] RELA @ {patch_addr:016x} => {sym_addr:016x}")
            p.write64(patch_addr, sym_addr)
        return self.entry


