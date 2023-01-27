
use crate::mem::*;
use core::alloc::{ GlobalAlloc, Layout };

#[derive(Clone, Copy)]
pub enum Gpr {
    x0,  x1,  x2,  x3,  x4,  x5,  x6,  x7, 
    x8,  x9,  x10, x11, x12, x13, x14, x15,
    x16, x17, x18, x19, x20, x21, x22, x23, 
    x24, x25, x26, x27, x28, x29, x30, xzr
}
impl Gpr {
    pub fn idx(&self) -> u32 {
        match self { 
            Self::x0  => 0,
            Self::x1  => 1,
            Self::x2  => 2,
            Self::x3  => 3,
            Self::x4  => 4,
            Self::x5  => 5,
            Self::x6  => 6,
            Self::x7  => 7,
            Self::x8  => 8,
            Self::x9  => 9,
            Self::x10 => 10,
            Self::x11 => 11,
            Self::x12 => 12,
            Self::x13 => 13,
            Self::x14 => 14,
            Self::x15 => 15,
            Self::x16 => 16,
            Self::x17 => 17,
            Self::x18 => 18,
            Self::x19 => 19,
            Self::x20 => 20,
            Self::x21 => 21,
            Self::x22 => 22,
            Self::x23 => 23,
            Self::x24 => 24,
            Self::x25 => 25,
            Self::x26 => 26,
            Self::x27 => 27,
            Self::x28 => 28,
            Self::x29 => 29,
            Self::x30 => 30,
            Self::xzr => 31,
        }
    }
}

pub enum Armv8Instr {
    Nop,
    DsbSy,
    Ret { rn: Gpr },
}
impl Armv8Instr {
    fn emit_ret(rn: Gpr) -> u32 {
        let val = 0b1101011_0_0_10_11111_0000_0_0_00000_00000;
        val | (rn.idx() << 5)
    }
    pub fn emit(&self) -> u32 {
        match self { 
            Self::Nop        => 0xd503201f,
            Self::DsbSy      => 0xd5033f9f,
            Self::Ret { rn } => Self::emit_ret(*rn),
        }
    }
}

pub struct CodeEmitter {
    data: Vec<Armv8Instr>,
    code: *mut u8,
    size: usize,
}
impl CodeEmitter {
    pub fn new() -> Self {
        Self { 
            data: Vec::new(),
            code: 0 as *mut u8,
            size: 0,
        }
    }
    pub fn push(&mut self, inst: Armv8Instr) {
        self.data.push(inst);
    }
    pub fn emit(&mut self) -> Option<*const u8> {
        if self.data.is_empty() {
            return None;
        }
        let num_instr = self.data.len();
        let num_bytes = num_instr * 4;

        unsafe { 
            let code: *mut u8 = ALLOCATOR.alloc(
                if let Ok(res) = Layout::from_size_align(num_bytes, 4096) {
                    res
                } else {
                    return None;
                }
            );
            let buf: &mut [u32] = core::slice::from_raw_parts_mut(
                code as *mut u32, num_instr
            );

            for idx in 0..self.data.len() {
                buf[idx] = self.data[idx].emit();
            }
            self.code = code;
            self.size = num_bytes;
            Some(code)
        }

    }
    pub fn as_ptr(&self) -> Option<*const u8> {
        if self.code as usize != 0 {
            Some(self.code as *const u8)
        } else {
            None
        }
    }
}

