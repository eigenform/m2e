
// These are all intended to be placed at '_mispredicted_return_target'.

// ======================================================================


// It seems likely that the maximum window is 2048 instructions. 
// This makes some sense if you consider that this region is 127 64B blocks, 
// and '_branch_and_link_target0' occupies a single 64B block. 
// This seems to indicate that the maximum number of in-flight 64B fetch
// blocks is 128. 
//
// You can see this limit drop [to 1039 NOP] when we invalidate the entire 
// icache before entering the test - presumably we're bottlenecked by the 
// front-end trying to fill it back up.
//
// (This also works for other instructions that resolve to NOP.)
.macro gadget_nop_limit count
	.rept \count
	nop
	.endr
	fneg d19, d19
.endm

// Check the number of speculated 8-wide decode windows. 
// Insert (count - 1) windows of 8 NOP, and then the last window with FNEG 
// at the very end. 
.macro gadget_num_windows count
	.rept (\count - 1)
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	.endr
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	fneg d19, d19
.endm

// Count the number of speculated 8-wide decode windows.
// (You should see one SIMD event per window)
.macro gadget_depth_by_fneg
	.rept 256
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	fneg d19, d19
	.endr
.endm

.macro gadget_b_limit count, off=0
	.rept \count
	b #\off
	.endr
	fneg d19, d19
.endm

.macro gadget_bl_limit count, off=0
	.rept \count
	bl #\off
	.endr
	fneg d19, d19
.endm

.macro gadget_mov_imm_limit count
	.rept \count
	mov x5, #1
	.endr
	fneg d19, d19
.endm

.macro gadget_adr_limit count, off=0
	.rept \count
	adr x5, #(\off)
	.endr
	fneg d19, d19
.endm

.macro gadget_str_limit count, xd=x0
	.rept \count
	str \xd, [x28]
	.endr
	fneg d19, d19
.endm

.macro gadget_stlf_limit count, str_xd=x0, ldr_xd=x1
	.rept \count
	str \str_xd, [x28]
	ldr \ldr_xd, [x28]
	.endr
	fneg d19, d19
.endm

.macro gadget_ldr_limit count, xd=x0
	.rept \count
	ldr \xd, [x28]
	.endr
	fneg d19, d19
.endm

.macro gadget_add_imm_limit count, xd=x0, xn=x0, imm=1
	.rept \count
	add \xd, \xn, #\imm
	.endr
	fneg d19, d19
.endm

.macro gadget_mov_reg_limit count
	.rept \count
	mov x5, x2
	.endr
	fneg d19, d19
.endm


