
use core::alloc::{ GlobalAlloc, Layout };
use core::cell::UnsafeCell;
use crate::common::{ ResultCode, exit };

extern crate alloc;
pub use alloc::boxed::Box;
pub use alloc::borrow::ToOwned;
pub use alloc::vec::*;
pub use alloc::vec;

/// Bare-minimum bump allocator.
///
/// NOTE: You *need* to call [Allocator::init] before using this. 
/// The heap base address is passed from m1n1 at the entrypoint. 
///
/// NOTE: We're single-threaded and probably won't be interrupted.
/// There's no need to complicate this with locking or anything.
///
pub struct Allocator {
    base: UnsafeCell<usize>,
    free: UnsafeCell<usize>,
}
impl Allocator {
    /// The size of the heap (in bytes).
    const ARENA_SIZE: usize = 512 * (1024 * 1024);

    /// Set the base address for this allocator.
    pub fn init(&self, base: usize) {
        unsafe { *self.base.get() = base; }
    }
    /// Read the base address for this allocator.
    pub fn get_base(&self) -> usize {
        unsafe { *self.base.get() }
    }
}
unsafe impl Sync for Allocator {}
unsafe impl GlobalAlloc for Allocator {
    unsafe fn dealloc(&self, _ptr: *mut u8, _layout: Layout) {}
    unsafe fn alloc(&self, layout: Layout) -> *mut u8 {
        let base = *self.base.get();
        let free = *self.free.get();

        let this_ptr = match free.checked_sub(layout.size()) {
            Some(next_free) => (base + next_free) & !(layout.align() - 1),
            None            => alloc_error_handler(layout),
        };
        match this_ptr.checked_sub(base) {
            Some(next_free) => *self.free.get() = next_free,
            None            => alloc_error_handler(layout),
        };
        this_ptr as *mut u8
    }
}

#[global_allocator]
pub static ALLOCATOR: Allocator = Allocator {
    free: UnsafeCell::new(Allocator::ARENA_SIZE),
    base: UnsafeCell::new(0),
};

#[alloc_error_handler]
fn alloc_error_handler(_layout: Layout) -> ! {
    exit(ResultCode::OOM);
}


