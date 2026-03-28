---
title: "Adding True FP32 and a Matrix Engine to a Verified VLIW SIMD Core"
date: 2026-03-28T00:05:00-05:00
categories:
  - Blog
tags:
  - vliw
  - simd
  - fp32
  - matrix-engine
  - spinalhdl
  - verification
classes: wide
permalink: /blog/floating-point-matrix-engine-vliw-simd/
---

This post is a follow-up to my earlier write-up, [Vibe Coding Hardware: Rebuilding Anthropic's VLIW SIMD Take-Home as an FPGA-Oriented SoC](/blog/vibe-coding-vliw-simd/).

That earlier post was about architecture and bring-up. This one is about capability expansion: adding true IEEE-754 FP32 scalar/vector execution and a dedicated matrix engine path, while keeping the implementation inspectable and verification-driven.

Project repo:
- [https://github.com/aneesh64/experimental-vliw-simd/tree/main](https://github.com/aneesh64/experimental-vliw-simd/tree/main)

## Why these two additions mattered

The original integer-focused machine was enough to validate the VLIW bundle format, scratchpad banking model, scheduler, and cocotb flow.

But once that base is working, the next question is obvious:

Can the same backend support kernels that look more like real DSP and ML work?

That means two things:

- general scalar/vector FP32 for conversion-heavy and numerically sensitive kernels
- a tile-oriented matrix engine for dense multiply-accumulate work

That is the transition from a pure verification platform into something that starts to look like a small accelerator stack.

## Architecture context

The machine is still a VLIW SIMD core with distinct execution engines behind a shared issue/decode model.

![VLIW SIMD architecture](/assets/images/diagrams/vliw-simd-arch.svg)

The mental model for the new compute paths looks like this:

```text
                    +-----------------------------+
                    |         Decode / Issue      |
                    +--------------+--------------+
                                   |
        +--------------------------+---------------------------+
        |                          |                           |
        v                          v                           v
+---------------+         +----------------+          +----------------+
| Scalar ALU    |         | Vector ALU     |          | Matrix Engine  |
| INT + FP32    |         | INT + FP32     |          | 8x8 tile path  |
+-------+-------+         +--------+-------+          +--------+-------+
        |                          |                           |
        +-------------+------------+---------------------------+
                      |
                      v
              +---------------+
              | Scratchpad /   |
              | Matrix local   |
              | memories       |
              +---------------+
```

The matrix engine is intentionally a micro-sequenced reference design over dedicated local memories, not a peak-throughput PE array. The goal for this revision was correctness, ISA coverage, and clean verification.

## The FP32 ISA surface

The scalar ALU gained these FP32 operations:

| Opcode | Mnemonic | Meaning |
|---|---|---|
| 18 | `fadd` | IEEE-754 FP32 add |
| 19 | `fsub` | IEEE-754 FP32 subtract |
| 20 | `fmul` | IEEE-754 FP32 multiply |
| 21 | `fmax` | FP32 max |
| 22 | `fmin` | FP32 min |
| 23 | `i2f` | signed int32 to FP32 |
| 24 | `f2i` | FP32 to signed int32 |
| 25 | `u2f` | unsigned int32 to FP32 |
| 26 | `f2u` | FP32 to unsigned int32 |

The vector ALU gained the corresponding lane-wise FP32 operations.

I kept one important boundary in place: there is still no hardware FP32 divide. That was a deliberate complexity cut.

I also added `fmadd` and `vfmadd` as software pseudo-ops rather than fused hardware FMA. They lower as:

```text
fmadd  dst, a, b, c   ->   fmul  tmp, a, b
                           fadd  dst, tmp, c

vfmadd dst, a, b, c   ->   vfmul tmp, a, b
                           vfadd dst, tmp, c
```

That improves the programming model without requiring a fused datapath in RTL.

## What "true FP32" means here

The first floating-point path in this project was not a true floating-point implementation. It was useful for plumbing, but not the right endpoint.

The current implementation is a real bit-level FP32 execution unit in SpinalHDL. It works directly on IEEE-754 sign, exponent, and significand fields, performs alignment and normalization explicitly, and rounds to nearest even.

The execution model is serialized:

- one FP32 op in flight per unit
- add/sub/max/min/conversions complete after the configured add-class latency
- multiply completes after the configured multiply-class latency

For the current core configuration that means:

- add-class FP32 ops: 4 cycles
- FP32 multiply: 5 cycles

That sounds like a small note, but it matters to the software stack. The scheduler also had to be updated to understand when the result is actually visible for reuse.

## The SpinalHDL FP32 unit

The implementation lives in `Fp32Unit.scala` and is intentionally explicit.

A good example is the pack-and-round stage:

```scala
private def roundPack(sign: Bool, expIn: SInt, sigIn: UInt): UInt = {
  val result = UInt(32 bits)
  result := (sign.asBits ## B(0, 31 bits)).asUInt

  val needsSubnormalShift = expIn < S(MinNormalExp, ExpWidth bits)
  val subShift = UInt(ExpWidth bits)
  subShift := 0
  when(needsSubnormalShift) {
    subShift := (S(MinNormalExp, ExpWidth bits) - expIn).asUInt.resize(ExpWidth)
  }

  val sigForRound = UInt(ExtSigWidth bits)
  sigForRound := sigIn
  when(needsSubnormalShift) {
    sigForRound := shiftRightJamTo(sigIn, subShift, ExtSigWidth, 31)
  }

  val mantPre = sigForRound(26 downto 3)
  val roundUp = sigForRound(2) && (sigForRound(1) || sigForRound(0) || mantPre(0))
  val mantRounded = (mantPre.resize(25) + roundUp.asUInt.resize(25)).resize(25)
  ...
}
```

This is why I call it a true FP32 implementation rather than a convenience approximation. The RTL is explicit about:

- subnormal handling via shift-and-jam
- normalization and exponent movement
- guard / round / sticky behavior
- round-to-nearest-even

That makes the behavior debuggable at the waveform and cocotb level.

## Matrix engine model

The other large addition is the matrix engine.

This revision fixes the engine shape and storage model to:

- 8x8 tile shape
- 8-bit matrix-local operand storage
- 32-bit accumulator storage
- one matrix slot occupying the engine until completion

The supported compute modes are:

- signed int8 multiply into accumulated results
- FP8 E4M3 multiply into FP32 accumulation
- FP8 E5M2 multiply into FP32 accumulation

That makes the engine useful both for classical integer kernels and for low-precision inference-style workloads.

## Matrix ISA surface

The matrix ISA now includes these FP8 modes:

| Opcode | Mnemonic | Meaning |
|---|---|---|
| 10 | `mcompute_fp8_e4m3` | FP8 E4M3 matrix multiply into FP32 accumulator |
| 11 | `mcompute_fp8_e4m3_acc` | FP8 E4M3 matrix multiply-accumulate |
| 12 | `mcompute_fp8_e5m2` | FP8 E5M2 matrix multiply into FP32 accumulator |
| 13 | `mcompute_fp8_e5m2_acc` | FP8 E5M2 matrix multiply-accumulate |

The assembler tuple form mirrors the existing matrix op style:

```text
("mcompute_fp8_e4m3", dest, srcA, srcB[, srcC[, tileRows[, tileCols[, flags]]]])
```

The important semantic choice is that accumulation remains FP32 even when the source operands are FP8.

## How the matrix engine is implemented

The top of `MatrixEngine.scala` says exactly what kind of design this is:

```scala
/**
 * Matrix Engine v1 functional model.
 *
 * Fixed configuration:
 *   - 8x8 matrix shape
 *   - 8-bit matrix-local operand storage
 *   - 32-bit accumulator storage
 *   - one matrix slot may occupy the engine until completion
 */
```

The FP8 path decodes compact FP8 values into a representation that can contribute to a fixed-point accumulation path before being packed back into FP32 accumulator state.

A representative helper is:

```scala
def fixedContributionFromFp8(a: Fp8Decoded, b: Fp8Decoded): SInt = {
  val shiftSum = UInt(7 bits)
  shiftSum := a.shift.resize(7) + b.shift.resize(7)
  val productShift = (shiftSum - U(FpAccumFracBits, 7 bits)).resize(6)
  val sigProduct = (a.sig.resize(8) * b.sig.resize(8)).resize(8)
  val magnitude = UInt(FpAccumBits bits)
  magnitude := 0

  when(!a.isZero && !b.isZero) {
    for (shift <- 0 to MaxFpProductShift) {
      when(productShift === U(shift, 6 bits)) {
        magnitude := (sigProduct.resize(FpAccumBits) << shift).resize(FpAccumBits)
      }
    }
  }

  val signed = SInt(FpAccumBits bits)
  signed := magnitude.asSInt
  when(a.sign ^ b.sign) {
    signed := -magnitude.asSInt
  }
  signed
}
```

This is not optimized for peak throughput. It is optimized for clarity and correctness:

- explicit FP8 decode behavior
- explicit local-memory interaction
- explicit accumulator semantics
- a clean path to cocotb golden-model comparison

That is the right place to start.

## What the programming model looks like

At the matrix ISA level, the sequence now looks like a real accelerator workflow:

```text
mzero                    acc0
mdmvin                   A_tile  -> matrixA
mdmvin                   B_tile  -> matrixB
mcompute_fp8_e4m3_acc    acc0, matrixA, matrixB
mdmvout                  acc0    -> out_tile
```

At the scalar/vector level, the FP32 additions mean the core can now express kernels that mix integer setup and floating-point math naturally.

That matters for workloads like:

- quantization and dequantization paths
- affine transforms
- small DSP kernels
- mixed address-generation and floating-point compute pipelines

## Verification mattered more than the opcode count

The reason I am confident in these additions is not that the RTL elaborated.

It is that the changes were pushed through multiple layers of verification:

- ALU and VALU cocotb tests for scalar and vector FP32 behavior
- full-core scalar FP32 integration tests
- full-core vector FP32 integration tests
- conversion and extrema coverage
- FMADD / VFMADD pseudo-op coverage
- matrix-engine unit tests
- matrix-engine integration and driver-style tests

I also added a focused FP32 integration alias so the floating-point regressions are easy to rerun:

```bash
python verification/cocotb/integration/run_integration.py --modules fp32
```

That sort of tooling detail matters. A feature that is annoying to regress tends to decay.

## What had to change outside RTL

A true FP32 path forces software changes too.

The scheduler had to understand:

- the serialized nature of the FP32 unit
- different FP32 latencies for add-class and multiply-class ops
- when results become visible to later bundles
- how FMADD pseudo-ops should lower without pretending they are fused

On top of that, the repo now has broader driver examples and emitted artifacts for matrix workloads, including a TurboQuant-style 32x32 flow.

That end-to-end story is what makes the project interesting to me. The hardware, toolchain, driver layer, and verification stack all moved together.

## Why I like this direction

This project is still intentionally conservative.

The matrix engine is a reference engine, not a peak-throughput systolic array.
The FP32 unit is serialized, not a many-lane floating-point cluster.
FMADD is a pseudo-op, not fused hardware FMA.
There is no FP32 divide.

But those constraints are useful.

They kept the implementation understandable while still adding genuinely important capability.

That is the style I want for this repository:

- add capability
- keep the implementation inspectable
- verify it end to end
- only then make it faster

## Closing thought

The most satisfying part of this milestone is that the project now has two distinct floating-point stories:

- general scalar/vector FP32 for ordinary compute kernels
- structured low-precision matrix compute with FP32 accumulation

That is a much stronger base for future compiler, DSL, and hardware work than an integer-only machine.

And because the implementation is explicit in SpinalHDL and backed by cocotb regressions, the project stays in the category I care about most:

not just features added, but features that are understandable and testable.
