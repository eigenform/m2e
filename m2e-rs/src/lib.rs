//! Simple environment for running Rust on top of m1n1. 
//!
//! In general, this whole thing is wildly unsafe.
//! I haven't managed to brick the machine though, so that's nice.
//!
//! About the environment (m1n1)
//! ============================
//!
//! Note that you *need* to call the following from the proxy client before
//! issuing `smp_call_sync()`, otherwise you will probably crash hard:
//!
//!     - `smp_start_secondaries()` (start up the other cores)
//!     - `mmu_init_secondary(cpu)` (set up the MMU on a particular core)
//!
//! The m1n1 proxyclient exposes a function `smp_call_sync()`, which you can 
//! use to synchronously run code on a particular core. Secondary cores idle 
//! in `smp_secondary_entry()` until some request occurs from an `smp_call()`.
//!
//! These are not SMT (simultaneous multithreading) cores, so assuming that
//! we don't receive any other interrupts during execution, programs should
//! not have to worry about being off-CPU. 
//!
//! Exceptions and Panic Handling
//! =============================
//!
//! It seems like the proxy usually traps and prints exceptions, but you
//! should probably write programs assuming that we have no guarantees about 
//! graceful recovery from potential exceptions.
//!
//! Rust panic handling seems to work fine, although right now the best we
//! can do is write [ResultCode::PANIC] and return to m1n1.
//!
//! Missing Features
//! ================
//!
//! - It'd be nice to have a way to assemble AArch64 code in-memory.
//!   This would make writing experiments very painless. 
//!
//! - Actually send useful info to the host when panicking
//!
//!
//! Using this library
//! ==================
//!
//! Programs begin in `_start` (defined in 'start.s') and jump to 'main'.
//!
//! When you're writing binaries, you'll want to do something like this
//! (otherwise `ld.lld` will become very angry with you):
//!
//! ```
//! pub extern "C" fn main(heap_base: usize) -> ! {
//!     // ...
//!     exit(ResultCode::OK)
//! }
//! ```
//!
//! For now, programs are expected to return a pointer to a [ResultContext] 
//! describing whatever data we'd like to retrieve with reads from the proxy 
//! client. This is automatically handled by [exit]. 
//!

#![no_std]
#![no_main]

#![feature(alloc_error_handler)]
#![feature(naked_functions)]

#![allow(non_camel_case_types)]
#![allow(unused_parens)]

pub mod chase;
pub mod sr;
pub mod armv8;
pub mod mem;
pub mod common;
pub mod pmu;

pub use core::assert;

// The entrypoint and exit point for binaries using this runtime.
core::arch::global_asm!(core::include_str!("start.s"));


