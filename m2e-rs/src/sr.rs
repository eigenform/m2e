
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

// Performance Monitoring Control Register 0
impl_register!(PMCR0_EL1,  "s3_1_c15_c0_0");
// Performance Monitoring Control Register 1
impl_register!(PMCR1_EL1,  "s3_1_c15_c1_0");

// Performance Monitoring Event Select Register 0 (PMC{2..5})
impl_register!(PMESR0_EL1, "s3_1_c15_c5_0");
// Performance Monitoring Event Select Register 1 (PMC{6..9})
impl_register!(PMESR1_EL1, "s3_1_c15_c6_0");

// Performance Monitoring Counters (Fixed)
impl_register!(PMC0_EL1,   "s3_2_c15_c0_0");
impl_register!(PMC1_EL1,   "s3_2_c15_c1_0");

// Performance Monitoring Counters (Programmable)
impl_register!(PMC2_EL1,   "s3_2_c15_c2_0");
impl_register!(PMC3_EL1,   "s3_2_c15_c3_0");
impl_register!(PMC4_EL1,   "s3_2_c15_c4_0");
impl_register!(PMC5_EL1,   "s3_2_c15_c5_0");
impl_register!(PMC6_EL1,   "s3_2_c15_c6_0");
impl_register!(PMC7_EL1,   "s3_2_c15_c7_0");
impl_register!(PMC8_EL1,   "s3_2_c15_c9_0");
impl_register!(PMC9_EL1,   "s3_2_c15_c10_0");


