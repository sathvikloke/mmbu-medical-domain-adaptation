# Independent processor-probe review

Verdict: the final script and evidence support the documented synthetic CPU preprocessing claims. One reproducible artifact-closure defect was found, repaired by the author, and independently rechecked. No unresolved defect was found in the reviewed claims about input selection, native assistant prefixes, dtype hazards or retained artifact hashes. This is a focused software/evidence review by a different agent from the probe author, not an independent scientific validation or a model/GPU readiness approval.

Reviewed final script: `tools/processor_probe.py`, SHA-256 `981e04e4d0be549bc68fb30868d8a68ad0f2bf55c8df2edeef6ed2b25e6d5fd8`. The author’s earlier reviewed script had SHA-256 `bc261487f4ab843693f523250cac8a9dc504bec47bef92a4efed80f282687a9f`.

## Fresh execution evidence

The reviewer used the existing `work/processor-probe/.venv/bin/python` and local artifact snapshots from the project root. No installation, download or model execution was performed. For the full replay, `socket.socket.connect`, `socket.create_connection` and `urllib.request.urlopen` were replaced with functions that raise an error before the script was executed with `runpy`. This checks the ordinary Python network paths used by this script; it is not a kernel network sandbox.

```python
import runpy, socket, sys, urllib.request
def deny(*args, **kwargs):
    raise RuntimeError("independent replay forbids network")
socket.socket.connect = deny
socket.create_connection = deny
urllib.request.urlopen = deny
sys.argv = ["outputs/mmbu-precompute/tools/processor_probe.py", "--offline",
            "--artifacts", "work/processor-probe/artifacts", "--output", "NEW_REPLAY_FILE.json"]
runpy.run_path(sys.argv[0], run_name="__main__")
```

Both the original and repaired scripts replayed all three candidates successfully. The repaired replay exited **0** and matched the final `evidence/processor-probe.json` recursively at every field except `run_at_utc`. This includes all rendered prompts, token IDs, tensor hashes/shapes/dtypes/statistics, warnings, native16 cases and rejection details. The replay retained the same three expected ambiguous-channel warnings for the extreme-aspect fixture. Final independent replay file SHA-256: `774216392e9c8331021ad0d2273b2c40eb7f0fc4e4a422d0592aa74f74f4ca73`.

Additional commands were run separately and their process exit codes preserved:

| Execution | Result |
| --- | --- |
| Isolated venv, native script, `--offline`, existing cache, connection-denying wrapper | Exit 0; final report identical except time |
| `work/processor-probe/.venv/bin/python work/processor-probe/test_processor_probe.py` | Exit 0; 8 artifact guard tests passed |
| Original bundled Python, native script, `--offline`, existing cache | Expected exit 2; all 3 candidates explicitly `unavailable` because dependencies are absent |
| Independent SHA-256 and manifest/file-size recomputation | Exit 0; all examined hashes and sizes matched |
| Independent token-prefix and PIL uint16 conversion check | Exit 0; observations below reproduced |

The temporary reviewer outputs and exact command arrays are under `/private/tmp/mmbu-processor-independent-_t_v3elg/` (`summary.json`, `final-summary.json`, `hash-checks.json`, `environment-prefix-dtype.json`, `auxiliary-executions.json`, replay JSON and logs). These temporary files are supplemental; this report preserves the findings, tested versions, exit codes and final script anchor without requiring their retention.

## Found defect and verified repair

**P2, closed: unmanifested optional processor files could be loaded without a hash check.** In the original `artifacts()` implementation, unexpected local names were checked against every filename that could be downloaded (`FILES`) rather than the subset whose contents had been verified from the manifest. A temporary synthetic snapshot containing the required files and a template passed offline validation after an extra `special_tokens_map.json` was added without any manifest entry. The reviewer directly reproduced acceptance with contents `{"eos_token":"UNRECEIPTED_TOKEN"}`. Such a file is an accepted processor input and could change downstream tokenization despite being absent from the receipt.

