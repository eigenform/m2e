
use core::arch::asm;

#[inline(always)]
pub fn dc_civac(ptr: *const u8) {
    unsafe { 
        asm!("dc cvac, {}", in(reg) ptr);
    }
}

#[inline(always)]
pub fn ic_ialluis() {
    unsafe { 
        asm!("ic ialluis; dsb sy");
    }
}

#[inline(always)]
pub fn tlbi_alle2is() {
    unsafe { 
        asm!("tlbi alle2is; dsb sy");
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
