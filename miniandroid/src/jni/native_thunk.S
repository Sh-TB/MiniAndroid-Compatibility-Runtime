/*
 * native_thunk.S — System V x86_64 dynamic native-call thunk (S-2 layer).
 *
 * JNI native functions take (JNIEnv*, receiver, <app args...>) where each
 * app arg is classified INTEGER (ints, longs, booleans, chars, shorts,
 * bytes, references) or SSE (float/double). A plain C function-pointer cast
 * mis-assigns SSE args to integer registers, so any float/double JNI
 * signature would corrupt. This thunk assigns registers dynamically:
 *
 *   INTEGER-class → rdi, rsi, rdx, rcx, r8, r9, then overflow stack (order)
 *   SSE-class     → xmm0..xmm7, then overflow stack (order)
 *
 * Overflow stack slots are 8 bytes each in ARGUMENT ORDER, exactly the
 * SysV layout the callee expects.
 *
 * C prototype:
 *   extern "C" uint64_t miniandroid_native_thunk(
 *       void* fn,                 // callee
 *       const void* stack_args,   // overflow args, 8 bytes each, in order
 *       size_t n_stack_args,      // overflow arg count
 *       const uint64_t* int_regs, // INTEGER-class args (>=6 entries)
 *       const double*  sse_regs,  // SSE-class args (>=8 entries)
 *       void* sse_ret);           // if non-null: receives xmm0 as double
 *   Returns the callee's INTEGER-class return (rax).
 */
    .text
    .globl miniandroid_native_thunk
    .type  miniandroid_native_thunk, @function
    .align 16
miniandroid_native_thunk:
    /* F-NEW-593 (W10) — UNWIND-THROUGH-THUNK LAW. The thunk had no
     * .eh_frame: a C++ exception thrown inside the real native (live
     * face: queens RunBundleAndSnapshotFromLibrary aborts via
     * std::terminate after the null-marshal fix — the unwinder found no
     * FDE for this frame and called terminate → SIGABRT, W10 fault
     * trace) could never propagate to run_native_guarded's catch. The
     * frame-pointer CFI below makes THIS frame unwound exactly like a
     * compiled C++ frame: CFA = rbp+16 (the dynamic rsp manipulation in
     * the body is invisible to the unwinder because CFA is rbp-based).
     * run_native_guarded then catches the exception and reports it
     * honestly — the AOSP JNI boundary contract (art's FaultHandler /
     * exception scoping), not a process-death abort. */
    .cfi_startproc
    push   %rbp
    .cfi_def_cfa_offset 16
    .cfi_offset rbp, -16
    mov    %rsp, %rbp
    .cfi_def_cfa_register rbp
    push   %rbx
    .cfi_offset rbx, -24
    push   %r12
    .cfi_offset r12, -32
    push   %r13
    .cfi_offset r13, -40
    push   %r14
    .cfi_offset r14, -48
    push   %r15
    .cfi_offset r15, -56
    /* entry args: rdi=fn rsi=stack_args rdx=n rcx=int_regs r8=sse_regs r9=sse_ret */
    mov    %rdi, %rbx          # fn
    mov    %rsi, %r12          # stack_args
    mov    %rdx, %r13          # n_stack_args
    mov    %r9,  %r14          # sse_ret
    mov    %rcx, %r15          # int_regs base
    # load SSE regs first (r8 still holds the sse_regs pointer)
    movsd  0(%r8),  %xmm0
    movsd  8(%r8),  %xmm1
    movsd  16(%r8), %xmm2
    movsd  24(%r8), %xmm3
    movsd  32(%r8), %xmm4
    movsd  40(%r8), %xmm5
    movsd  48(%r8), %xmm6
    movsd  56(%r8), %xmm7
    # load INTEGER regs (r15 base survives its own loads)
    mov    0(%r15),  %rdi
    mov    8(%r15),  %rsi
    mov    16(%r15), %rdx
    mov    24(%r15), %rcx
    mov    32(%r15), %r8
    mov    40(%r15), %r9
    # reserve aligned overflow-arg space and copy n*8 bytes (arg order)
    mov    %r13, %rax
    shl    $3,  %rax
    add    $15, %rax
    and    $-16, %rax
    sub    %rax, %rsp
    and    $-16, %rsp
    xor    %r10, %r10
copy_loop:
    cmp    %r13, %r10
    jge    copy_done
    mov    (%r12,%r10,8), %rax
    mov    %rax, (%rsp,%r10,8)
    inc    %r10
    jmp    copy_loop
copy_done:
    call   *%rbx
    # epilogue
    lea    -40(%rbp), %rsp
    test   %r14, %r14
    jz     no_sse_ret
    movsd  %xmm0, (%r14)
no_sse_ret:
    pop    %r15
    .cfi_restore r15
    pop    %r14
    .cfi_restore r14
    pop    %r13
    .cfi_restore r13
    pop    %r12
    .cfi_restore r12
    pop    %rbx
    .cfi_restore rbx
    pop    %rbp
    .cfi_restore rbp
    .cfi_def_cfa rsp, 8
    ret
    .cfi_endproc
    .size miniandroid_native_thunk, .-miniandroid_native_thunk
