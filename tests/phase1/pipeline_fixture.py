"""One executed synthetic base/adapted Phase 1A run shared by end-to-end tests."""

import copy
import os
from pathlib import Path
import shutil
import sys
import tempfile

from mmbu_phase1 import authority, canonical, phase1a, synthetic
from mmbu_phase1.store import RecordStore

REPO = Path(__file__).resolve().parents[2]
MANIFEST_SHA256 = "15daeff7a4f162a0c6adf1aae4d8d772bcbaa23351ab3120cd284a7ca8835cce"
SOURCE_STATE = "5" * 64
_CACHE = {}


def executed(cases=None):
    """Build and execute once per distinct case set; returns (world, execution, tempdir)."""
    key = tuple(c.example_id for c in cases) if cases else "all"
    if key not in _CACHE:
        temp = Path(os.path.realpath(tempfile.mkdtemp(prefix="phase1a-test-")))
        auth = {p: (REPO / p).read_bytes() for p in authority.AUTHORITY_PATHS}
        original = synthetic.CASES
        try:
            if cases is not None:
                synthetic.CASES = list(cases)
            world = phase1a.build_world(temp / "bundle", repository_root=str(REPO), run_root=str(temp / "run"),
                                        python_executable=os.path.realpath(sys.executable), authority_files=auth)
            execution = phase1a.execute(world, source_state_digest=SOURCE_STATE, contract_manifest_digest=MANIFEST_SHA256)
        finally:
            synthetic.CASES = original
        _CACHE[key] = (world, execution, temp)
    return _CACHE[key]


def cleanup():
    for _, _, temp in _CACHE.values():
        for directory, _, files in os.walk(temp):
            for name in files:
                os.chmod(os.path.join(directory, name), 0o644)
        shutil.rmtree(temp, ignore_errors=True)
    _CACHE.clear()


def clone_store(world):
    store = RecordStore()
    for record in world.store.records():
        store.add(copy.deepcopy(record))
    for digest in list(world.store._artifacts):
        store.add_artifact(world.store._artifacts[digest])
    return store


def reseal(record, **changes):
    updated = copy.deepcopy(record)
    updated.update(changes)
    return canonical.seal(updated)


def layers_of(world, execution, side):
    from mmbu_phase1 import layers

    output = world.store.get(execution.runs[side]["output_manifest_digest"], "execution_output_manifest")
    return output, layers.layers_by_example(output, world.read)
