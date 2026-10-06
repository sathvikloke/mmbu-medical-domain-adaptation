# Independent diagnostics and acquisition review

Review date: 2026-10-04. Reviewer: `/root/processor_probe`, independently assigned after root authored these modules. This review made no implementation or test edits. It used Python 3.12.14 from `work/processor-probe/.venv/bin/python`, actual loopback HTTP requests and temporary synthetic archives. No remote dataset archive was fetched for the review.

Initial verdict: **changes requested for acquisition**. Final status: **both findings independently closed on the repaired version below**. No diagnostics defect was found within the checks below. This is a focused implementation review, not a full SENTINEL audit, source-permission review, or a model-result assessment. The initial findings and hashes are preserved; the repair closure applies to its separately identified version.

## Reviewed hashes

| File, relative to package root | SHA256 |
| --- | --- |
| `src/mmbu_prep/diagnostics.py` | `08f30d0c78a05fe3863d734e1ed3aced01e8cf2f912f4de57cdce349f4c80f57` |
| `src/mmbu_prep/acquisition.py` | `e908e5453fbaed933f3f02d3d2d22576b5bea37dc163b0b4e20cefc1b5b72f2f` |
| `tests/test_diagnostics.py` | `0d544fcc00416b783e102b99def6e31b11df22d172e76893bf0675c43f0c00bc` |
| `tests/test_acquisition.py` | `26f7c3ebcbf9e035b9a673ec8b9715f7fe14f20326e26d534115a6dc52b2a9fd` |
| `src/mmbu_prep/comparison.py` | `4c9c1d1cdb3d9c227c9c23baebbec9f78ebac3da0d3249ee80d6790f24500dd4` |
| `src/mmbu_prep/metrics.py` | `2af7036a70132102910c6a30cf68270a32db094b207723a7e1fa40677bdca799` |

## Findings

### DA-01 — P2: selected ZIP names can collide on the output filesystem

`acquisition.py:85–90` checks uniqueness of raw names and rejects some unsafe components, but `Path` normalizes names during `path.write_bytes` at line 112. The distinct names `a/b.txt` and `a//b.txt` both resolve to one output. The second payload silently overwrites the first, while the successful report lists both copied members and their distinct hashes. The same failure was reproduced with `a/./b.txt`, and with `A.txt`/`a.txt` on this host's case-insensitive filesystem. This makes the published data inconsistent with the acquisition manifest.

Minimal executed reproduction, run with `PYTHONPATH=outputs/mmbu-precompute/src`:

```python
import io, zipfile, tempfile
from pathlib import Path
from mmbu_prep.acquisition import copy_zip_members

payload = io.BytesIO()
with zipfile.ZipFile(payload, 'w') as archive:
    archive.writestr('a/b.txt', b'first')
    archive.writestr('a//b.txt', b'second')
payload.seek(0)
with tempfile.TemporaryDirectory() as folder:
    output = Path(folder) / 'new'
    report = copy_zip_members(payload, ['a/b.txt', 'a//b.txt'], output)
    print(len(report['members']))
    print([p.relative_to(output).as_posix() for p in output.rglob('*') if p.is_file()])
    print((output / 'a/b.txt').read_bytes())
```

Observed stdout (exit 0):

```text
2
['a/b.txt']
b'second'
```

The report claimed the first member SHA256 `a7937b64b8caa58f03721bb6bacf5c78cb235febe0e70b1b84cd99541461a08e` and second member SHA256 `16367aacb67a4a017c8da8ab95682ccb390863780f7114dda0a0e0c55644c7c4`, although only the latter bytes remained. No inference about an actual source archive is made.

Requested root repair: reject noncanonical selected paths and filesystem destination collisions before publication; ensure a selected file cannot overwrite an earlier selected file during extraction. Add regression coverage for repeated separators, dot components and case-insensitive collisions. A rejection must leave no published directory.

### DA-02 — P3: the body-byte ceiling excludes the oversized-response detection byte

`acquisition.py:46` budgets `count`, but line 58 reads `count+1`. With no Content-Length header and one extra response byte, the implementation consumes more than `max_transfer_bytes` before raising. The overshoot is one byte in this repro, not an unbounded download. It contradicts the strict named cap and should be accounted for explicitly.

Minimal executed real-HTTP reproduction:

```python
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import threading
from mmbu_prep.acquisition import HTTPRangeReader

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(206)
        self.send_header('Content-Range', 'bytes 0-3/4')
        self.end_headers()  # Deliberately no Content-Length.
        self.wfile.write(b'abcde')
    def log_message(self, *args):
        pass

server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
thread = threading.Thread(target=server.serve_forever, daemon=True)
thread.start()
try:
    with HTTPRangeReader(f'http://127.0.0.1:{server.server_port}/fixture',
                         4, block_size=4, max_transfer_bytes=4) as reader:
        try:
            reader.read(4)
        except ValueError as error:
            print(type(error).__name__, str(error))
        print('limit', reader.max_transfer_bytes,
              'counted_body_bytes', reader.transferred_bytes)
finally:
    server.shutdown()
    server.server_close()
    thread.join()
```

