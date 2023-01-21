#![no_std]
#![no_main]

use m2e::common::*;
use m2e::mem::*;

#[no_mangle]
pub fn main(heap_base: usize) -> ! {
    ALLOCATOR.init(heap_base);

    let myvec = Box::new([0xffu8; 0x100]);

    CONTEXT.get().set_payload(
        myvec.as_ptr(), 
        core::mem::size_of_val(&*myvec)
    );
    exit(ResultCode::OK)
}

