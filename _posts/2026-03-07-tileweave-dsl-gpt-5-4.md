---
title: "TileWeave: A Triton-Inspired DSL for a Verified VLIW SIMD Backend, Built with GPT-5.4"
date: 2026-03-07T00:05:00-05:00
categories:
  - Blog
tags:
  - vliw
  - simd
  - dsl
  - compilers
  - gpt-5.4
  - verification
classes: wide
permalink: /blog/tileweave-dsl-gpt-5-4/
---

This post is a follow-up to my earlier write-up, [Vibe Coding Hardware: Rebuilding Anthropic's VLIW SIMD Take-Home as an FPGA-Oriented SoC](/blog/vibe-coding-vliw-simd/).

The previous post focused on the hardware bring-up story: architecture choices, toolchain direction, verification stack, and what it felt like to use copilots while building a VLIW SIMD project for FPGA-oriented targets.

This one is about the next layer up the stack: the programming model.

Most of the recent work in this repository has shifted from "can the hardware run kernels?" to "can the programming model become pleasant without losing verification discipline?"

That is where `TileWeave` comes in.

`TileWeave` is the new high-level Python DSL frontend for this VLIW SIMD project. It is inspired by Triton and deliberately similar in block-programming style, but it lowers into a very different backend: a custom VLIW SIMD toolchain with scheduler-aware lowering, assembler emission, and RTL-backed validation.

One detail I want to make explicit: this DSL was created specifically using GPT-5.4 as the development copilot during design, implementation, refactoring, test updates, documentation work, and naming cleanup.

- Project repo: [https://github.com/aneesh64/experimental-vliw-simd/tree/main](https://github.com/aneesh64/experimental-vliw-simd/tree/main)
- Previous post: [Vibe Coding Hardware: Rebuilding Anthropic's VLIW SIMD Take-Home as an FPGA-Oriented SoC](/blog/vibe-coding-vliw-simd/)

## Why rename the frontend?

The original name in the repo was descriptive, but temporary. It read like an implementation note instead of a real programming surface.

`TileWeave` is a better fit for what the DSL is trying to do:
- express kernels in blocks and tiles
- compose scalar and vector behavior
- map logical tensor-style work onto a constrained SIMD machine
- stay extensible as engines, scratchpad layout, and instruction subsets evolve

The name matters because this is no longer just a quick façade experiment. It now has real compile coverage, real RTL coverage, and a growing set of authoring patterns.

## What TileWeave does today

The current verified subset includes:
- contiguous block kernels
- scalar broadcast via `splat()`
- elementwise `add`, `sub`, `mul`
- dual-output expressions
- tail-safe cleanup for non-multiple lengths
- automatic chunking of logical blocks larger than hardware `vlen`
- valid-prefix masked load/store
- affine strided row-major column access
- explicit overlapping affine launches for full column sweeps over a matrix

This is already enough to cover useful kernels that look much closer to modern accelerator DSL authoring than raw scheduler operations.

## What makes this interesting

A lot of DSL conversations stop at syntax. Here the interesting part is the full stack under the syntax:
- Python authoring frontend
- lowering into a scheduler-friendly IR
- bundle scheduling
- assembly into binary bundles
- cocotb-backed RTL execution
- golden checking against DMEM results

That means the DSL is not being judged by whether it "looks nice" alone. It is being judged by whether it survives actual backend lowering and hardware verification.

## Why GPT-5.4 mattered for this project

This was not a case of asking for one code snippet and pasting it in.

GPT-5.4 was useful because the work required keeping a lot of constraints in mind at the same time:
- existing scheduler and assembler behavior
- hardware vector width and scratchpad assumptions
- DSL ergonomics
- backward-compatible refactors
- unit-test updates
- RTL-backed integration coverage
- documentation and example quality

That combination is where a strong coding model actually becomes interesting.

In practice, GPT-5.4 helped with:
- multi-file refactors across the frontend, examples, tests, and docs
- preserving naming consistency during the `TileWeave` rebrand
- extending the frontend while keeping lowering behavior conservative
- reasoning about tail cleanup, chunking, masks, and strided access patterns
- generating and then tightening practical documentation for real kernel authoring
- keeping implementation work tied to verification instead of letting the frontend drift away from the backend

The useful capability here is not just raw code generation. It is sustained technical reasoning across a real codebase.

## What GPT-5.4 is especially good at in a codebase like this

Projects like this need more than autocomplete. They need a model that can:
- understand architecture spread across Python tooling, hardware docs, tests, and generated artifacts
- make coordinated edits across code, docs, and verification
- preserve invariants while renaming or restructuring public APIs
- explain tradeoffs clearly enough that documentation improves with the implementation
- work iteratively: add a feature, update tests, inspect failures, refine lowering, and repeat

That is exactly the kind of work where GPT-5.4 felt strong.

It was especially helpful for moving between abstraction layers without losing the thread:
- high-level DSL surface
- lowering decisions
- scheduler expectations
- assembler-facing constraints
- RTL validation strategy

That ability to hold the whole stack together is what made it a good fit for building a DSL on top of a nontrivial hardware backend.

## A concrete example

A simple TileWeave gain kernel now looks like this:

```python
from dsl import TileWeaveKernelBuilder, U32


def build_gain_kernel():
    tw = TileWeaveKernelBuilder(
        "gain_kernel",
        length=24,
        block_size=8,
        tile_stride_elements=16,
        dtype=U32,
    )

    samples = tw.tensor("samples")
    out = tw.tensor("out")
    gain = tw.scalar("gain", default=2)

    pid = tw.program_id(0)
    offsets = tw.arange(0, 8)
    x = tw.load(samples, pid, offsets)
    tw.store(out, pid, offsets, x * tw.splat(gain))
    return tw.build()
```

That is a much nicer authoring surface than manually wiring pointer math, vector temporaries, and per-tile control flow by hand.

## The more interesting milestone: strided matrix work

The bigger change is that the DSL can now express conservative row-major column operations.

That matters because it is a bridge toward more realistic workloads:
- separable image filters
- DCT-style row/column passes
- matrix preprocessing
- FFT stage building blocks where logical problem sizes exceed the hardware vector width

The current implementation is intentionally conservative. Non-unit stride lowering may scalarize through gather/scatter when needed. That is fine. Correctness and RTL stability come first.

## Documentation cleanup was part of the work

The repo now has:
- a shorter top-level README focused on overview and status
- a proper docs index
- a TileWeave guide
- a broader DSL programming guide with practical examples
- a clearer status page for the project and DSL frontier

This was overdue. Once the frontend started becoming real, the repo needed the documentation structure to match.

## What comes next

The next major frontier is multi-axis launch support.

Right now the project has a good base for:
- 1D block programs
- affine row-major strided access
- overlapping launch strides via explicit program counts

The obvious next step is richer launch semantics like `program_id(1)`, row/column decomposition, and better 2D view composition.

## Bigger picture

I think the most interesting part of this project is not just the hardware or just the DSL. It is the connection between them.

A DSL becomes much more meaningful when it is tested against a real backend and real hardware semantics.

That is what makes `TileWeave` worth building out further.

And it is also what made GPT-5.4 genuinely useful here: not as a novelty, but as a tool that could help design, implement, refactor, document, and verify a programming model against a real compiler-and-hardware stack.

If you read the earlier post first, this follow-up should make the progression clearer: hardware first, then a real programming layer on top.

You can jump back here to the earlier write-up anytime: [Vibe Coding Hardware: Rebuilding Anthropic's VLIW SIMD Take-Home as an FPGA-Oriented SoC](/blog/vibe-coding-vliw-simd/).
