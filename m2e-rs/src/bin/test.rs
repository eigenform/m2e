#![no_std]
#![no_main]

use m2e::chase::*;
use m2e::common::*;
use m2e::mem::*;
use m2e::pmu::*;
use m2e::sr;
use m2e::armv8;
use core::assert;

// NOTE: I don't know how I'm going to do this yet
core::arch::global_asm!(core::include_str!("../wrapper.s"));
extern "C" {
    fn test_wrapper(pmcr0_bits: usize); 
}

//const MAZE_LENGTH: usize = 0x0100_0000;
//const MAZE_STRIDE: usize = 2;

#[no_mangle]
pub extern "C" fn main(heap_base: usize) -> ! {
    ALLOCATOR.init(heap_base);
    assert!(heap_base == ALLOCATOR.get_base());
    clear_pmu_state();

    //let mut rng  = Xorshift64::new();
    //let mut maze = PointerMaze::<MAZE_LENGTH>::new();
    //maze.shuffle(&mut rng, MAZE_STRIDE);
    //maze.flush();

    let result = Box::new(run_gadget(0x02));
    CONTEXT.get().set_payload(
        result.as_ptr() as *const u8, 
        core::mem::size_of::<[usize; 8]>()
    );

    clear_pmu_state();
    exit(ResultCode::OK)
}

fn run_gadget(event: u8) -> [usize; 8] {
    let mut result = [0; 8];
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

        test_wrapper(pmu.pmcr0_bits());

        result[0] = sr::PMC2_EL1::read();
        result[1] = sr::PMC3_EL1::read();
        result[2] = sr::PMC4_EL1::read();
        result[3] = sr::PMC5_EL1::read();
        result[4] = sr::PMC6_EL1::read();
        result[5] = sr::PMC7_EL1::read();
        result[6] = sr::PMC8_EL1::read();
        result[7] = sr::PMC9_EL1::read();
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