The author changed directory closure to the verified `present` filenames and added `test_offline_refuses_unmanifested_optional_artifact`. The reviewer independently repeated the same temporary fixture against final script `981e04...`; it raised:

```text
ValueError: unexpected files in processor-only directory: ['special_tokens_map.json']
```

The repaired full native replay still matched all prior substantive observations. The fixed-file download allowlist contains only configuration, tokenizer, vocabulary and template names. Weight and index filenames are excluded. The per-file and per-model download bounds are explicit; the helper tests exercise oversize rejection before writing. Offline validation verifies the chosen model/revision, expected hashes/sizes, required members and local file closure before `AutoProcessor` is loaded.

## Claim checks

**Environment isolation.** The executed interpreter reports `sys.prefix` at `work/processor-probe/.venv`, with its bundled Python runtime as `sys.base_prefix`. `pyvenv.cfg` has `include-system-site-packages = false`; `site.ENABLE_USER_SITE` is false. All **36** versions in `processor-requirements.txt` matched installed distribution metadata. The native replay uses CPU processing explicitly. Static inspection found `AutoProcessor.from_pretrained(..., local_files_only=True, trust_remote_code=False)` and no model constructor, forward pass, model weight retrieval or GPU operation.

**Evidence integrity.** The reviewer independently recomputed **23** downloaded artifact file sizes and SHA-256 values, totaling **45,900,851 bytes**, and compared each local manifest to its copy in the report. Every value matched. The **9** installed Transformers source-file hashes in `processor-upstream-sources.json` matched their local installed sources. The final script and registry digests matched the final probe report; the script digest and all three log digests matched `processor-verification.json`. These checks establish consistency of the local evidence, not independent authentication of a model publisher or package distribution.

**Task/context input selection.** The native script calls the package's existing input selectors and constructs fresh messages from the resulting allowlisted fields. Source inspection and replay confirm that the poison reference answer/options/context/history/messages/previous-prediction values are absent. Changing those fields preserves task token IDs; additionally changing the question preserves context token IDs. This supports the documented selector/template claim. It does not test model conversation caches or prove isolation between actual inference requests, and the documentation says so.

**Assistant target boundaries.** The reviewer recomputed prefix equality directly from the saved raw multimodal token arrays, independently of the reported Boolean or boundary:

| Model / variant | Prompt tokens | Full tokens | Prefix | Reported boundary |
| --- | ---: | ---: | --- | ---: |
| Qwen2.5-VL, default | 42 | 51 | Exact | 42 |
| Qwen3.5, default | 104 | 115 | Mismatch | `null` |
| Qwen3.5, `enable_thinking=False` | 106 | 115 | Exact | 106 |
| Qwen3-VL, default | 102 | 111 | Exact | 102 |

Every exact suffix contained the recorded EOS token. The Qwen3.5 default mismatch is retained and no label boundary is invented. The replay also reproduces equality of integrated native chat encoding and separate render/encode tensors. The report does not claim a production collator, valid arbitrary-example loss mask or a training-loss check.

**Dtype hazards.** In a separate seven-value PIL check, native uint16 values `[0, 1, 255, 256, 1024, 32768, 65535]` converted to RGB red-channel values `[0, 1, 255, 255, 255, 255, 255]`. The full replay reproduces the processed native16/PIL-RGB equality. NumPy uint16 RGB maxima of **981.7819213867188** for Qwen2.5 and **513.0** for the newer candidates match the saved evidence; two-dimensional uint16 arrays are rejected. The normalized-float rescaling observations also replay identically. Accepted input is correctly distinguished from appropriate biomedical preprocessing.

## Scope of the verdict

The overall probe's success status represents the declared RGB, chat-selector, integrated-encoding and expected aspect-rejection checks. It intentionally does not mean that default Qwen3.5 assistant masking is valid or that native16 input is safe. Those failures/hazards are explicit, reproducible observations in the saved report and documentation. The probe remains synthetic preprocessing evidence only: no real source image suitability, label correctness, model quality, GPU memory fit, training, export, official-protocol equivalence or untouched confirmation claim is established.
