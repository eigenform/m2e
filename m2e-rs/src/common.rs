
use core::panic::PanicInfo;
use core::cell::UnsafeCell;

extern "C" {
    /// Terminate the program by returning to m1n1.
    ///
    /// This function is defined in 'start.s'.
    /// The argument in x0 ('ctx') is returned to m1n1 after:
    ///
    ///     - Restoring the caller's non-volatile registers
    ///     - Restoring the stack pointer saved at the entrypoint
    ///     - Restoring the link register saved at the entrypoint
    ///
    pub fn _exit(ctx: *const ResultContext) -> !;
}

/// Jump to program exit and return to m1n1. 
pub fn exit(res: ResultCode) -> ! {
    unsafe { 
        CONTEXT.get().set_result(res);
        _exit(CONTEXT.get())
    }
}

#[repr(C)]
pub enum ResultCode {
    OOM   = 1,
    PANIC = 2,
    OK    = 3,
}

/// Context passed to m1n1 after program exit.
#[repr(C, align(0x100))]
pub struct ResultContext {
    pub result: ResultCode,
    pub payload: *const u8, 
    pub len: usize,
}
impl ResultContext {
    pub fn set_payload(&mut self, payload: *const u8, len: usize) {
        self.payload = payload;
        self.len = len;
    }
    pub fn set_result(&mut self, result: ResultCode) {
        self.result = result;
    }
}

/// This is only for giving us a way to do static mutable [ResultContext].
pub struct StaticCell<T>(pub UnsafeCell<T>);
unsafe impl <T> Sync for StaticCell<T> {}
impl <T> StaticCell<T> { 
    pub const fn new(x: T) -> Self { Self(UnsafeCell::new(x)) }
    pub fn get(&self) -> &mut T {
        unsafe { 
            self.0.get().as_mut().unwrap()
        }
    }
}

pub static CONTEXT: StaticCell<ResultContext> = StaticCell::new(
    ResultContext { 
        result: ResultCode::OK,
        payload: 0 as *const u8,
        len: 0,
    }
);

/// Panic handler. 
///
/// NOTE: We could probably pull data out of [PanicInfo] if necessary.
#[panic_handler]
#[no_mangle]
pub unsafe extern "C" fn panic_handler(_info: &PanicInfo<'_>) -> ! {
    let ctx = CONTEXT.get();
    ctx.set_result(ResultCode::PANIC);
    _exit(ctx)
}


