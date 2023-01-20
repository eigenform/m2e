
.section .text

// test_wrapper(pmcr0_bits: usize)
.global test_wrapper
test_wrapper:

	// Preserve the SP, LR, and all non-volatile GPRs
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

	mov x29, x0 // pmcr0_bits

	// Clear as many general-purpose registers as possible.
	// We want to prevent the machine from carrying dependences into the test.

	mov x0, xzr
	mov sp, x0
	mov x1, xzr
	mov x2, xzr
	mov x3, xzr
	mov x4, xzr
	mov x5, xzr
	mov x6, xzr
	mov x7, xzr
	mov x8, xzr
	mov x9, xzr
	mov x10, xzr
	mov x11, xzr
	mov x12, xzr
	mov x13, xzr
	mov x14, xzr
	mov x15, xzr
	mov x16, xzr
	mov x17, xzr
	mov x18, xzr
	mov x19, xzr
	mov x20, xzr
	mov x21, xzr
	mov x22, xzr
	mov x23, xzr
	mov x24, xzr
	mov x25, xzr
	mov x26, xzr
	mov x27, xzr
	mov x28, xzr
	mov lr, xzr

	msr NZCV, xzr

// Write PMCR0_EL1 (starting the counters).
//
// NOTE: I wonder about how alignment might affect this.
//
.balign 64
_start_measurement:
    msr s3_1_c15_c0_0, x29
    isb

test_body:


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


