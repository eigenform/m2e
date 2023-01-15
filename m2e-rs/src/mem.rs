
use core::alloc::{ GlobalAlloc, Layout };


extern crate alloc;
pub use alloc::boxed::Box;
pub use alloc::borrow::ToOwned;
pub use alloc::vec;

const ARENA_SIZE: usize = 256 * (1024 * 1024);
const MAX_SUPPORTED_ALIGN: usize = 4096;

pub struct Allocator {
    size: usize,
    base: usize,
    end:  usize,
    next: usize,
    ctr:  usize,
}
impl Allocator {
    pub fn init(&mut self, base: usize) {
        self.base = base;
        self.end  = base + ARENA_SIZE;
        self.next = base;
        self.ctr  = 0;
    }
}

#[global_allocator]
pub static mut ALLOCATOR: Allocator = Allocator {
    size: ARENA_SIZE,
    base: usize::MAX,
    end:  usize::MAX,
    next: usize::MAX,
    ctr:  usize::MIN,
};

fn align_up(addr: usize, align: usize) -> usize { 
    (addr + align - 1) & !(align - 1)
}

unsafe impl Sync for Allocator {}
unsafe impl GlobalAlloc for Allocator {
    unsafe fn alloc(&self, layout: Layout) -> *mut u8 {

        let start = align_up(self.next, layout.align());
        let end   = match start.checked_add(layout.size()) {
            Some(end) => end,
            None => usize::MAX
        };

        if end > self.end {
            usize::MAX as *mut u8
        } else {
            self.next = end;
            self.ctr += 1;
            start as *mut u8
        }
    }
    unsafe fn dealloc(&self, ptr: *mut u8, layout: Layout) {
        self.ctr -= 1;
        if self.ctr == 0 {
            self.next = self.base;
        }
    }
}

#[alloc_error_handler]
fn alloc_error_handler(layout: Layout) -> ! {
    panic!("oom");
}

