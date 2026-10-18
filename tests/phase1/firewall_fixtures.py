"""Synthetic-canary lineage and decision-firewall fixtures (no real or official content)."""

import copy

from mmbu_phase1 import canonical
from mmbu_phase1.store import RecordStore

P = "mmbu.phase1."
T0 = "2026-10-16T10:00:00Z"   # plan frozen
T1 = "2026-10-16T10:05:00Z"   # planned opening not_before
T2 = "2026-10-16T10:10:00Z"   # sandbox start
T3 = "2026-10-16T10:20:00Z"   # sandbox end
T4 = "2026-10-16T10:30:00Z"   # attestations
EXCLUDED_CLASSES = sorted([
    "example_id", "image", "question", "answer", "label", "annotation", "benchmark_outcome",
    "example_statistic", "error_analysis", "example_derived_recommendation",
])
FORBIDDEN = ["mmbu_derivative", "mmbu_official", "unknown"]


def d(label):
    return canonical.raw_digest(("synthetic-canary:" + label).encode())


def lineage(artifact, origin, purposes, parents=(), created_at=T0, reviewed=False):
    record = {
        "schema_id": P + "lineage_receipt",
        "schema_version": 1,
        "lineage_id": "lineage-" + artifact[:12],
        "artifact_digest": artifact,
        "origin_class": origin,
        "allowed_purposes": sorted(purposes),
        "parents": sorted(({"parent_digest": p, "edge_role": r} for p, r in parents),
                          key=lambda e: (e["parent_digest"].encode(), e["edge_role"].encode())),
        "source_version": d("version") if reviewed else None,
        "rights_receipt_digest": d("rights") if reviewed else None,
        "grouping_receipt_digest": d("grouping") if reviewed else None,
        "qa_receipt_digest": d("qa") if reviewed else None,
        "created_at": created_at,
    }
    return canonical.seal(record)


def extraction(source, output, reviewers=("reviewer-a", "reviewer-b"), dispositions=("approved", "approved"),
               classes=None):
    return canonical.seal({
        "schema_id": P + "sanitized_rule_extraction",
        "schema_version": 1,
        "extraction_id": "extraction-" + output[:12],
        "source_digest": source,
        "source_origin_class": "mmbu_official",
        "source_span_registry_digest": d("span-registry"),
        "included_spans": [
            {"source_locator": "page-03", "start": 0, "end": 120, "extracted_bytes_digest": d("span-1")},
            {"source_locator": "page-03", "start": 200, "end": 260, "extracted_bytes_digest": d("span-2")},
            {"source_locator": "page-10", "start": 10, "end": 90, "extracted_bytes_digest": d("span-3")},
        ],
        "excluded_content_classes": list(EXCLUDED_CLASSES if classes is None else classes),
        "extraction_function_digest": d("extract-fn"),
        "output_digest": output,
        "reviewer_attestations": [
            {"reviewer_id": rid, "reviewed_output_digest": output, "disposition": disp,
             "reviewed_at": T0, "attestation_digest": d("att-" + rid)}
            for rid, disp in zip(reviewers, dispositions)
        ],
        "created_at": T0,
    })


