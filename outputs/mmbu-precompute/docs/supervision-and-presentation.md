# Training-input boundaries prepared on CPU

The native CPU probes showed why the preprocessing boundary needs explicit checks. All three candidate processors silently clipped direct PIL uint16 image input into byte RGB. Direct uint16 arrays and already-normalized floats can also be scaled incorrectly. Qwen3.5's default thinking generation prefix did not align with a full assistant-answer sequence; its explicit non-thinking variant did. These are observed preprocessing/template behaviors, not model quality measurements.

## Image presentation

`presentation.present_image(input_path, output_path, window=None)` writes a **new** PNG and a returned provenance receipt. It first runs the existing native image inspector. RGB8 samples are preserved; grayscale8 is replicated into RGB channels. Other color, float, transparency, precision-reducing or orientation cases fail. Native uint16 grayscale requires a caller-specified integer `(black,white)` window with0≤black<white≤65535. Values are clipped to that window, mapped linearly to0–255 and rounded by the documented integer formula. The source bytes, original width/height and coordinate frame remain unchanged. The receipt gives parent/output hashes, recipe, window and clipped-pixel counts.

No default medical display window is supplied. A recipe that produces legal byte RGB is not thereby clinically appropriate, eligible for the competition, or a good adaptation strategy. Source-specific intensity review remains separate. No learned conversion, cropping, resizing or image-dependent task retry occurs. This helper prepares potential external data; it must not be inserted into an official evaluation harness without matching its confirmed input contract.

## Assistant loss labels

`supervision.assistant_labels(prompt_ids, full_ids, forbidden_target_ids=..., max_length=...)` requires the native prompt token sequence to be an exact prefix of the complete native assistant sequence, with at least one suffix token. Both encodings must use the same source image, processor settings and template options. It emits the ignore index−100 for the prompt and retains the full assistant suffix, including native ending tokens. It rejects prefix mismatch, over-budget examples and forbidden image/video/control IDs inside targets. It never searches for approximate role markers or silently truncates an answer.

The caller supplies forbidden IDs from the pinned tokenizer/processor; hardcoded offsets, prefix lengths or EOS IDs are not portable across these candidates. The Qwen3.5 default-prefix mismatch should fail this boundary. Explicitly disabling thinking is an engineering profile to test; it is not a claim that organizers require or permit that setting for final evaluation.

`pad_supervised_batch` right-pads input IDs with the declared padding ID, attention with zero and labels with−100. It validates per-example length and label consistency, requires nonempty supervision and refuses padding that exceeds the token cap. Its supervised-token count supports later loss-normalization checks. This is text-label bookkeeping, not a full multimodal trainer or vision-tensor collator. Native vision tensors/grids, optimizer behavior, accumulation, adaptation modules, actual memory and export still need their own integration evidence.
