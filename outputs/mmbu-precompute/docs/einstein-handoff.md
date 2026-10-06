# Einstein IT and first-session handoff

Current fact: the user reports an Einstein GPU that is behaving unreliably and plans to speak with IT. We have not connected, diagnosed the cause, or verified its type or usable memory. No scheduler, host address, CUDA version or allocation command is assumed here.

Ask IT for the normal supported workflow and record:

1. Whether access uses a scheduler, notebook service or direct host; the supported way to obtain an interactive GPU allocation and a batch job.
2. GPU model, usable memory, count available to this team, allocation duration, quota and expected queue limits; whether the GPU is partitioned/shared.
3. Supported driver, Python/environment or container image, writable scratch location, storage quota, and whether model/data downloads are allowed from worker nodes.
4. The current failure's cause, any incident reference, and a minimal successful GPU check inside the allocated worker session.

Inside the GPU allocation, if it is NVIDIA, preserve the output of `nvidia-smi` and `python3 --version`. Do not conclude that a login node without a visible GPU means the allocated GPU is broken. Do not reinstall drivers, change permissions or alter shared environments to work around the problem. Redact credentials before sharing logs.

After access works:

- Copy this preparation directory and run the offline test suite and demo first; it requires no CUDA libraries.
- Record the supported environment and exact driver/runtime versions. Pin a compatible maintained trainer only after checking the actual model requirements and IT constraints.
- Start with the initial model's pinned revision from `configs/model-registry.json`, confirm allowed network/storage and measure native inference on a small approved external engineering set. No training job is ready merely because nvidia-smi works.
- Verify the native processor/template and independently constructed task/context passes. Check raw output, image token/resolution limits, actual vision/language/projection/adapter parameter counts, and memory peaks.
- Reproduce a non-quantized BF16/FP16 export/reload before scaling. Then time a short training step sequence, both evaluation passes and judging; fill `configs/experiment-record.template.json` with actual costs and limits.
- Run the language-adapter pilot and bounded visual-component probe only after source QA and the relevant protocol decisions are recorded. Compare two feasible models under matched exposure; retain uncertain rankings.

Model cards for the planned candidates: [Qwen2.5-VL-7B-Instruct](https://huggingface.co/Qwen/Qwen2.5-VL-7B-Instruct), [Qwen3.5-9B](https://huggingface.co/Qwen/Qwen3.5-9B), [Qwen3-VL-8B-Instruct](https://huggingface.co/Qwen/Qwen3-VL-8B-Instruct). These links establish candidate documentation, not compatibility with Einstein.
