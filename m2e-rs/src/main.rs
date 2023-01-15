#![no_std]
#![no_main]
#![feature(alloc_error_handler)]

pub mod chase;
pub mod sr;
pub mod armv8;
pub mod mem;

pub use sr::SystemRegister;
use mem::ALLOCATOR;

use core::panic::PanicInfo;
use core::arch::asm;

core::arch::global_asm!("
.section .text

// x0=heap_base_ptr, x1=ctx_ptr
.global _start
_start:
    b main

//    // Before anything else happens: save the original SP and LR somewhere!
//    //
//    mov x8, sp
//    str x8,  [x1, #0x00]
//    str lr,  [x1, #0x08]
//    str x29, [x1, #0x10]
//    str x28, [x1, #0x18]
//    str x27, [x1, #0x20]
//    str x26, [x1, #0x28]
//    str x25, [x1, #0x30]
//    str x24, [x1, #0x38]
//    str x23, [x1, #0x40]
//    str x22, [x1, #0x48]
//    str x21, [x1, #0x50]
//    str x20, [x1, #0x58]
//    str x19, [x1, #0x60]
//    str x18, [x1, #0x68]
//    dmb sy
//    isb
//
//_do_main:
//    b main
//    hvc 0xdead
");


#[repr(C)]
pub enum ResultCode {
    OOM  = 1,
    ERR  = 2,
    OK   = 3,
}

#[repr(C)]
pub struct Context {
    saved_sp: usize,
    saved_lr: usize,
    saved_29_18: [usize; 12],
    rng: usize,
    value: u64,
}

pub static mut CONTEXT: *mut Context = usize::MAX as *mut Context;

/// Easy solution: simply assume that we will never panic
#[panic_handler]
pub unsafe extern "C" fn panic_handler(_info: &PanicInfo<'_>) -> ! {
    loop {}
}

#[no_mangle]
pub extern "C" fn main(heap_base: usize, ctx: *mut Context) -> usize {
    let mut rng  = chase::Xorshift64::new();

    unsafe {
        CONTEXT = ctx;
        ALLOCATOR.init(heap_base);
        clear_pmu_state();
    }

    //let mut maze = chase::PointerMaze::<0x0001_0000>::new();
    //maze.shuffle(&mut rng, 512);
    //maze.flush();

    test();

    ResultCode::OK as usize
}

pub fn test() {
    unsafe { 
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
        let val = sr::PMC0_EL1::read();
        (*CONTEXT).value = val;
        sr::PMC0_EL1::clear();
        armv8::isb();
    }
}


pub unsafe fn clear_pmu_state() {
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



