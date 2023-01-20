
.section .text

// This is the entrypoint called from m1n1.

.global _start
_start:

	// 
	adr x8, _entrypoint_saved_context
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
    bl main

// Presumably we can just call '_exit' from Rust and naively unwind 
// everything in case something goes horribly wrong. 

.global _exit
_exit:
	adr x8, _entrypoint_saved_context
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
	mov sp, x9
    ret

_entrypoint_saved_context:
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

.pool

