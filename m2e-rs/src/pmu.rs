
use core::arch::asm;

use crate::sr;
use crate::armv8;

/// Clear all PMU registers.
#[inline(never)]
pub fn clear_pmu_state() {
    unsafe { 
        sr::PMCR0_EL1::clear();
        sr::PMCR1_EL1::clear();
        sr::PMESR0_EL1::clear();
        sr::PMESR1_EL1::clear();
        sr::PMC0_EL1::clear();
        sr::PMC1_EL1::clear();
        sr::PMC2_EL1::clear();
        sr::PMC3_EL1::clear();
        sr::PMC4_EL1::clear();
        sr::PMC5_EL1::clear();
        sr::PMC6_EL1::clear();
        sr::PMC7_EL1::clear();
        sr::PMC8_EL1::clear();
        sr::PMC9_EL1::clear();
        armv8::isb();
    }
}

// NOTE: Remember that you *need* ISB to post system register writes. 
pub fn pmc_test() {
    let val = unsafe { 
        sr::PMCR1_EL1::write(0x0000_0000_0001_0000);
        sr::PMCR0_EL1::write(0x0000_0000_0000_0001);
        armv8::isb();

        asm!("nop; nop; nop; nop; nop; nop; nop; nop");
        asm!("nop; nop; nop; nop; nop; nop; nop; nop");
        asm!("nop; nop; nop; nop; nop; nop; nop; nop");
        asm!("nop; nop; nop; nop; nop; nop; nop; nop");

        sr::PMCR0_EL1::clear();
        armv8::isb();
        sr::PMCR1_EL1::clear();
        armv8::isb();
        let result = sr::PMC0_EL1::read();
        sr::PMC0_EL1::clear();
        armv8::isb();
        result
    };
    //CONTEXT.write_value(val);
}



