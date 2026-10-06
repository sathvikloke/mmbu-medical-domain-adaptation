# Independent supervision and presentation review

October 4, 2026. Read-only review by the source-expansion agent, independent of the implementation owner. Production code was not changed by this reviewer. Scope: `supervision.py`, `presentation.py`, their direct tests, the image-inspection dependency, and cached native processor integration. This is an engineering review, not a research-performance or complete SENTINEL audit.

**Final scoped verdict: PASS after SUP-01 was fixed by the implementation owner and independently retested.** No open defect remains within the checks described below. The intended `assistant_labels` → `pad_supervised_batch` composition passes with the tested native processors.

## SUP-01: zero effective causal targets — closed

`pad_supervised_batch` checks for any unmasked label and counts every unmasked position. It accepts `input_ids=[7,9], labels=[7,-100]` and reports `supervised_tokens=1`. In standard causal next-token training the targets shift to `labels[1:]`, so this example has zero effective targets. The helper's claim that each example retains supervised targets is therefore not enforced for all accepted inputs. A one-token unmasked example has the same issue.

Evidence: [executed counterexample](supervision-presentation-padding-counterexample.json). The owner fixed this by requiring the first label to be `-100` and at least one unmasked label in `labels[1:]`. Independent regression probes now reject the original counterexample, an unmasked one-token example, an example with the first and later positions unmasked, and a fully masked one-token example. The checks are now in `supervision.py` lines 43–44. This is a public-helper guard gap, not an observed failure of the tested composition: `assistant_labels` requires a nonempty prompt and masks it, so its outputs have a masked first position.

## Executed checks

The final direct unit suites passed using bundled Python 3.12.14 with Pillow 12.3.0: [six supervision tests](supervision-presentation-unit-supervision.txt) and [three presentation tests](supervision-presentation-unit-presentation.txt). Exit codes were zero.

The independent driver is project-root `work/source-expansion/review_supervision_presentation.py`. It imports the production helpers without editing them; original synthetic fixtures are created in temporary directories. The [adversarial report](supervision-presentation-adversarial.json) records script and production hashes. Exit code was zero after correcting the reviewer's path fixture.

- **Supervision:** 35 rejection probes covered Boolean/float/negative IDs, empty sequences, malformed forbidden-ID collections and budgets, missing targets, shorter full sequences, non-prefix repeated-marker cases, forbidden suffix IDs, truncation and padding rounding past the cap. Target token zero and EOS equal to the pad ID were preserved. Input lists remained unchanged. Unequal-length batches retained exact labels and attention masks.
- **Numeric image mapping:** every value from 0 through 65,535 was tested in both little- and big-endian uint16 TIFFs under six explicit windows, for **786,432 pixel comparisons**. The independent expected value used the doubled-integer formula `floor((2 * (v-black) * 255 + span) / (2 * span))` inside the window and clipped endpoints. Output RGB values, low/high clip counts, dimensions, identity coordinates, source-byte preservation and recorded hashes all matched. Windows included the full range, nonzero black, spans 1, 2 and 3, and a large asymmetric span.
- **Images and paths:** 17 rejection fixtures covered float/NaN, signed integer, opaque RGBA, LA, palette, CMYK, nonidentity EXIF orientations 2–8, RGB and grayscale transparency, animation and handcrafted 16-bit RGB PNG precision loss. Ten invalid/missing windows and two symlink cases were checked. Failed conversions published no output. Asymmetric RGB and grayscale test patterns preserved every source pixel's position. Existing outputs and source-path overwrite attempts were rejected.

The initial path probe incorrectly expected rejection of an input symlink whose target remained inside the declared image root. That is permitted behavior under `inspect_images`. The fixture was corrected to escape that root, then rejected as intended. The initial exit-1 result is preserved in [the initial report](supervision-presentation-adversarial-initial.json); it is not a production defect. No production changes were needed for the correction.

## Native processor integration

The [native report](supervision-presentation-native.json) is a fresh CPU-only execution in `work/processor-probe/.venv`, rather than an inference from prior saved token IDs. It used the three pinned local snapshots from `model-registry.json`, verified each cached file against its artifact manifest, and loaded only `AutoProcessor` with `local_files_only=True, trust_remote_code=False`. Offline environment flags were set, and socket connection methods were replaced with a rejecting guard; **zero network connection attempts occurred**. No weights, model instance, forward pass or GPU operation was used. Exit code was zero; [stderr](supervision-presentation-native.stderr) was empty.

Each variant encoded two independently rendered prompt/full-conversation pairs using the same synthetic RGB image and native processor settings. Image sizes were 64×64 and 301×199; answers differed in length and included accented text, a Unicode arrow and bracketed coordinates. Boundaries were derived separately from actual token sequences. Native special-token definitions supplied the image/video/vision/role-start forbidden IDs. No token boundary or special ID was hardcoded.

| Candidate and native template setting | Result for both cases | Supervised suffix lengths |
| --- | --- | --- |
| Qwen2.5-VL defaults | Exact prefix accepted | 8, 25 |
| Qwen3-VL defaults | Exact prefix accepted | 8, 25 |
| Qwen3.5 defaults | Prefix mismatch rejected | No boundary assigned |
| Qwen3.5 `enable_thinking=False` | Exact prefix accepted | 8, 25 |

Every accepted result masked all prompt/image positions, supervised the complete native suffix including EOS and newline, rejected a budget one token too small, and rejected an appended native image token in the target. Padded batches preserved all original IDs/labels, ignored padding, retained EOS even when equal to the pad token, and reported 33 supervised positions across the two valid examples. All returned native tensors were on CPU.

## Limits

The helper must still receive prompt/full encodings generated with identical images and processor settings, as its docstring requires; token-prefix equality alone cannot certify identical vision tensors. Caller-provided forbidden IDs must come from the actual selected processor. The current padding helper only handles text IDs/masks; native vision tensors/grids need a model-specific collator. No shifted model loss or training gradient was computed.

The presentation probe establishes integer mapping and pixel-frame preservation for the checked encodings. It does not choose or medically validate a window, validate annotations, establish color-managed display equivalence, or approve source/model use. Source inspection warnings such as ICC-profile handling remain separate from sample-value correctness.
