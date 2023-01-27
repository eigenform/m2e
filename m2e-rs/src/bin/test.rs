#![no_std]
#![no_main]

use m2e::chase::*;
use m2e::common::*;
use m2e::mem::*;
use m2e::pmu::*;
use m2e::codegen::*;
use m2e::sr;
use m2e::armv8;
use core::assert;

// NOTE: I don't know how I'm going to do this yet
core::arch::global_asm!(core::include_str!("../wrapper.s"));
core::arch::global_asm!(core::include_str!("../trampoline.s"));
extern "C" {
    fn test_wrapper(pmcr0_bits: usize, scratch_addr: usize); 
    fn measured_trampoline(
        pmcr0_bits: usize, 
        func: usize, 
        arg0: usize, 
        arg1: usize
    );
}

#[derive(Clone, Copy)]
#[repr(C)]
pub struct Results {
    ctr: [usize; 8]
}
impl Results {
    pub fn new() -> Self { Self { ctr: [0; 8] } }
}

#[no_mangle]
pub extern "C" fn main(heap_base: usize) -> ! {
    ALLOCATOR.init(heap_base);
    assert!(heap_base == ALLOCATOR.get_base());
    clear_pmu_state();

    // Run the test 256 times, for each of the 256 events. 
    //let mut scratch_buf = Box::new([0x00u8; 0x1000]);
    //let mut results = Box::new([ [Results::new(); 0x100]; 0x100]);
    //for evt_idx in 0x01..=0xf0u8 {
    //    for test_idx in 0x00..=0xff {
    //        results[evt_idx as usize][test_idx] = run_gadget(evt_idx, 
    //            scratch_buf.as_ptr(),
    //            0 as *const u8,
    //        );
    //    }
    //}

    // Testing runtime codegen
    let mut emitter = CodeEmitter::new();
    for _ in 0..16 { 
        emitter.push(Armv8Instr::Nop); 
    }
    emitter.push(Armv8Instr::Ret { rn: Gpr::x30 });
    let func = emitter.emit().unwrap();
    let mut results = Box::new([ [Results::new(); 0x100]; 0x100]);
    for evt_idx in 0x01..=0xf0u8 {
        for test_idx in 0..256 {
            results[evt_idx as usize][test_idx] = run_emitted_code(
                evt_idx, func as usize, 0, 0
            );
        }
    }


    CONTEXT.get().set_payload(
        results.as_ptr() as *const u8, 
        core::mem::size_of::<[[Results; 0x100]; 0x100]>()
    );

    clear_pmu_state();
    exit(ResultCode::OK)
}


fn run_gadget(event: u8, scratch_addr1: *const u8, scratch_addr2: *const u8) 
    -> Results
{
    let mut result = Results::new();
    let pmu = PmuConfig {
        en: [ false, false, true, true, true, true, true, true, true, true ],
        event: [ None, None, 
            Some(event), Some(event), Some(event), Some(event),
            Some(event), Some(event), Some(event), Some(event),
        ],
    };

    unsafe { 
        sr::PMCR1_EL1::write(pmu.pmcr1_bits());
        sr::PMESR0_EL1::write(pmu.pmesr0_bits());
        sr::PMESR1_EL1::write(pmu.pmesr1_bits());
        armv8::isb();

        test_wrapper(pmu.pmcr0_bits(), scratch_addr1 as usize);

        result.ctr[0] = sr::PMC2_EL1::read();
        result.ctr[1] = sr::PMC3_EL1::read();
        result.ctr[2] = sr::PMC4_EL1::read();
        result.ctr[3] = sr::PMC5_EL1::read();
        result.ctr[4] = sr::PMC6_EL1::read();
        result.ctr[5] = sr::PMC7_EL1::read();
        result.ctr[6] = sr::PMC8_EL1::read();
        result.ctr[7] = sr::PMC9_EL1::read();

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

    result
}

fn run_emitted_code(event: u8, func: usize, arg0: usize, arg1: usize) 
    -> Results
{

    let mut result = Results::new();
    let pmu = PmuConfig {
        en: [ false, false, true, true, true, true, true, true, true, true ],
        event: [ None, None, 
            Some(event), Some(event), Some(event), Some(event),
            Some(event), Some(event), Some(event), Some(event),
        ],
    };

    unsafe { 
        sr::PMCR1_EL1::write(pmu.pmcr1_bits());
        sr::PMESR0_EL1::write(pmu.pmesr0_bits());
        sr::PMESR1_EL1::write(pmu.pmesr1_bits());
        armv8::isb();

        measured_trampoline(pmu.pmcr0_bits(), func, 0, 0);

        result.ctr[0] = sr::PMC2_EL1::read();
        result.ctr[1] = sr::PMC3_EL1::read();
        result.ctr[2] = sr::PMC4_EL1::read();
        result.ctr[3] = sr::PMC5_EL1::read();
        result.ctr[4] = sr::PMC6_EL1::read();
        result.ctr[5] = sr::PMC7_EL1::read();
        result.ctr[6] = sr::PMC8_EL1::read();
        result.ctr[7] = sr::PMC9_EL1::read();

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

    result


}


