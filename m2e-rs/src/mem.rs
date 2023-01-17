
use core::alloc::{ GlobalAlloc, Layout };
use core::sync::atomic::*;
use core::cell::UnsafeCell;
use crate::{ ResultCode, exit };

extern crate alloc;
pub use alloc::boxed::Box;
pub use alloc::borrow::ToOwned;
pub use alloc::vec::*;
pub use alloc::vec;


/// Bare-minimum bump allocator.
///
/// NOTE: I think we're single-threaded, and AFAIK there isn't any reason
/// we should ever go off-CPU. Seems fine without atomics/locking?
///
/// NOTE: You *need* to call [Allocator::init] before using this. 
/// The heap base address is passed from m1n1 at the entrypoint. 
///
pub struct Allocator {
    base: UnsafeCell<usize>,
    free: UnsafeCell<usize>,
}
impl Allocator {
    const ARENA_SIZE: usize = 256 * (1024 * 1024);
    pub fn init(&self, base: usize) {
        unsafe { *self.base.get() = base; }
    }
    pub fn get_base(&self) -> usize {
        unsafe { *self.base.get() }
    }
}
unsafe impl Sync for Allocator {}
unsafe impl GlobalAlloc for Allocator {
    unsafe fn alloc(&self, layout: Layout) -> *mut u8 {
        let base = *self.base.get();
        let free = *self.free.get();

        let next_free = match free.checked_sub(layout.size()) {
            Some(x) => x,
            None    => alloc_error_handler(layout),
        };
        let this_ptr  = (base + next_free) & !(layout.align() - 1);
        let next_free = match this_ptr.checked_sub(base) {
            Some(x) => x,
            None    => alloc_error_handler(layout),
        };

        *self.free.get() = next_free;
        this_ptr as *mut u8
    }

    unsafe fn dealloc(&self, ptr: *mut u8, layout: Layout) {}
}

#[global_allocator]
pub static ALLOCATOR: Allocator = Allocator {
    free: UnsafeCell::new(Allocator::ARENA_SIZE),
    base: UnsafeCell::new(0),
};

#[alloc_error_handler]
fn alloc_error_handler(layout: Layout) -> ! {
    exit(ResultCode::OOM);
}

