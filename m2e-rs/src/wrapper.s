
.include "./src/gadgets.s"

.section .text

// test_wrapper(pmcr0_bits: usize, scratch_addr: usize)
.global test_wrapper
test_wrapper:
	adr x8, _trampoline_saved_state
	mov x9, sp
	str x18, [x8, #0x00]
	str x19, [x8, #0x08]
	str x20, [x8, #0x10]
	str x21, [x8, #0x18]
	str x22, [x8, #0x20]
	str x23, [x8, #0x28]
	str x24, [x8, #0x30]
	str x25, [x8, #0x38]
	str x26, [x8, #0x40]
	str x27, [x8, #0x48]
	str x28, [x8, #0x50]
	str x29, [x8, #0x58]
	str lr,  [x8, #0x60]
	str x9,  [x8, #0x68]
	dsb sy

	// Put the real desired return address somewhere in memory.
	// Remember that these registers are carried into the test body. 
	// You want to clear everything else to free up physical registers.

	adr x27, _architectural_return_target
	str x27, [x1]
	mov x28, x1     // scratch_addr
	mov x29, x0     // pmcr0_bits
	dsb sy

	mov x0,  #0
	mov sp,  x0
	mov x1,  #0
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
	mov lr,  #0
	msr NZCV, x0

// After this point, alignment *really matters*.
// Everything is padded to 64B cachelines (that's 16 instructions).
// These machines have an 8-wide decode window. 

.balign 64
_start_measurement_0:
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
_start_measurement_1:
	nop
	nop
	nop
	nop
	nop
	nop
    msr s3_1_c15_c0_0, x29
    isb

// Branch and link to the gadget.
//
// The TLB flushing here is not strictly necessary, although it probably 
// increases the latency of ldst operations if you use them later...
//
// NOTE: Results may be extremely sensitive to the number of iterations taken
// in '_busy_loop', indicated by x1 here. Also, you choice of iterations here
// is a tradeoff:
//
//   - More iterations == longer latency between BL and RET, probably
//   - More iterations == more physical register allocations
//   - More iterations == more nonspeculative in-flight ops in the window
//

_branch_and_link_0:
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
_branch_and_link_1:
	nop
	nop
	nop
	mov x1, #64
	tlbi alle2is
	dsb sy
	isb
	bl _branch_and_link_target0

// See gadgets.s for details about these macros. 
// NOTE: You should consider emitting these at runtime ..
//
// At the moment, all of these results are for x1=64.
// All of these use FNEG as a marker, and you're expected to look at the value
// of SIMD events for feedback. 
//

_mispredicted_return_target:

	//gadget_num_windows   254  // (limit on disp+map+iss)
	//gadget_num_windows   255  // (limit on decode?)

	//gadget_nop_limit     2034 // (limit on disp+map+iss)
	//gadget_nop_limit     2042 // (limit on decode?)

	//gadget_mov_imm_limit 418  // (limit on disp+map)
	//gadget_mov_imm_limit 426  // (limit on decode?)

	//gadget_mov_reg_limit 594  // (limit on disp+map+iss)
	//gadget_mov_reg_limit 602  // (limit on decode?)

	//gadget_adr_limit     406, off=0xfffff // (limit on iss)
	//gadget_adr_limit     413, off=0xfffff // (limit on disp+map)
	//gadget_adr_limit     418, off=0xfffff // (limit on decode?)

	//gadget_add_imm_limit   370, xd=x0, xn=x0, imm=1 // (disp limit)

	//gadget_b_limit       78, off=4
	//gadget_bl_limit      78, off=4

	// NOTE: We're probably polluting the load/store queues with barrier
	// instructions in '_busy_loop' while this is occuring.
	// You probably need a different approach to measure these?

	//gadget_str_limit     63,  xd=lr
	//gadget_str_limit     126, xd=x0
	//gadget_ldr_limit     103, xd=x0

// Explicit NOP padding at the end to make things clearer.
// (Don't rely on .balign to guarantee that NOPs have been inserted here)
.rept 2048
	nop
.endr

// Simply changing the LR is sufficient to consistently mispredict RET.
// (This doesn't have anything to do with the state of the RAS apart from
// the most-recent entry AFAIK; any reasonable branch predictor should always 
// predict the previous LR, and it would be a mistake not to do so!).
//
// NOTE: This loop is very sensitive to all sorts of conditions. 
// Remember that this is also a tradeoff: you might be deferring the 
// resolution of the LR, but you're probably going to pay by consuming 
// other resources (ie. physical registers, the barriers/cache-maintinence
// ops cutting into the budget on in-flight load/stores, etc).
//
// NOTE: I know you *want* to try to use TLBI here to generate latency, 
// but you can't (it will *restart* fetch and re-speculate down the predicted 
// path every time).
//

.balign 64
_branch_and_link_target0:
	isb
_busy_loop:
	dc civac, x28
	dsb sy
	dc civac, x28
	subs x1, x1, #1
	b.ne _busy_loop
	ldr lr, [x28]
	ret

// This is the *architecturally valid* return address. 
.balign 4096
_architectural_return_target:
	isb
	dsb sy

// ============================================================================
// Clear PMCR0_EL1 (stopping the counters).
_end_measurement:
    msr s3_1_c15_c0_0, xzr
    isb

	// Restore our saved state and return to the caller
	adr x8, _trampoline_saved_state
	ldr x18, [x8, #0x00]
	ldr x19, [x8, #0x08]
	ldr x20, [x8, #0x10]
	ldr x21, [x8, #0x18]
	ldr x22, [x8, #0x20]
	ldr x23, [x8, #0x28]
	ldr x24, [x8, #0x30]
	ldr x25, [x8, #0x38]
	ldr x26, [x8, #0x40]
	ldr x27, [x8, #0x48]
	ldr x28, [x8, #0x50]
	ldr x29, [x8, #0x58]
	ldr lr,  [x8, #0x60]
	ldr x9,  [x8, #0x68]
	dsb sy
	mov sp, x9
    ret

_trampoline_saved_state:
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


