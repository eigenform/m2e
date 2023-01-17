//! Structures for deliberate pointer-chasing.
//!
//! See [eigenform/lamina](https://github.com/eigenform/lamina) for my
//! original x86_64 implementation.
//!
//! [PointerMaze::shuffle] is an implementation of [Sattolo's
//! algorithm](https://en.wikipedia.org/wiki/Fisher%E2%80%93Yates_shuffle).

use crate::mem::*;
use crate::armv8;

/// XorShift64* PRNG implementation.
///
/// # Safety
/// This is not designed to be safe (nor sound): the quality of randomness 
/// doesn't matter much for our purposes here. Do **not** use this elsewhere.
pub struct Xorshift64 { 
    pub val: usize 
}
impl Xorshift64 {

    /// Create a new PRNG seeded with the time-stamp counter.
    pub fn new() -> Self {
        Self { val: armv8::cntpct_el0() }
    }
    /// Update the state of the PRNG and return the next value.
    pub fn next(&mut self) -> usize {
        let mut next = self.val;
        next ^= next >> 12;
        next ^= next << 25;
        next ^= next >> 27;
        next  = next.wrapping_mul(0x2545f4914f6cdd1d);
        self.val = next;
        next
    }
}


/// Wrapper around a pointer.
#[derive(Clone, Copy, Debug)]
#[repr(transparent)]
pub struct Pointer(pub usize);
impl Default for Pointer {
    fn default() -> Self { Self(0) }
}

/// Storage for a cyclic chain of pointers.
///
/// The constant `SIZE` indicates the number of elements/pointers.
#[repr(C, align(4096))]
pub struct PointerMaze<const SIZE: usize> {
    pub data: Box<[Pointer]>, 
}
impl <const SIZE: usize> PointerMaze<SIZE> {

    // NOTE: You can't create a sized array and move it into a [Box] (you'll 
    // run out of stack space with the big arrays we need here!) This whole 
    // `.into_boxed_slice()` dance avoids those cases.
    pub fn new() -> Self {
        let mut res = Self { 
            data: vec![Pointer::default(); SIZE]
                .into_boxed_slice().to_owned()
        };
        res.initialize();
        res.flush();
        res
    }

    /// Get a pointer to the first entry.
    pub fn head_ptr(&self) -> *const Pointer { &self.data[0] }

    /// Get a pointer to the middle entry.
    pub fn mid_ptr(&self) -> *const Pointer { &self.data[SIZE / 2] }

    /// Get a pointer to the last entry.
    pub fn tail_ptr(&self) -> *const Pointer { &self.data[SIZE - 1] }

    /// Return the size of the structure in bytes.
    pub fn size_in_bytes(&self) -> usize {
        core::mem::size_of::<[Pointer; SIZE]>()
    }
    /// Return the number of cache lines occupied by this structure.
    pub fn size_in_lines(&self) -> usize {
        self.size_in_bytes() / 64
    }
    /// Return the number of elements (pointers) in this structure.
    pub fn len(&self) -> usize {
        SIZE
    }

    /// Flush all associated cache lines.
    pub fn flush(&mut self) {
        let head = self.data.as_ptr() as *const [u8; 64];
        for line_idx in 0..self.size_in_lines() {
            unsafe { 
                let ptr = head.offset(line_idx as isize) as *const u8;
                armv8::dc_civac(ptr);
            }
        }
    }

    /// Initialize each element with a pointer to itself.
    pub fn initialize(&mut self) {
        for idx in 0..SIZE {
            let ptr = &self.data[idx] as *const Pointer;
            self.data[idx] = Pointer(ptr as usize);
        }
    }

    /// Shuffle elements, producing a randomized cyclic linked-list. 
    pub fn shuffle(&mut self, rng: &mut Xorshift64, stride: usize) {
        for i in (1..SIZE / stride).rev() {
            let j = rng.next() % i;
            let a = j * stride;
            let b = i * stride;
            self.data.swap(a, b);
        }
    }
}

