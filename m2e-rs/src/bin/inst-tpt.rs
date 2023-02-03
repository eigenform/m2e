//! Using the cycle counter (PMC0) to determine what instructions can be 
//! handled in a single cycle. 

#![no_std]
#![no_main]

use m2e::common::*;
use m2e::mem::*;

use m2e::chase::*;
use m2e::pmu::*;
use m2e::sr;
use m2e::armv8;
use core::assert;


#[no_mangle]
pub fn main(heap_base: usize) -> ! {
    ALLOCATOR.init(heap_base);
    clear_pmu_state();

    //let mut rng  = Xorshift64::new();
    //let mut maze = PointerMaze::<0x0001_0000>::new();
    //maze.shuffle(&mut rng, 512);
    //let ptr1 = maze.head_ptr() as usize;
    //let ptr2 = maze.mid_ptr() as usize;

    let tmp1 = Box::new([0u8; 0x100]);
    let tmp2 = Box::new([0u8; 0x100]);
    let ptr1 = tmp1.as_ptr() as usize;
    let ptr2 = tmp2.as_ptr() as usize;

    let pmu = PmuConfig {
        en: [ true, false, true, true, true, true, true, true, true, true ],
        event: [ None, None, None, None, None, None, None, None, None, None ],
    };

    const TEST_ITERS: usize = 0x100;
    let mut results = Box::new([0usize; TEST_ITERS]);

    unsafe { 
        sr::PMCR1_EL1::write(pmu.pmcr1_bits());
        sr::PMESR0_EL1::write(pmu.pmesr0_bits());
        sr::PMESR1_EL1::write(pmu.pmesr1_bits());

        for idx in 0..TEST_ITERS {

            sr::PMCR0_EL1::write(pmu.pmcr0_bits());
            armv8::isb();
            let cycles = tpt_test(ptr1, ptr2);

            sr::PMCR0_EL1::clear();
            sr::PMC0_EL1::clear();
            armv8::isb();

            results[idx] = cycles;

        }

    }

    CONTEXT.get().set_payload(
        results.as_ptr() as *const u8, 
        core::mem::size_of_val(&*results)
    );
    exit(ResultCode::OK)
}