class World:
    """One valid promotable decision plus its synthetic ancestry."""

    def __init__(self):
        self.official = d("official-rules-pdf")
        self.summary = d("official-rule-summary")
        self.data = d("external-reviewed-data")
        self.synthetic = d("synthetic-engineering-input")
        self.derivative = d("official-derivative")
        self.unknown = d("unknown-origin")
        self.rationale = d("rationale-bytes")
        self.lineages = {
            self.official: lineage(self.official, "mmbu_official", ["official_audit"]),
            self.summary: lineage(self.summary, "official_rule_summary", [], [(self.official, "governance")]),
            self.data: lineage(self.data, "external_reviewed", ["engineering", "train"], reviewed=True),
            self.synthetic: lineage(self.synthetic, "synthetic_engineering", ["engineering"]),
            self.derivative: lineage(self.derivative, "mmbu_derivative", ["train"], [(self.official, "data")]),
            self.unknown: lineage(self.unknown, "unknown", ["train"]),
        }
        self.extractions = [extraction(self.official, self.summary)]
        self.plan = None
        self.payload = None
        self.output_lineage = None
        self.receipt = None
        self.build()

    def build(self, inputs=None, purpose="train", kind="experiment_priority"):
        inputs = sorted(inputs or [self.data, self.summary])
        self.plan = canonical.seal({
            "schema_id": P + "decision_plan",
            "schema_version": 1,
            "plan_id": "plan-1",
            "decision_kind": kind,
            "purpose": purpose,
            "scope": "synthetic-firewall-scope",
            "subject_ids": ["cand-a", "cand-b"],
            "allowed_input_digests": inputs,
            "forbidden_origin_classes": list(FORBIDDEN),
            "forbidden_root_digests": [],
            "decision_function_digest": d("decision-fn"),
            "command_digest": d("command"),
            "source_state_digest": d("source-state"),
            "sandbox_policy_digest": d("sandbox-policy"),
            "planned_opening_event": {
                "opening_kind": "protected_access",
                "trigger": "decision-runner-start",
                "not_before": T1,
                "operator_role": "decision_operator",
                "protected_artifact_digests": inputs,
                "command_template_digest": d("command-template"),
            },
            "operator_id": "operator-1",
            "created_at": T0,
        })
        self.payload = canonical.seal({
            "schema_id": P + "decision_payload",
            "schema_version": 1,
            "decision_id": "decision-1",
            "plan_digest": self.plan["record_digest"],
            "decision_kind": kind,
            "purpose": purpose,
            "subject_ids": ["cand-a", "cand-b"],
            "selected_subject_ids": ["cand-a"],
            "dispositions": [
                {"subject_id": "cand-a", "status": "selected", "reason_code": "rule_satisfied"},
                {"subject_id": "cand-b", "status": "not_selected", "reason_code": "rule_not_satisfied"},
            ],
            "claim_digests": [inputs[0]],
            "rationale_digest": self.rationale,
            "created_at": "2026-10-16T10:15:00Z",
        })
        parents = [(digest, "governance" if digest == self.summary else "decision") for digest in inputs]
        synthetic_only = inputs == [self.synthetic]
        self.output_lineage = lineage(self.payload["record_digest"],
                                      "synthetic_engineering" if synthetic_only else "external_reviewed",
                                      [purpose], parents, created_at="2026-10-16T10:15:00Z",
                                      reviewed=not synthetic_only)
        self.receipt = canonical.seal({
            "schema_id": P + "decision_execution_receipt",
            "schema_version": 1,
            "receipt_id": "receipt-1",
            "plan_digest": self.plan["record_digest"],
            "decision_payload_digest": self.payload["record_digest"],
            "rationale_digest": self.rationale,
            "output_lineage_receipt_digest": self.output_lineage["record_digest"],
            "source_state_digest": self.plan["source_state_digest"],
            "command_digest": self.plan["command_digest"],
            "sandbox_policy_digest": self.plan["sandbox_policy_digest"],
            "mounted_input_digests": list(inputs),
            "observed_content_read_digests": list(inputs),
            "emitted_output_digests": sorted([self.payload["record_digest"], self.rationale]),
            "attempted_denied_reads": [],
            "network_events": [],
            "operator_attestation": {
                "operator_id": "operator-1",
                "no_undeclared_influence": True,
                "no_protected_memory_used": True,
                "attested_at": T4,
                "attestation_digest": d("operator-attestation"),
            },
            "independent_review": {
                "reviewer_id": "reviewer-9",
                "reviewed_plan_digest": self.plan["record_digest"],
                "reviewed_payload_digest": self.payload["record_digest"],
                "reviewed_rationale_digest": self.rationale,
                "disposition": "approved",
                "reviewed_at": T4,
                "attestation_digest": d("independent-review"),
            },
            "started_at": T2,
            "ended_at": T3,
            "exit_code": 0,
            "terminal_status": "succeeded",
        })
        return self

    def store(self):
        records = [*self.lineages.values(), *self.extractions, self.plan, self.payload, self.output_lineage, self.receipt]
        store = RecordStore(records)
        store.add_artifact(b"synthetic rationale text")
        return store

    def relink(self):
        """Recompute payload/lineage/receipt digests after editing the plan or payload."""
        self.plan = canonical.seal(self.plan)
        payload = copy.deepcopy(self.payload)
        payload["plan_digest"] = self.plan["record_digest"]
        self.payload = canonical.seal(payload)
        out = copy.deepcopy(self.output_lineage)
        out["artifact_digest"] = self.payload["record_digest"]
        out["lineage_id"] = "lineage-" + self.payload["record_digest"][:12]
        self.output_lineage = canonical.seal(out)
        receipt = copy.deepcopy(self.receipt)
        receipt["plan_digest"] = self.plan["record_digest"]
        receipt["decision_payload_digest"] = self.payload["record_digest"]
        receipt["output_lineage_receipt_digest"] = self.output_lineage["record_digest"]
        receipt["emitted_output_digests"] = sorted([self.payload["record_digest"], receipt["rationale_digest"]])
        receipt["independent_review"]["reviewed_plan_digest"] = self.plan["record_digest"]
        receipt["independent_review"]["reviewed_payload_digest"] = self.payload["record_digest"]
        self.receipt = canonical.seal(receipt)
        return self
