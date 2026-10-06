# What now needs external evidence

The local CPU work establishes preparation tools and source-review material. It does not establish a trained contender or a leaderboard gain. Current base-model order remains Qwen2.5-VL-7B-Instruct first, Qwen3.5-9B as challenger, and Qwen3-VL-8B-Instruct as fallback; the final choice requires paired adaptation evidence on the same reviewed population.

| Next decision | Ready material | Missing evidence |
| --- | --- | --- |
| Restore Einstein and choose a viable pilot size | Read-only diagnostic script and IT handoff | Actual GPU model/count/VRAM, allocated visibility, driver/runtime behavior, quota and scheduler limits |
| Pin task/context output and scoring behavior | Conflict register, tested provisional serializers/parsers, organizer question draft | Organizer-selected final harness/schema, malformed-output handling, context policy, multi-label and localization grading |
| Establish permitted development and training data | Source registry, publisher metadata, article licenses, conversion receipts, grouped pending manifests | Intended-use/release compatibility, challenge overlap policy, access terms where relevant, suitable biomedical review |
| Choose the first adaptation recipe | Pinned processor artifacts, tested target masks, loss arithmetic, prospective experiment records | Native model loading/forward/backward, exact trainable module support, measured throughput/memory and BF16/FP16 export |
| Compare contenders and calibrate grades | Paired comparisons, source/task sensitivity and separate random/targeted calibration accounting | Actual untouched-base and adapted predictions, authoritative grading, blinded reviewer judgments |
| Select and confirm one checkpoint | Artifact hashes and confirmation lifecycle with independently retained anchors | Reviewed development evidence, an untouched eligible confirmation cohort and a genuine exported model |

Run the diagnostic from the Einstein environment where the GPU is expected to be visible; do not run it only on this Mac and infer remote health:

```sh
python3 tools/einstein_preflight.py --output einstein-preflight.json --torch-cuda
```

It reads local status and writes a new JSON report. A successful exit means the report was written, not that training is viable. Use the details in `docs/einstein-preflight.md` and `docs/einstein-handoff.md` when speaking with IT. No remote session, scheduler job or message has been initiated by this task.

The organizer draft is `docs/organizer-questions.md`; it has not been sent. Public sources were rechecked on October 4. The dataset revision remained unchanged and no open website-repository issues supplied the missing authoritative decisions. Sponsor subscriptions are challenge-work tools; they are not evidence of GPU access, API credits or permission to upload restricted data.

Biomedical review queues are `evidence/bbbc039-review-queue.csv` and `evidence/roco-review-queue.csv`. All real records remain pending. The ROCO review has 24 source-training examples across six modalities; BBBC039 has 100 source-training fields with derived count/box candidates. Review should address actual visual support, source semantics, figure lineage, text/overlay shortcuts, ambiguous objects and display policy. Tool-generated structural checks do not fill these answers.

Once those facts are available, start E00 with a small native load/forward/export smoke check, then E01 untouched bases, then matched E02 pilots. Preserve negative outcomes and failed predictions under the confirmed grading rule. Do not start a long run merely because the local software tests pass.
