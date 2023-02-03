
use core::arch::asm;

macro_rules! impl_register { 
    ($name_ident:ident, $reg_name:literal) => {
        pub struct $name_ident;
        impl $name_ident {
            #[inline(always)]
            pub unsafe fn clear() { 
                asm!(concat!("msr ", $reg_name, ", xzr"), 
                     options(nomem, nostack)); 
            }

            #[inline(always)]
            pub unsafe fn write(val: usize) { 
                asm!(concat!("msr ", $reg_name, ", {reg:x}"), 
                     reg = in(reg) val, options(nomem, nostack)
                );
            }

            #[inline(always)]
            pub unsafe fn read() -> usize { 
                let val: usize;
                asm!(concat!("mrs {reg:x}, ", $reg_name), 
                     reg = out(reg) val, options(nomem, nostack)
                );
                val
            }
        }
    }
}

impl_register!(SCTLR_EL2,  "SCTLR_EL2");

// Performance Monitoring Control Register 0
impl_register!(PMCR0_EL1,  "s3_1_c15_c0_0");
// Performance Monitoring Control Register 1
impl_register!(PMCR1_EL1,  "s3_1_c15_c1_0");
impl_register!(PMCR2_EL1,  "s3_1_c15_c2_0");
impl_register!(PMCR3_EL1,  "s3_1_c15_c3_0");
impl_register!(PMCR4_EL1,  "s3_1_c15_c4_0");
// Performance Monitoring Event Select Register 0 (PMC{2..5})
impl_register!(PMESR0_EL1, "s3_1_c15_c5_0");
// Performance Monitoring Event Select Register 1 (PMC{6..9})
impl_register!(PMESR1_EL1, "s3_1_c15_c6_0");

// No clue what these are
impl_register!(OPMAT0,     "s3_1_c15_c7_0");
impl_register!(OPMAT1,     "s3_1_c15_c8_0");
impl_register!(OPMSK0,     "s3_1_c15_c9_0");
impl_register!(OPMSK1,     "s3_1_c15_c10_0");
//                          s3_1_c15_c11_0 (returns 0xfffff)
//                          s3_1_c15_c12_0 (returns 0x0)
//                          s3_1_c15_c13_0 (returns 0x0)
//                          s3_1_c15_c14_0 (returns 0x0)
//                          s3_1_c15_c15_0 (returns 0x0)

// Performance Monitoring Counters (Fixed)
impl_register!(PMC0_EL1,   "s3_2_c15_c0_0"); // Cycles
impl_register!(PMC1_EL1,   "s3_2_c15_c1_0"); // Retired instructions

// Performance Monitoring Counters (Programmable)
impl_register!(PMC2_EL1,   "s3_2_c15_c2_0");
impl_register!(PMC3_EL1,   "s3_2_c15_c3_0");
impl_register!(PMC4_EL1,   "s3_2_c15_c4_0");
impl_register!(PMC5_EL1,   "s3_2_c15_c5_0");
impl_register!(PMC6_EL1,   "s3_2_c15_c6_0");
impl_register!(PMC7_EL1,   "s3_2_c15_c7_0");
//                          s3_2_c15_c8_0 (throws an exception?)
impl_register!(PMC8_EL1,   "s3_2_c15_c9_0");
impl_register!(PMC9_EL1,   "s3_2_c15_c10_0");
//                          s3_2_c15_c11_0 (throws an exception?)

// No clue what these are
impl_register!(PMTRHLD6,   "s3_2_c15_c12_0");
impl_register!(PMTRHLD4,   "s3_2_c15_c13_0");
impl_register!(PMTRHLD2,   "s3_2_c15_c14_0");
impl_register!(PMMAP,      "s3_2_c15_c15_0");