core::arch::global_asm!("
.section .text

// tpt_test(arg0: usize, arg1: usize) -> usize
.global tpt_test
tpt_test:
	adr x8, _tpt_saved_state
	mov x9, sp
	stp x18, x19, [x8, #0x00]
	stp x20, x21, [x8, #0x10]
	stp x22, x23, [x8, #0x20]
	stp x24, x25, [x8, #0x30]
	stp x26, x27, [x8, #0x40]
	stp x28, x29, [x8, #0x50]
	stp x30, x9,  [x8, #0x60]
	dsb sy
	isb

	mov x28, x0 // arg0
	mov x29, x1 // arg1

	mov x0,  #0
	mov x1,  #0
	mov sp,  x0
	msr NZCV,x0
	mov x2,  #0
	mov x3,  #0
	mov x4,  #0
	mov x5,  #0
	mov x6,  #0
	mov x7,  #0
	mov x8,  #0
	mov x9,  #0
	mov x10, #0
	mov x11, #0
	mov x12, #0
	mov x13, #0
	mov x14, #0
	mov x15, #0
	mov x16, #0
	mov x17, #0
	mov x18, #0
	mov x19, #0
	mov x20, #0
	mov x21, #0
	mov x22, #0
	mov x23, #0
	mov x24, #0
	mov x25, #0
	mov x26, #0
	mov x27, #0

	.rept 2048
	nop
	.endr
.balign 64
	.rept 8
	dsb sy
	isb
	.endr

.balign 64
_tpt_start_measurement:
    nop
    nop
    nop
    nop
    nop
    nop
    nop
    nop

    nop
    nop
    nop
    mov x20, #20
    isb
	mrs x26, s3_2_c15_c0_0
    dsb sy
    isb

// This first 'DSB SY; ISB' should always incur a fixed amount of latency. 
// However, the one at the end indicates that instructions in '_tpt_test_body' 
// should *complete* before taking the second measurement.
//
// For a window of 8 NOPs, the baseline 'minimum' latency is 83 cycles. 
// We expect that changing only the first instruction will change this, since 
// the trailing barriers wait for completion. 
//
// Since we always stall for completion, you want to make sure that all of 
// the meausred instructions do not have data dependences (otherwise we'd be
// observing the latency from something other than 'contention for execution
// resources'. 
//
// It seems like this matches Dougall's notes on the execution units available
// on the Firestorm cores: 
//
//  - Six integer operations 
//      - One DIV, two MUL, 
//  - Four floating point operations
//  - Two FP-to-INT moves
//  - Three INT-to-FP moves
//  - Three load operations, two store operations 

_tpt_test_body:
    // NOPs are effectively free!
    //nop
    //nop
    //nop
    //nop
    //nop
    //nop
    //nop
    //nop

    // Six integer units?
    //add x1, x20, #1 // 83 cycles ...
    //add x2, x20, #1 // 83 cycles ...
    //add x3, x20, #1 // 83 cycles ...
    //add x4, x20, #1 // 83 cycles ...
    //add x5, x20, #1 // 83 cycles ...
    //add x6, x20, #1 // 83 cycles ...
    //add x7, x20, #1 // 84 cycles!
    //nop

    // One DIV instruction per cycle
    //udiv x0, x1, x2 // 87 cycles ...
    //udiv x3, x4, x5 // 89 cycles!
    //nop
    //nop
    //nop
    //nop
    //nop
    //nop

    // Two MUL instructions per cycle
    //mul x0, x1, x2 // 83 cycles ...
    //mul x3, x4, x5 // 83 cycles ...
    //mul x6, x7, x8 // 84 cycles!
    //nop
    //nop
    //nop
    //nop
    //nop

    // Four floating-point units?
    //fneg d1, d2  // 86 cycles ...
    //fneg d3, d4  // 86 cycles ...
    //fneg d5, d6  // 86 cycles ...
    //fneg d7, d8  // 86 cycles ...
    //fneg d9, d10 // 87 cycles!
    //nop
    //nop
    //nop

    // Two FP-to-integer moves per cycle?
    fmov x0, d0 // 86 cycles ...
    fmov x1, d1 // 86 cycles ...
    fmov x2, d2 // 87 cycles!
    nop
    nop
    nop
    nop
    nop

    // Three integer-to-FP moves per cycle?
    //fmov d0, x0 // 88 cycles ...
    //fmov d1, x1 // 88 cycles ...
    //fmov d2, x2 // 88 cycles ...
    //fmov d3, x3 // 89 cycles!
    //nop
    //nop
    //nop
    //nop

    // Three load pipes?
    //ldr x0, [x28] // 88 cycles ...
    //ldr x1, [x28] // 88 cycles ...
    //ldr x2, [x28] // 88 cycles ...
    //ldr x3, [x28] // 89 cycles ...
    //nop
    //nop
    //nop
    //nop

    // Two store pipes?
    //str x0, [x28] // 88 cycles ...
    //str x1, [x28] // 88 cycles ...
    //str x2, [x28] // 89 cycles!
    //nop
    //nop
    //nop
    //nop
    //nop

    // 2 loads and 2 stores; the last load pipe must be shared with stores!
    //str x0, [x28, #0x20] // 88 cycles ...
    //ldr x0, [x28]        // 88 cycles ...
    //str x1, [x28, #0x40] // 88 cycles ...
    //ldr x1, [x28]        // 88 cycles ...
    //ldr x3, [x28]        // 89 cycles!
    //nop
    //nop
    //nop

    // 3 loads and 1 store; the last store pipe must be shared with loads!
    //str x0, [x28, #0x20] // 88 cycles ...
    //ldr x0, [x28]        // 88 cycles ...
    //ldr x1, [x28]        // 88 cycles ...
    //ldr x2, [x28]        // 88 cycles ...
    //str x3, [x28, #0x40] // 89 cycles!
    //nop
    //nop
    //nop

    // Register-to-register moves are effectively free?
    //mov x1, x0
    //mov x2, x0
    //mov x3, x0
    //mov x4, x0
    //mov x5, x0
    //mov x6, x0
    //mov x7, x0
    //mov x8, x0

    // Immediate-to-register moves are effectively free?
    //mov x1, #111
    //mov x2, #222
    //mov x3, #333
    //mov x4, #444
    //mov x5, #555
    //mov x6, #666
    //mov x7, #777
    //mov x8, #888

    // It seems like 'xzr' is exempt from renaming?
    //mov x1, xzr // 84 cycles ...
    //mov x2, xzr // 84 cycles ...
    //mov x3, xzr // 84 cycles ...
    //mov x4, xzr // 84 cycles ...
    //mov x5, xzr // 84 cycles ...
    //mov x6, xzr // 84 cycles ...
    //mov x7, xzr // 85 cycles!
    //nop

    // ADR on only 4/6 integer datapaths?
    //adr x0, #0x7ffff // 83 cycles ...
    //adr x0, #0x7ffff // 83 cycles ...
    //adr x0, #0x7ffff // 83 cycles ...
    //adr x0, #0x7ffff // 83 cycles ...
    //adr x0, #0x7ffff // 84 cycles!
    //nop
    //nop
    //nop

    // NOTE: The maximum latency varies when there are more than four 
    // unconditional branches in the decode window. I wonder if this is 
    // related to the observation about limits on 'ADR'. 
   
    // Two conditional branches per cycle? 
    //b.eq #0x4 // 83 cycles ...
    //b.eq #0x4 // 83 cycles ...
    //b.eq #0x4 // 84 cycles!
    //b.eq #0x4 // 84 cycles!
    //b.eq #0x4 // 85 cycles!
    //b.eq #0x4 // 85 cycles!
    //b.eq #0x4 // 86 cycles!
    //b.eq #0x4 // 86 cycles!

    // Two unconditional branches per cycle?
    //b #4 // 84 cycles ...
    //b #4 // 84 cycles ...
    //b #4 // 85 cycles!
    //b #4 // 86 cycles!
    //b #4 // 87 cycles! (maximum latency starts to vary...)
    //nop
    //nop
    //nop

    // One branch-and-link per cycle?
    //bl #4 // 83 cycles ...
    //bl #4 // 84 cycles!
    //bl #4 // 85 cycles!
    //bl #4 // 86 cycles!
    //bl #4 // 87 cycles! (maximum latency starts to vary ...)
    //nop
    //nop
    //nop

    // One system register read per cycle?
    //mrs x0, s3_2_c15_c2_0 // 84 cycles ...
    //mrs x1, s3_2_c15_c2_0 // 85 cycles!
    //nop
    //nop
    //nop
    //nop
    //nop
    //nop

    // One system register write per cycle?
    //msr s3_2_c15_c2_0, xzr // 88 cycles ...
    //msr s3_2_c15_c2_0, xzr // 89 cycles!
    //nop
    //nop
    //nop
    //nop
    //nop
    //nop

_tpt_end_measurement:
    dsb sy
    isb
	mrs x27, s3_2_c15_c0_0
    isb
	sub x0, x27, x26
    nop
    nop
    nop

    nop
    nop
    nop
	nop
	nop
	nop
	nop


_tpt_test_exit:
	adr x8, _tpt_saved_state
	ldp x18, x19, [x8, #0x00]
	ldp x20, x21, [x8, #0x10]
	ldp x22, x23, [x8, #0x20]
	ldp x24, x25, [x8, #0x30]
	ldp x26, x27, [x8, #0x40]
	ldp x28, x29, [x8, #0x50]
	ldp x30, x9,  [x8, #0x60]
	dsb sy
	mov sp, x9
    ret

_tpt_saved_state:
	.quad 0
	.quad 0
	.quad 0
	.quad 0
	.quad 0
	.quad 0
	.quad 0
	.quad 0
	.quad 0
	.quad 0
	.quad 0
	.quad 0
	.quad 0
	.quad 0


");

extern "C" {
    fn tpt_test(ptr1: usize, ptr2: usize) -> usize; 
}


