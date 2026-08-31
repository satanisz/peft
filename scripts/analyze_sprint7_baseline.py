from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results" / "sprint7"
SEEDS = ("20260827", "20260828", "20260829")


def load_json(path: str | Path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def load_jsonl(path: str | Path):
    return [json.loads(line) for line in (ROOT / path).read_text(encoding="utf-8").splitlines() if line.strip()]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def is_ancestor(commit: str) -> bool:
    return subprocess.run(
        ["git", "merge-base", "--is-ancestor", commit, "HEAD"], cwd=ROOT
    ).returncode == 0


def root_causes(row: dict) -> list[str]:
    causes: list[str] = []
    expected = row.get("expected_status")
    predicted = row.get("predicted_status")
    if row.get("prompt_injection_followed"):
        causes.append("prompt_trust_boundary")
    if expected == "INSUFFICIENT_DATA" and predicted != expected:
        causes.append("missing_data_semantics")
    if expected == "NOT_APPLICABLE" and predicted != expected:
        causes.append("applicability_semantics")
    if not row.get("status_correct", True) and not causes:
        causes.append("decision_boundary")
    if row.get("severity_enforced", True) and not row.get("severity_correct", True):
        causes.append("severity_coupling")
    if not row.get("sources_valid", True):
        causes.append("source_integrity")
    if row.get("cited_untrusted_source"):
        causes.append("source_trust_boundary")
    if not row.get("human_review_correct", True):
        causes.append("escalation_policy")
    if row.get("deterministic_mismatch"):
        causes.append("deterministic_decision_boundary")
    return sorted(set(causes))


def remediation(cause: str) -> list[str]:
    mapping = {
        "prompt_trust_boundary": ["prompt", "source_guard", "human_review"],
        "source_trust_boundary": ["prompt", "source_guard"],
        "missing_data_semantics": ["data", "prompt", "human_review"],
        "applicability_semantics": ["data", "prompt"],
        "decision_boundary": ["data", "prompt"],
        "severity_coupling": ["contract", "data", "decision_guard"],
        "source_integrity": ["source_guard", "contract"],
        "escalation_policy": ["contract", "decision_guard", "human_review"],
        "deterministic_decision_boundary": ["decision_guard", "human_review"],
    }
    return mapping[cause]


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    closure_path = ROOT / "results/sprint6/protected_evidence_v1_closure.json"
    closure = json.loads(closure_path.read_text(encoding="utf-8"))

    bound_checks = []
    for relative, expected in closure["bound_sha256"].items():
        path = ROOT / relative
        actual = sha256(path) if path.exists() else None
        bound_checks.append(
            {
                "path": relative,
                "expected_sha256": expected,
                "actual_sha256": actual,
                "matches": actual == expected,
            }
        )

    adapter_manifests = [
        "results/sprint3/q1_adapter_manifest.json",
        "results/sprint4/q1_seed_20260828_adapter_manifest.json",
        "results/sprint4/q1_seed_20260829_adapter_manifest.json",
    ]
    adapter_checks = []
    for manifest_path in adapter_manifests:
        manifest = load_json(manifest_path)
        base = ROOT / manifest["adapter_path"]
        files = []
        for entry in manifest["files"]:
            local = base / entry["name"]
            actual = sha256(local) if local.exists() else None
            files.append(
                {
                    "name": entry["name"],
                    "expected_sha256": entry["sha256"],
                    "actual_sha256": actual,
                    "present": local.exists(),
                    "matches_if_present": actual is None or actual == entry["sha256"],
                }
            )
        adapter_checks.append(
            {
                "adapter_id": manifest["adapter_id"],
                "manifest": manifest_path,
                "adapter_path": manifest["adapter_path"],
                "files": files,
                "all_present": all(item["present"] for item in files),
                "all_present_hashes_match": all(item["present"] and item["matches_if_present"] for item in files),
                "no_present_hash_mismatch": all(item["matches_if_present"] for item in files),
            }
        )

    q1_configs = [
        "configs/qlora_q1_v1.json",
        "configs/qlora_q1_seed_20260828_v1.json",
        "configs/qlora_q1_seed_20260829_v1.json",
    ]
    q1_train_sources = []
    for config_path in q1_configs:
        config = load_json(config_path)
        q1_train_sources.append(
            {
                "config": config_path,
                "sources": [source["path"] for source in config["dataset"]["train_sources"]],
            }
        )

    forbidden_for_q2_train = [
        "data/generated/dataset_v1/validation.jsonl",
        "data/generated/dataset_v1/test.jsonl",
        "data/generated/dataset_v1/challenge.jsonl",
        "data/splits/boundary_validation.jsonl",
        "data/splits/boundary_test.jsonl",
        "data/diagnostic/diagnostic_set_v1.jsonl",
        "data/shadow/shadow_challenge_v1.jsonl",
    ]
    forbidden_for_v2_evidence = sorted(
        set(
            forbidden_for_q2_train
            + [
                "data/generated/dataset_v1/train.jsonl",
                "data/generated/dataset_v1/development.jsonl",
                "data/splits/boundary_train.jsonl",
                "data/splits/boundary_development.jsonl",
            ]
        )
    )

    datasets = {
        "original_test": load_jsonl("data/generated/dataset_v1/test.jsonl"),
        "boundary_test": load_jsonl("data/splits/boundary_test.jsonl"),
        "challenge": load_jsonl("data/generated/dataset_v1/challenge.jsonl"),
        "shadow_challenge": load_jsonl("data/shadow/shadow_challenge_v1.jsonl"),
    }
    case_meta = {}
    for split, rows in datasets.items():
        for row in rows:
            source_map = {source["source_id"]: source.get("content", "") for source in row["input"]["sources"]}
            untrusted = {
                source_id
                for source_id, content in source_map.items()
                if "INSTRUKCJA DLA MODELU" in content.upper() or "ZIGNORUJ" in content.upper()
            }
            case_meta[(split, row["case_id"])] = {
                "mutation_type": row.get("metadata", {}).get("mutation_type"),
                "reason_code": row.get("metadata", {}).get("reason_code"),
                "group_id": row.get("group_id"),
                "untrusted_source_ids": sorted(untrusted),
            }

    review_index = {}
    for split, review_path in (
        ("challenge", "results/sprint4/challenge_manual_review.json"),
        ("shadow_challenge", "results/sprint6/shadow_manual_response_review.json"),
    ):
        review = load_json(review_path)
        for row in review["responses"]:
            review_index[(split, row["seed"].removeprefix("seed_"), row["case_id"])] = row

    errors = []
    legacy_severity_observations = []
    response_count = 0
    split_seed_metrics = []
    for split in datasets:
        prefix = "results/sprint6" if split == "shadow_challenge" else "results/sprint4"
        for seed in SEEDS:
            metrics_path = f"{prefix}/seed_{seed}_{split}_metrics.json"
            raw_path = f"{prefix}/seed_{seed}_{split}.jsonl"
            metrics = load_json(metrics_path)
            raw = {row["case_id"]: row for row in load_jsonl(raw_path)}
            response_count += len(metrics["cases"])
            aggregate = metrics["aggregate"]
            split_seed_metrics.append(
                {
                    "split": split,
                    "seed": seed,
                    "count": aggregate["count"],
                    "status_correct_rate": aggregate["status_correct_rate"],
                    "macro_f1": aggregate["macro_f1"],
                    "severity_correct_rate": aggregate["severity_correct_rate"],
                    "sources_valid_rate": aggregate["sources_valid_rate"],
                    "schema_valid_rate": aggregate["schema_valid_rate"],
                }
            )
            for case in metrics["cases"]:
                raw_response = raw.get(case["case_id"], {})
                try:
                    parsed = json.loads(raw_response.get("response", "{}"))
                except json.JSONDecodeError:
                    parsed = {}
                cited = {item.get("source_id") for item in parsed.get("evidence", []) if isinstance(item, dict)}
                meta = case_meta[(split, case["case_id"])]
                review = review_index.get((split, seed, case["case_id"]), {})
                row = {
                    "split": split,
                    "seed": seed,
                    "case_id": case["case_id"],
                    "group_id": case.get("group_id") or meta["group_id"],
                    "control_type": case.get("control_type"),
                    "mutation_type": meta["mutation_type"],
                    "reason_code": meta["reason_code"],
                    "expected_status": case.get("expected_status"),
                    "predicted_status": case.get("predicted_status"),
                    "status_correct": case.get("status_correct", False),
                    "severity_correct": case.get("severity_correct", False),
                    "severity_enforced": split != "original_test",
                    "severity_mode": "legacy_report_only" if split == "original_test" else "enforced",
                    "sources_valid": case.get("sources_valid", False),
                    "schema_valid": case.get("schema_valid", False),
                    "human_review_correct": case.get("human_review_correct", False),
                    "prompt_injection_followed": review.get("prompt_injection_followed", False),
                    "false_assurance": review.get("false_assurance", False),
                    "critical_error": review.get("critical_error", False),
                    "manual_decision": review.get("decision"),
                    "failed_fields": review.get("failed_fields", []),
                    "cited_untrusted_source": bool(cited.intersection(meta["untrusted_source_ids"])),
                    "untrusted_source_ids": meta["untrusted_source_ids"],
                    "cited_source_ids": sorted(item for item in cited if item),
                    "deterministic_mismatch": False,
                }
                if not row["severity_enforced"] and not row["severity_correct"]:
                    legacy_severity_observations.append(
                        {
                            "split": split,
                            "seed": seed,
                            "case_id": case["case_id"],
                            "expected_status": row["expected_status"],
                            "predicted_status": row["predicted_status"],
                            "note": "Legacy dataset-v1 severity is report-only and predates status-policy-v1.",
                        }
                    )
                has_error = any(
                    [
                        not row["status_correct"],
                        row["severity_enforced"] and not row["severity_correct"],
                        not row["sources_valid"],
                        not row["schema_valid"],
                        not row["human_review_correct"],
                        row["prompt_injection_followed"],
                        row["critical_error"],
                        row["cited_untrusted_source"],
                    ]
                )
                if has_error:
                    row["root_causes"] = root_causes(row)
                    row["remediation_layers"] = sorted(
                        {layer for cause in row["root_causes"] for layer in remediation(cause)}
                    )
                    errors.append(row)

    cause_counts = Counter(cause for row in errors for cause in row["root_causes"])
    layer_counts = Counter(layer for row in errors for layer in row["remediation_layers"])
    by_case = defaultdict(lambda: {"seeds": [], "root_causes": set(), "remediation_layers": set()})
    for row in errors:
        entry = by_case[(row["split"], row["case_id"])]
        entry["seeds"].append(row["seed"])
        entry["root_causes"].update(row["root_causes"])
        entry["remediation_layers"].update(row["remediation_layers"])
    case_summary = [
        {
            "split": split,
            "case_id": case_id,
            "affected_seeds": sorted(entry["seeds"]),
            "affected_seed_count": len(set(entry["seeds"])),
            "root_causes": sorted(entry["root_causes"]),
            "remediation_layers": sorted(entry["remediation_layers"]),
        }
        for (split, case_id), entry in sorted(by_case.items())
    ]

    fc209 = load_json("results/sprint4_2c/report.json")
    deterministic_findings = [
        {
            "case_id": "FC-209",
            "seed": str(item["seed"]),
            "raw_status": item["fc209"]["deterministic_decision"]["actual_status"],
            "required_status": item["fc209"]["deterministic_decision"]["required_status"],
            "value": item["fc209"]["deterministic_decision"]["value"],
            "threshold": item["fc209"]["deterministic_decision"]["threshold"],
            "guard_decision": item["fc209"]["decision"],
            "silently_corrected": item["fc209"]["silently_corrected"],
            "root_cause": "deterministic_decision_boundary",
            "remediation_layers": ["decision_guard", "human_review"],
            "scope": "Historical diagnostic, not Evidence v1 and not independent Evidence v2.",
        }
        for item in fc209["seeds"]
    ]

    manifest = {
        "id": "S7-BASELINE-V1-MANIFEST",
        "version": "1.0.0",
        "head_commit": git("rev-parse", "HEAD"),
        "evidence_v1_status": closure["status"],
        "evidence_v1_future_use": closure["future_use"],
        "evidence_v1_rerun_allowed": False,
        "retuning_on_evidence_v1_allowed": False,
        "closure": {
            "path": "results/sprint6/protected_evidence_v1_closure.json",
            "sha256": sha256(closure_path),
            "bound_artifact_count": len(bound_checks),
            "all_bound_hashes_match": all(item["matches"] for item in bound_checks),
            "bound_checks": bound_checks,
            "evidence_run_commit_is_ancestor": is_ancestor(closure["evidence_run_commit"]),
            "final_review_commit_is_ancestor": is_ancestor(closure["final_review_commit"]),
        },
        "q1_adapters": adapter_checks,
        "q1_train_sources": q1_train_sources,
        "forbidden_for_q2_train": forbidden_for_q2_train,
        "forbidden_for_v2_evidence": forbidden_for_v2_evidence,
        "checks": {
            "closure_is_failed_frozen_read_only": closure["status"] == "CONSUMED_FROZEN_READ_ONLY_FAILED_THRESHOLDS",
            "all_closure_hashes_match": all(item["matches"] for item in bound_checks),
            "all_present_adapter_hashes_match": all(item["no_present_hash_mismatch"] for item in adapter_checks),
            "closure_commits_are_ancestors": is_ancestor(closure["evidence_run_commit"]) and is_ancestor(closure["final_review_commit"]),
            "q1_train_sources_exclude_protected_shadow": all(
                source not in forbidden_for_q2_train
                for config in q1_train_sources
                for source in config["sources"]
            ),
        },
        "decision": "S7_BASELINE_FROZEN",
    }

    exclusion_registry = {
        "id": "S7-DATA-EXCLUSION-REGISTRY-V1",
        "version": "1.0.0",
        "policy": {
            "evidence_v1": "DIAGNOSTIC_AND_REGRESSION_ONLY_NOT_INDEPENDENT_EVIDENCE",
            "q2_training": "No historical validation, test, challenge, diagnostic or shadow cases.",
            "evidence_v2": "No historical train, dev, validation, test, challenge, diagnostic or shadow cases.",
        },
        "forbidden_for_q2_train": [
            {"path": path, "sha256": sha256(ROOT / path)} for path in forbidden_for_q2_train
        ],
        "forbidden_for_v2_evidence": [
            {"path": path, "sha256": sha256(ROOT / path)} for path in forbidden_for_v2_evidence
        ],
    }

    analysis = {
        "id": "S7-EVIDENCE-V1-ERROR-ANALYSIS",
        "version": "1.0.0",
        "scope": "Diagnostic analysis only; Evidence v1 remains failed, frozen and read-only.",
        "analyzed_response_count": response_count,
        "error_response_count": len(errors),
        "unique_affected_case_count": len(case_summary),
        "legacy_severity_observation_count": len(legacy_severity_observations),
        "root_cause_counts": dict(sorted(cause_counts.items())),
        "remediation_layer_counts": dict(sorted(layer_counts.items())),
        "split_seed_metrics": split_seed_metrics,
        "case_summary": case_summary,
        "errors_per_case_and_seed": errors,
        "legacy_severity_observations": legacy_severity_observations,
        "diagnostic_control_findings": deterministic_findings,
    }

    manifest_path = RESULTS / "baseline_v1_manifest.json"
    analysis_path = RESULTS / "evidence_v1_error_analysis.json"
    exclusion_path = RESULTS / "data_exclusion_registry_v1.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    analysis_path.write_text(json.dumps(analysis, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    exclusion_path.write_text(json.dumps(exclusion_registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "manifest": str(manifest_path.relative_to(ROOT)),
                "analysis": str(analysis_path.relative_to(ROOT)),
                "exclusion_registry": str(exclusion_path.relative_to(ROOT)),
                "manifest_decision": manifest["decision"],
                "analyzed_responses": response_count,
                "error_responses": len(errors),
                "affected_cases": len(case_summary),
                "legacy_severity_observations": len(legacy_severity_observations),
                "root_causes": dict(cause_counts),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
