
use core::arch::asm;

#[inline(always)]
pub fn dc_civac(ptr: *const u8) {
    unsafe { 
        asm!("dc cvac, {}", in(reg) ptr);
    }
}

#[inline(always)]
pub fn cntpct_el0() -> usize {
    let val: usize;
    unsafe { 
        asm!("mrs {}, CNTPCT_EL0", out(reg) val);
    }
    val
}

#[inline(always)]
pub fn isb() {
    unsafe {
        asm!("isb");
    }
}
