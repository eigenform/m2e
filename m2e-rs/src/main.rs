#![no_std]
#![no_main]
#![feature(alloc_error_handler)]

pub mod chase;
pub mod sr;
pub mod armv8;
pub mod mem;
pub mod common;
pub mod pmu;

use mem::*;
use common::*;
use pmu::*;

core::arch::global_asm!(include_str!("start.s"));

#[no_mangle]
pub extern "C" fn main(heap_base: usize) -> ! {
    ALLOCATOR.init(heap_base);
    assert!(heap_base == ALLOCATOR.get_base());
    clear_pmu_state();

    let mut rng  = chase::Xorshift64::new();
    let mut maze = chase::PointerMaze::<0x0000_0100>::new();
    maze.shuffle(&mut rng, 4);
    maze.flush();

    //panic!("this is a test");

    exit(ResultCode::OK)
}