Observed stdout (exit 0):

```text
ValueError Truncated or oversized range response
limit 4 counted_body_bytes 5
```

Requested root repair: include any detection byte in the available body-byte budget or reject responses whose framing cannot be checked within that budget. Preserve exact range/size and oversized-response rejection. Add a no-Content-Length loopback regression test at the exact byte ceiling.

## Executed checks without a defect

The supplied tests were run independently with:

```sh
PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH=outputs/mmbu-precompute/src:outputs/mmbu-precompute/tests \
work/processor-probe/.venv/bin/python -m unittest test_diagnostics test_acquisition -v
```

Result: **12 tests passed**, exit 0, 5.220 seconds. These tests did not cover either finding above. Existing coverage includes exact-range and status rejection, truncated body rejection, seek/cache/EOF/budget behavior, selected-only extraction, existing output refusal, unsafe/missing/duplicate/oversized selections, population alignment and separated calibration sampling frames.

Additional independently executed checks (all assertions passed, exit 0):

- Built a 16-row fixture with all four task groups, two sources per task with unequal 1:3 row counts, one counting row grouped into global classification, two candidates with reversed/shuffled row order, and distinct baseline/adapted/context grades. For natural, balanced and all four stress mixtures, independently computed every per-record weight using `fractions.Fraction`: natural `1/16`, otherwise task mass divided by two sources and then by within-source/task row count. Task masses were `1/4` for balanced and `2/5` or `1/5` for stress. All reported weights and both candidates' independently computed `S=(4T/5+C/5)*(T-T_base)` matched to below `1e-15`. Every scenario retained all sorted record IDs and input objects remained unchanged.
- Changed task, source, group and context-field coverage independently for one candidate; every mismatch raised before subgroup reporting. Counting stayed a separate by-task diagnostic. The result reported no winner. The existing missing-task test verified that no complete balanced proxy was fabricated from partial coverage.
- A random calibration set with one each of TP/FP/TN/FN retained `n=4` and agreement 0.5; a separate targeted false-negative case retained `n=1` and agreement 0.0. No pooled statistic was generated. Supplied human grades are explicitly labeled as uncertified reference judgments, and sampling labels are not represented as verified randomness.
- Corrupted the central-directory CRC of a selected stored ZIP member by toggling the byte at `PK\x01\x02 + 16`, then read it through the real loopback range server. `BadZipFile: Bad CRC-32 for file 'safe/a.txt'` was raised; no published output or staging directory remained. The tiny fixture caused 225 body bytes to be read. Selected-member CRC checking did not claim whole-archive authentication.
- Read one exact 4-byte range with ETag `"first"`; the next correct range carried ETag `"changed"`. The reader rejected it with `Remote archive validator changed during acquisition` before adding its body bytes; the recorded byte count stayed 4.
- Closed a reader before issuing `read(1)` and `seek(0)`; both raised `ValueError`. No model, archive-wide checksum or source-authenticity claim was introduced. Acquisition remains an explicitly imported networking module separate from the offline prep CLI.

The root was notified of both findings and asked to repair them. No claims about concurrent publication races, arbitrary archive formats, biomedical labels, model ranking or packages outside this implementation were added to this review.

## Independent repair closure

Root repaired DA-01 by requiring canonical `PurePosixPath` spelling and rejecting NFC/casefold destination collisions. The reviewer reran all three original distinct-name fixtures (`a//b.txt`, `a/./b.txt`, and `A.txt` versus `a.txt`); each now raised before publishing an output directory.

Root's first DA-02 repair required exact Content-Length. The reviewer found that this alone did not close the cap: an HTTP/1.1 response with `Content-Length: 4` and `Transfer-Encoding: chunked`, framing five bytes as `5\r\nabcde\r\n0\r\n\r\n`, still consumed five body bytes because urllib prioritizes chunked framing. Root reproduced that counterexample in an additional regression, then rejected any Transfer-Encoding and limited the body read to the declared count.

The reviewer independently reran both real-server framing reproductions on the final version. Missing-length responses now raise `Exact bounded Content-Length is required`; contradictory chunked responses raise `Chunked or ambiguous transfer framing is unsupported`. Both reject before body consumption, with `transferred_bytes == 0` at the four-byte ceiling. The eight updated acquisition tests independently passed in 7.567 seconds, exit 0. Original selected-member, range, budget and no-whole-archive-checksum checks remained passing.

Closed findings on these exact hashes:

| Repaired artifact | SHA256 |
| --- | --- |
| `src/mmbu_prep/acquisition.py` | `9c196f252e83bafe07fdc0fe6bf02a8846c8fd4982bb4737f6fd059034d64a8c` |
| `tests/test_acquisition.py` | `baea089a968cb14f283d6d126d1ac7a690aef4145e426be956c39a5b0ee95ea8` |

No further actionable acquisition defect was found in this focused replay. This closure authorizes no source use and verifies no whole archive checksum.
