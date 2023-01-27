
.section .text

// measured_trampoline(pmcr0_bits: usize, func: usize, arg0: usize, arg1: usize)
.global measured_trampoline
measured_trampoline:
	adr x8, _trampoline_saved_state
	mov x9, sp
	stp x18, x19, [x8, #0x00]
	stp x20, x21, [x8, #0x10]
	stp x22, x23, [x8, #0x20]
	stp x24, x25, [x8, #0x30]
	stp x26, x27, [x8, #0x40]
	stp x28, x29, [x8, #0x50]
	stp x30, x9,  [x8, #0x60]
	dsb sy

	mov x30, x0 // pmcr0_bits
	mov x29, x1 // func
	mov x0,  x2 // arg0
	mov x1,  x3 // arg1

	mov sp,  x0
	msr NZCV,x0
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
	mov x27, #0
	mov x28, #0

.balign 64
_trampoline_call:
	nop
	nop
	nop
	nop
	nop
    msr s3_1_c15_c0_0, x30
    isb
	blr x29

_trampoline_return:
    msr s3_1_c15_c0_0, xzr
    isb
	nop
	nop
	nop
	nop
	nop
	nop

	adr x8, _trampoline_saved_state
	ldp x18, x19, [x8, #0x00]
	ldp x20, x21, [x8, #0x10]
	ldp x22, x23, [x8, #0x20]
	ldp x24, x25, [x8, #0x30]
	ldp x26, x27, [x8, #0x40]
	ldp x28, x29, [x8, #0x50]
	ldp x30, x9,  [x8, #0x60]
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


