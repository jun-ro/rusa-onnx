# Rusa — in-browser rewriter

A single-page app that runs [`jun-ai/Rusa`](https://huggingface.co/jun-ai/Rusa)
(350 M parameter English rewriter, LFM2-350M base) on the Q4 ONNX export, fully
client-side. No server, no API keys.

**Hosted:** https://jun-ro.github.io/rusa-onnx/ — the page is ~25 kB; the first
visit downloads the 289 MB of weights from the Hugging Face CDN (then cached by
the browser).

## What it does

Rusa is not a chat model. It rewrites a draft so it reads like a person wrote
it, keeping facts, numbers and quotes intact. The app builds the prompt the
model was trained on:

```
<instruction>

<your draft>

### Rewritten:
```

Sampling defaults follow the model card: `temperature=1.0`, `top_p=0.95`,
`top_k=0`, no repetition penalty. The instruction is editable in the settings
strip.

## Run locally

```bash
git clone https://github.com/jun-ro/rusa-onnx
cd rusa-onnx
./start.sh                 # http://localhost:8000
```

The repo does not contain the weights. Without `./model/`, the page pulls them
from Hugging Face exactly like the hosted copy. To run fully offline, put the
Q4 export next to `index.html`:

```
model/
├── config.json
├── tokenizer.json
├── tokenizer_config.json
├── special_tokens_map.json
├── generation_config.json
└── onnx/
    ├── model_q4.onnx            (~180 kB graph)
    └── model_q4.onnx_data       (~289 MB weights)
```

```bash
hf download jun-ai/Rusa --include "onnx/model_q4*" "*.json" --local-dir model
```

Serving over plain HTTP is required (not `file://`), and `serve.py` sends the
COOP/COEP headers that let the WASM backend use more than one thread. GitHub
Pages cannot send those headers, so the hosted copy runs single-threaded on
CPU — WebGPU is unaffected.

## Backends

| Backend | State | Notes |
| --- | --- | --- |
| WebGPU, real GPU | works | fast path, 4-bit matmuls on the GPU |
| WebGPU via SwiftShader | loads, unusable | software rasteriser, pegs every core |
| CPU / WASM | works | needs the plain ORT build, see below |

The page asks `navigator.gpu.requestAdapter()` and only selects WebGPU for a
real hardware adapter; `swiftshader` / `llvmpipe` mean it stays on CPU. The
dropdown lets you override it.

### WebGPU needs Vulkan on Linux

Chromium implements WebGPU on top of Vulkan. On some Intel iGPUs (Gen11 /
Jasper Lake, for instance) Chromium leaves Vulkan off, so `requestAdapter()`
silently returns SwiftShader. `chrome://gpu` shows it as
`vulkan: disabled_off` and `webgpu: unavailable_software`.

Start the browser with Vulkan enabled:

```bash
brave-browser --enable-features=Vulkan
# flatpak:
flatpak run com.brave.Browser --enable-features=Vulkan
```

The page then reports `adapter: intel | gen-11` and runs on the GPU.

### Why the CPU path needs a runtime override

4-bit exports keep the embedding table in `GatherBlockQuantized`, an ONNX
Runtime contrib op. Transformers.js 4.x defaults to the `asyncify` WASM build,
which has no CPU kernel for it, so session creation fails with
`Could not find an implementation for GatherBlockQuantized(1)`.

`index.html` points ORT at the plain `ort-wasm-simd-threaded` build whenever
the backend is `wasm`. Switching backends reloads the page because the runtime
is initialised once per document.

## Model and licence

The weights are downloaded from
[`jun-ai/Rusa`](https://huggingface.co/jun-ai/Rusa) and are licensed under the
[LFM Open License v1.0](https://huggingface.co/jun-ai/Rusa/blob/main/LICENSE).
This repository contains only the web app; it does not redistribute the model.
