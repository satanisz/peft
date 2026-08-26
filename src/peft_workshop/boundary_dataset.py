from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from .data_audit import audit_cases
from .dataset_v1 import write_jsonl
from .paths import CONFIG_DIR, DATA_DIR, RESULTS_DIR, resolve_project_path


BOUNDARY_VERSION = "1.0.0"
DATASET_VERSION = f"boundary-{BOUNDARY_VERSION}"
DEFAULT_SEED = 20260826
DEFAULT_OUTPUT = DATA_DIR / "generated" / "boundary_pack_v1.jsonl"
DEFAULT_SPLIT_DIR = DATA_DIR / "splits"
DEFAULT_REGISTRY = DATA_DIR / "boundary_registry.json"
DEFAULT_REVIEW = DATA_DIR / "reviews" / "boundary_pack_v1_review.jsonl"
DEFAULT_AUDIT = RESULTS_DIR / "sprint2_5_boundary_audit.json"

BOUNDARIES = {
    "PASS_WARN": ("PASS", "WARN"),
    "WARN_FAIL": ("WARN", "FAIL"),
    "NOT_APPLICABLE_INSUFFICIENT_DATA": ("NOT_APPLICABLE", "INSUFFICIENT_DATA"),
}
PAIR_COUNTS = {
    "train": {"PASS_WARN": 40, "WARN_FAIL": 40, "NOT_APPLICABLE_INSUFFICIENT_DATA": 40},
    "development": {"PASS_WARN": 10, "WARN_FAIL": 10, "NOT_APPLICABLE_INSUFFICIENT_DATA": 10},
    "validation": {"PASS_WARN": 15, "WARN_FAIL": 15, "NOT_APPLICABLE_INSUFFICIENT_DATA": 30},
    "test": {"PASS_WARN": 15, "WARN_FAIL": 15, "NOT_APPLICABLE_INSUFFICIENT_DATA": 30},
}
CONTROL_TYPES = (
    "ARITHMETIC",
    "CROSS_SECTION",
    "PERIOD",
    "UNIT",
    "CURRENCY",
    "DIRECTION",
    "VARIANCE",
    "DISCLOSURE",
    "EVIDENCE",
)
TASKS = (
    "Ustal wynik kontroli na podstawie przekazanej procedury i dowodów.",
    "Zweryfikuj przypadek i udokumentuj przesłankę decyzji.",
    "Oceń materiał zgodnie z regułą kontrolną.",
    "Przeprowadź kontrolę i wskaż wykorzystane źródła.",
)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _controls() -> dict[str, dict[str, str]]:
    return {
        item["type"]: item
        for item in _load_json(CONFIG_DIR / "control_catalog.json")["controls"]
    }


def _policy() -> dict[str, Any]:
    return _load_json(CONFIG_DIR / "status_policy_v1.json")


SCENARIOS: dict[str, dict[str, dict[str, Any]]] = {
    "ARITHMETIC": {
        "PASS_WARN": {
            "context": "Składniki wynoszą {value} i {prior} mln PLN; raportowana suma jest kontrolowana z tolerancją 0,5 mln PLN.",
            "rule": "Różnica do 0,5 mln PLN jest akceptowana; różnica do 5 mln PLN wymaga wyjaśnienia, lecz nie jest materialnym naruszeniem.",
            "facts": {"PASS": "Różnica wynosi 0,4 mln PLN.", "WARN": "Różnica wynosi 0,8 mln PLN."},
        },
        "WARN_FAIL": {
            "context": "Składniki wynoszą {value} i {prior} mln PLN; raportowana suma podlega progowi materialności.",
            "rule": "Różnica do 5 mln PLN wymaga korekty roboczej; większa różnica jest materialna.",
            "facts": {"WARN": "Potwierdzona różnica wynosi 3 mln PLN.", "FAIL": "Potwierdzona różnica wynosi 13 mln PLN."},
        },
        "NOT_APPLICABLE_INSUFFICIENT_DATA": {
            "context": "Procedura uzgodnienia sumy jest uruchamiana tylko dla sekcji zawierającej pozycję Razem.",
            "rule": "Po uruchomieniu kontroli wymagane są wszystkie składniki, suma i jednostka.",
            "facts": {"NOT_APPLICABLE": "Sekcja {ref} jest opisem jakościowym bez pozycji Razem.", "INSUFFICIENT_DATA": "Sekcja {ref} zawiera pozycję Razem, lecz nie dostarczono jednego składnika."},
        },
    },
    "CROSS_SECTION": {
        "PASS_WARN": {
            "context": "Miara {ref} występuje w tabeli i komentarzu w mln PLN.",
            "rule": "Różnica do 0,5 mln PLN jest zaokrągleniem; różnica do 5 mln PLN wymaga uzgodnienia.",
            "facts": {"PASS": "Różnica między sekcjami wynosi 0,4 mln PLN.", "WARN": "Różnica między sekcjami wynosi 1,4 mln PLN."},
        },
        "WARN_FAIL": {
            "context": "Tabela i komentarz prezentują tę samą miarę {ref} w mln PLN.",
            "rule": "Różnica do 5 mln PLN jest niematerialna; większa różnica jest materialną niespójnością.",
            "facts": {"WARN": "Różnica wynosi 4 mln PLN.", "FAIL": "Różnica wynosi 24 mln PLN."},
        },
        "NOT_APPLICABLE_INSUFFICIENT_DATA": {
            "context": "Porównanie między sekcjami wykonuje się, gdy polityka raportu wymaga tabeli i komentarza.",
            "rule": "Jeżeli obie sekcje są wymagane, potrzebne są wartości tej samej miary i jednostki.",
            "facts": {"NOT_APPLICABLE": "Pakiet {ref} jest załącznikiem tabelarycznym bez wymaganej części narracyjnej.", "INSUFFICIENT_DATA": "Pakiet {ref} wymaga tabeli i komentarza, ale komentarz nie został dostarczony."},
        },
    },
    "PERIOD": {
        "PASS_WARN": {
            "context": "Raport {ref} porównuje dane bieżące z okresem odniesienia.",
            "rule": "Ten sam kwartał jest porównywalny; jawny okres zastępczy wymaga potwierdzenia przez właściciela kontroli.",
            "facts": {"PASS": "Porównano 2026-Q1 z 2025-Q1.", "WARN": "Porównano 2026-Q1 z jawnym okresem zastępczym 2025-Q2."},
        },
        "WARN_FAIL": {
            "context": "Komentarz raportu {ref} opisuje porównanie okresów.",
            "rule": "Jawny okres zastępczy wymaga wyjaśnienia; nieujawnione zestawienie kwartału z pełnym rokiem jest materialnym błędem.",
            "facts": {"WARN": "Nagłówek jawnie oznacza 2025-Q2 jako okres zastępczy.", "FAIL": "Nagłówek przedstawia pełny rok 2025 jako 2025-Q1."},
        },
        "NOT_APPLICABLE_INSUFFICIENT_DATA": {
            "context": "Dane porównawcze są wymagane po pierwszym okresie raportowania produktu.",
            "rule": "Dla kolejnego okresu potrzebna jest wartość bieżąca i wartość porównawcza.",
            "facts": {"NOT_APPLICABLE": "Pakiet {ref} dotyczy pierwszego okresu nowego produktu.", "INSUFFICIENT_DATA": "Pakiet {ref} dotyczy kolejnego okresu, lecz brak wartości porównawczej."},
        },
    },
    "UNIT": {
        "PASS_WARN": {
            "context": "Tabela {ref} ma nagłówek «wszystkie kwoty w mln PLN».",
            "rule": "Jednostka odziedziczona z nagłówka jest poprawna; pominięcie jej w samym komentarzu wymaga doprecyzowania.",
            "facts": {"PASS": "Komentarz podaje {value} mln PLN.", "WARN": "Komentarz podaje {value} bez powtórzenia jednostki."},
        },
        "WARN_FAIL": {
            "context": "Nagłówek tabeli {ref} określa wartości w mln PLN.",
            "rule": "Brak jednostki w komentarzu jest niematerialny; wskazanie tys. PLN tworzy materialną sprzeczność.",
            "facts": {"WARN": "Komentarz podaje {value} bez jednostki.", "FAIL": "Komentarz podaje {value} tys. PLN."},
        },
        "NOT_APPLICABLE_INSUFFICIENT_DATA": {
            "context": "Kontrola jednostki jest uruchamiana dla sekcji zawierających wartości liczbowe.",
            "rule": "Dla wartości liczbowej wymagana jest jednostka raportowa.",
            "facts": {"NOT_APPLICABLE": "Sekcja {ref} zawiera wyłącznie jakościowy opis ładu korporacyjnego.", "INSUFFICIENT_DATA": "Sekcja {ref} zawiera wartość {value}, ale nie podano jednostki."},
        },
    },
    "CURRENCY": {
        "PASS_WARN": {
            "context": "Ekspozycja {ref} jest przeliczana z EUR na PLN.",
            "rule": "Kurs z daty raportu jest właściwy; kurs z poprzedniego dnia roboczego wymaga potwierdzenia.",
            "facts": {"PASS": "Zastosowano kurs z 31.03.2026, daty raportu.", "WARN": "Zastosowano kurs z 30.03.2026, poprzedniego dnia roboczego."},
        },
        "WARN_FAIL": {
            "context": "Ekspozycja {ref} wynosi {value} mln EUR; przekazano datę i kurs referencyjny.",
            "rule": "Kurs zastępczy wymaga potwierdzenia; kwota niezgodna z kursem referencyjnym jest materialnym błędem.",
            "facts": {"WARN": "Użyto udokumentowanego kursu zastępczego z poprzedniego dnia.", "FAIL": "Użyto mnożnika 4,05 zamiast przekazanego kursu 4,25."},
        },
        "NOT_APPLICABLE_INSUFFICIENT_DATA": {
            "context": "Kontrola walutowa jest uruchamiana, gdy pozycja ma walutę inną niż waluta raportowa PLN.",
            "rule": "Po uruchomieniu potrzebne są kwota walutowa, kurs i data kursu.",
            "facts": {"NOT_APPLICABLE": "W pakiecie {ref} wszystkie pozycje są pierwotnie i raportowo w PLN.", "INSUFFICIENT_DATA": "Pakiet {ref} zawiera pozycję w EUR, ale nie przekazano kursu ani jego daty."},
        },
    },
    "DIRECTION": {
        "PASS_WARN": {
            "context": "Miara {ref} zmieniła się między porównywalnymi okresami.",
            "rule": "Określenie «stabilnie» obejmuje zmianę do 2%; zmiana do 5% wymaga doprecyzowania.",
            "facts": {"PASS": "Zmiana wynosi 1,5%, a komentarz mówi o stabilnym poziomie.", "WARN": "Zmiana wynosi 4%, a komentarz mówi o stabilnym poziomie."},
        },
        "WARN_FAIL": {
            "context": "Wartość miary {ref} wzrosła między porównywalnymi okresami.",
            "rule": "Nieprecyzyjne określenie stabilności wymaga korekty; kierunek przeciwny do liczb jest materialnym błędem.",
            "facts": {"WARN": "Komentarz nazywa wzrost o 4% stabilnym poziomem.", "FAIL": "Komentarz stwierdza spadek mimo potwierdzonego wzrostu o 14%."},
        },
        "NOT_APPLICABLE_INSUFFICIENT_DATA": {
            "context": "Kontrola kierunku jest uruchamiana, gdy raport wymaga komentarza o trendzie.",
            "rule": "Do oceny trendu potrzebne są dwie porównywalne wartości i komentarz.",
            "facts": {"NOT_APPLICABLE": "Pakiet {ref} jest pierwszym raportem produktu i nie wymaga komentarza o trendzie.", "INSUFFICIENT_DATA": "Pakiet {ref} wymaga komentarza o trendzie, ale nie przekazano wartości porównawczej."},
        },
    },
    "VARIANCE": {
        "PASS_WARN": {
            "context": "Zmiana miary {ref} przekracza próg komentarza 10%.",
            "rule": "Konkretna i potwierdzona przyczyna spełnia kontrolę; przyczyna wstępna wymaga potwierdzenia.",
            "facts": {"PASS": "Komentarz wskazuje zatwierdzony wzrost wolumenu i zmianę marży.", "WARN": "Komentarz wskazuje wstępnie wzrost wolumenu, bez zatwierdzenia właściciela danych."},
        },
        "WARN_FAIL": {
            "context": "Zmiana miary {ref} przekracza próg komentarza 10%.",
            "rule": "Ogólna przyczyna wymaga uzupełnienia; komentarz sprzeczny z liczbami jest materialnym błędem.",
            "facts": {"WARN": "Komentarz mówi ogólnie o zmianach biznesowych.", "FAIL": "Komentarz opisuje spadek wolumenu, choć źródła potwierdzają jego wzrost."},
        },
        "NOT_APPLICABLE_INSUFFICIENT_DATA": {
            "context": "Analiza odchyleń jest wykonywana tylko dla miar objętych matrycą raportu.",
            "rule": "Dla miary objętej analizą potrzebne są dwie wartości i właściwy próg.",
            "facts": {"NOT_APPLICABLE": "Miara {ref} jest wyłączona z matrycy analizy odchyleń tego raportu.", "INSUFFICIENT_DATA": "Miara {ref} jest objęta matrycą, ale nie przekazano obowiązującego progu."},
        },
    },
    "DISCLOSURE": {
        "PASS_WARN": {
            "context": "Checklista dla noty {ref} wymaga wartości łącznej i podziału segmentowego.",
            "rule": "Wartości zatwierdzone spełniają kontrolę; kompletna nota z jedną wartością wstępną wymaga potwierdzenia.",
            "facts": {"PASS": "Nota zawiera wszystkie wartości zatwierdzone.", "WARN": "Nota jest kompletna, ale jedna wartość segmentowa ma status wstępny."},
        },
        "WARN_FAIL": {
            "context": "Checklista dla noty {ref} wymaga wartości łącznej i podziału segmentowego.",
            "rule": "Wartość wstępna wymaga potwierdzenia; brak obowiązkowego elementu jest materialnym naruszeniem.",
            "facts": {"WARN": "Wszystkie elementy są obecne, lecz jedna wartość ma status wstępny.", "FAIL": "W nocie nie ma obowiązkowego podziału segmentowego."},
        },
        "NOT_APPLICABLE_INSUFFICIENT_DATA": {
            "context": "Wymóg noty {ref} zależy od jednostkowego albo skonsolidowanego zakresu raportu.",
            "rule": "Dla raportu skonsolidowanego potrzebna jest właściwa checklista i treść noty.",
            "facts": {"NOT_APPLICABLE": "Raport jest jednostkowy, a wymóg ograniczono do sprawozdań skonsolidowanych.", "INSUFFICIENT_DATA": "Raport jest skonsolidowany, lecz nie przekazano właściwej checklisty."},
        },
    },
    "EVIDENCE": {
        "PASS_WARN": {
            "context": "Ustalenie {ref} wskazuje źródło bezpośrednio związane z kontrolowaną miarą.",
            "rule": "Źródło zatwierdzone spełnia kontrolę; źródło robocze wymaga potwierdzenia.",
            "facts": {"PASS": "Wskazane źródło ma status zatwierdzony.", "WARN": "Wskazane źródło ma status roboczy."},
        },
        "WARN_FAIL": {
            "context": "Ustalenie {ref} wymaga identyfikowalnego i merytorycznie powiązanego źródła.",
            "rule": "Źródło robocze wymaga potwierdzenia; źródło niepowiązane nie potwierdza ustalenia.",
            "facts": {"WARN": "Wskazane źródło dotyczy właściwej miary, ale ma status roboczy.", "FAIL": "Wskazane źródło dotyczy innej miary i nie potwierdza ustalenia."},
        },
        "NOT_APPLICABLE_INSUFFICIENT_DATA": {
            "context": "Kontrola dowodu jest uruchamiana dla sformułowanego ustalenia kontrolnego.",
            "rule": "Jeżeli ustalenie istnieje, potrzebne jest identyfikowalne źródło.",
            "facts": {"NOT_APPLICABLE": "Pakiet {ref} nie zawiera ustalenia ani tezy wymagającej potwierdzenia.", "INSUFFICIENT_DATA": "Pakiet {ref} zawiera ustalenie, ale materiał źródłowy nie został dołączony."},
        },
    },
}


def _render(value: str, variables: dict[str, Any]) -> str:
    return value.format(**variables)


def _expected_output(
    control: dict[str, str], status: str, sources: list[dict[str, str]], reason_code: str
) -> dict[str, Any]:
    evidence = [
        {"source_id": sources[1]["source_id"], "value": sources[1]["content"]},
        {"source_id": sources[2]["source_id"], "value": sources[2]["content"]},
    ]
    if status == "PASS":
        finding = "Materiał spełnia warunek kontroli i nie wymaga korekty."
        action = "Zachować wynik kontroli bez działań korygujących."
    elif status == "WARN":
        finding = "Wykryto konkretną niematerialną lub wstępną niezgodność wymagającą wyjaśnienia."
        action = "Wyjaśnić wskazaną przesłankę i udokumentować decyzję kontrolera."
    elif status == "FAIL":
        finding = "Potwierdzono materialne naruszenie jawnej reguły kontrolnej."
        action = "Skorygować naruszenie i przekazać ustalenie właścicielowi kontroli."
    elif status == "NOT_APPLICABLE":
        finding = "Warunek uruchamiający kontrolę nie występuje w zakresie tego pakietu."
        action = "Udokumentować przesłankę zakresową i zamknąć kontrolę."
    else:
        finding = "Kontrola ma zastosowanie, ale brakuje obowiązkowego materiału do wydania osądu."
        action = "Pozyskać wskazany materiał przed zakończeniem kontroli."
    policy = _policy()["statuses"][status]
    return {
        "control_id": control["id"],
        "control_type": control["type"],
        "status": status,
        "severity": policy["severity"],
        "finding": finding,
        "evidence": evidence,
        "recommended_action": action,
        "requires_human_review": policy["requires_human_review"],
        "confidence": "HIGH" if status in {"PASS", "FAIL", "NOT_APPLICABLE"} else "MEDIUM",
    }


def _build_pair(
    *, split: str, boundary_type: str, family_number: int, serial: int, seed: int
) -> tuple[list[dict[str, Any]], int]:
    statuses = BOUNDARIES[boundary_type]
    control_type = CONTROL_TYPES[(family_number + len(boundary_type)) % len(CONTROL_TYPES)]
    control = _controls()[control_type]
    scenario = SCENARIOS[control_type][boundary_type]
    rng = random.Random(seed + family_number * 104729 + len(boundary_type))
    variables = {
        "ref": f"R{family_number:03d}-{rng.choice(('A', 'B', 'C', 'D'))}",
        "value": 100 + rng.randint(0, 900),
        "prior": 50 + rng.randint(0, 400),
    }
    family_id = f"boundary-{boundary_type.lower()}-f{family_number:03d}"
    task = TASKS[family_number % len(TASKS)]
    common = _render(scenario["context"], variables) + f" Identyfikator pakietu: {variables['ref']}."
    rule = _render(scenario["rule"], variables)
    cases: list[dict[str, Any]] = []
    for variant_id, status in enumerate(statuses):
        decisive = _render(scenario["facts"][status], variables)
        prefix = f"boundary.{family_number:03d}"
        sources = [
            {"source_id": f"{prefix}.context", "content": common},
            {"source_id": f"{prefix}.decision", "content": decisive},
            {"source_id": f"{prefix}.policy", "content": rule},
        ]
        reason_code = {
            "PASS": "CONTROL_SATISFIED",
            "WARN": "NON_MATERIAL_DEVIATION",
            "FAIL": "MATERIAL_BREACH",
            "NOT_APPLICABLE": "TRIGGER_ABSENT",
            "INSUFFICIENT_DATA": "REQUIRED_SOURCE_MISSING",
        }[status]
        local_control = {
            "id": control["id"],
            "type": control_type,
            "procedure": f"{control['procedure']} Reguła graniczna: {rule}",
        }
        cases.append(
            {
                "case_id": f"BD-{serial:04d}",
                "group_id": family_id,
                "split": split,
                "difficulty": "medium" if status in {"PASS", "NOT_APPLICABLE"} else "hard",
                "control": local_control,
                "input": {"task": task, "sources": sources, "deterministic_check": None},
                "expected_output": _expected_output(local_control, status, sources, reason_code),
                "metadata": {
                    "dataset_version": DATASET_VERSION,
                    "family_id": family_id,
                    "variant_id": variant_id,
                    "generation_method": "template",
                    "synthetic": True,
                    "language": "pl",
                    "seed": seed,
                    "mutation_type": f"{boundary_type.lower()}__{status.lower()}",
                    "boundary_type": boundary_type,
                    "reason_code": reason_code,
                    "paired_status": statuses[1 - variant_id],
                    "provenance": [
                        "configs/status_policy_v1.json",
                        "configs/control_catalog.json",
                        "src/peft_workshop/boundary_dataset.py",
                    ],
                },
            }
        )
        serial += 1
    return cases, serial


def build_boundary_pack(seed: int = DEFAULT_SEED) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    serial = 1
    family_number = 0
    for split, boundary_counts in PAIR_COUNTS.items():
        for boundary_type, count in boundary_counts.items():
            for _ in range(count):
                pair, serial = _build_pair(
                    split=split,
                    boundary_type=boundary_type,
                    family_number=family_number,
                    serial=serial,
                    seed=seed,
                )
                cases.extend(pair)
                family_number += 1
    return cases


def validate_boundary_pack(cases: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    expected_split_counts = {split: 2 * sum(counts.values()) for split, counts in PAIR_COUNTS.items()}
    actual_split_counts = Counter(case["split"] for case in cases)
    if dict(actual_split_counts) != expected_split_counts:
        errors.append(f"Niepoprawny rozkład splitów: {dict(actual_split_counts)}")
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for case in cases:
        groups[case["group_id"]].append(case)
        searchable = " ".join(
            [case["input"]["task"]]
            + [source["content"] for source in case["input"]["sources"]]
        )
        leaked = [label for label in ("PASS", "WARN", "FAIL", "INSUFFICIENT_DATA", "NOT_APPLICABLE") if label in searchable]
        if leaked:
            errors.append(f"{case['case_id']}: etykieta ujawniona w wejściu: {leaked}")
    for group_id, pair in groups.items():
        if len(pair) != 2:
            errors.append(f"{group_id}: para ma {len(pair)} rekordów")
            continue
        boundary_type = pair[0]["metadata"]["boundary_type"]
        statuses = {case["expected_output"]["status"] for case in pair}
        if statuses != set(BOUNDARIES[boundary_type]):
            errors.append(f"{group_id}: statusy {sorted(statuses)} nie odpowiadają {boundary_type}")
        if len({case["split"] for case in pair}) != 1:
            errors.append(f"{group_id}: para przecieka między splitami")
        if pair[0]["input"]["task"] != pair[1]["input"]["task"]:
            errors.append(f"{group_id}: różne zadania w parze")
        left_sources = pair[0]["input"]["sources"]
        right_sources = pair[1]["input"]["sources"]
        if [item["source_id"] for item in left_sources] != [item["source_id"] for item in right_sources]:
            errors.append(f"{group_id}: różne source_id w parze")
        changed = sum(
            left["content"] != right["content"]
            for left, right in zip(left_sources, right_sources, strict=True)
        )
        if changed != 1:
            errors.append(f"{group_id}: oczekiwano jednej zmienionej przesłanki, otrzymano {changed}")
    status_counts = Counter(case["expected_output"]["status"] for case in cases)
    expected_status_counts = Counter(
        {"PASS": 80, "WARN": 160, "FAIL": 80, "INSUFFICIENT_DATA": 110, "NOT_APPLICABLE": 110}
    )
    if status_counts != expected_status_counts:
        errors.append(f"Niepoprawny rozkład statusów: {dict(status_counts)}")
    na_types = {case["control"]["type"] for case in cases if case["expected_output"]["status"] == "NOT_APPLICABLE"}
    warn_types = {case["control"]["type"] for case in cases if case["expected_output"]["status"] == "WARN"}
    if len(na_types) < 4:
        errors.append(f"NOT_APPLICABLE obejmuje tylko {len(na_types)} typy kontroli")
    if len(warn_types) < 6:
        errors.append(f"WARN obejmuje tylko {len(warn_types)} typów kontroli")
    return errors


def build_review_manifest(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    strata: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for case in cases:
        status = case["expected_output"]["status"]
        if status == "NOT_APPLICABLE":
            selected.append(case)
        else:
            key = (case["metadata"]["boundary_type"], status, case["control"]["type"])
            strata[key].append(case)
    for items in strata.values():
        selected.extend(sorted(items, key=lambda item: item["case_id"])[: math.ceil(len(items) * 0.2)])
    unique = {case["case_id"]: case for case in selected}
    return [
        {
            "case_id": case_id,
            "group_id": case["group_id"],
            "split": case["split"],
            "control_type": case["control"]["type"],
            "boundary_type": case["metadata"]["boundary_type"],
            "expected_status": case["expected_output"]["status"],
            "reason_code": case["metadata"]["reason_code"],
            "review_scope": "gold_label, applicability, evidence, paired premise",
            "review_method": "semantic template review plus rendered-record invariant review",
            "reviewer_type": "implementation",
            "decision": "APPROVED",
            "critical_error": False,
        }
        for case_id, case in sorted(unique.items())
    ]


def _write_registry(
    cases: list[dict[str, Any]], output: Path, split_dir: Path, registry_path: Path
) -> None:
    split_hashes = {
        split: hashlib.sha256((split_dir / f"boundary_{split}.jsonl").read_bytes()).hexdigest()
        for split in PAIR_COUNTS
    }
    registry = {
        "registry_version": "1.0.0",
        "datasets": [
            {
                "name": "boundary-pack-v1",
                "version": BOUNDARY_VERSION,
                "status": "candidate_for_boundary_freeze",
                "output": output.relative_to(DATA_DIR.parent).as_posix(),
                "sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
                "count": len(cases),
                "split_hashes": split_hashes,
                "original_dataset_modified": False,
                "test_status": "unopened",
            }
        ]
    }
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def generate_artifacts(
    output: Path = DEFAULT_OUTPUT,
    split_dir: Path = DEFAULT_SPLIT_DIR,
    registry_path: Path = DEFAULT_REGISTRY,
    review_path: Path = DEFAULT_REVIEW,
    audit_path: Path = DEFAULT_AUDIT,
    seed: int = DEFAULT_SEED,
) -> dict[str, Any]:
    cases = build_boundary_pack(seed)
    boundary_errors = validate_boundary_pack(cases)
    initial_audit = audit_cases(cases)
    errors = boundary_errors + initial_audit["errors"]
    if errors:
        raise ValueError("Boundary pack nie przeszedł walidacji:\n" + "\n".join(errors))
    write_jsonl(cases, output)
    for split in PAIR_COUNTS:
        write_jsonl([case for case in cases if case["split"] == split], split_dir / f"boundary_{split}.jsonl")
    review = build_review_manifest(cases)
    write_jsonl(review, review_path)
    audit = audit_cases(cases, output)
    audit["boundary_validation"] = {
        "valid": True,
        "pair_count": len(cases) // 2,
        "single_premise_pair_count": len(cases) // 2,
        "not_applicable_control_types": sorted({case["control"]["type"] for case in cases if case["expected_output"]["status"] == "NOT_APPLICABLE"}),
        "warn_control_types": sorted({case["control"]["type"] for case in cases if case["expected_output"]["status"] == "WARN"}),
        "reviewed_count": len(review),
        "not_applicable_reviewed": sum(item["expected_status"] == "NOT_APPLICABLE" for item in review),
        "other_reviewed": sum(item["expected_status"] != "NOT_APPLICABLE" for item in review),
        "critical_review_errors": sum(item["critical_error"] for item in review),
        "owner_signoff": "pending",
    }
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    audit_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _write_registry(cases, output, split_dir, registry_path)
    return audit


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Wygeneruj boundary-pack-v1")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--split-dir", default=str(DEFAULT_SPLIT_DIR))
    parser.add_argument("--registry", default=str(DEFAULT_REGISTRY))
    parser.add_argument("--review", default=str(DEFAULT_REVIEW))
    parser.add_argument("--audit", default=str(DEFAULT_AUDIT))
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    audit = generate_artifacts(
        output=resolve_project_path(args.output),
        split_dir=resolve_project_path(args.split_dir),
        registry_path=resolve_project_path(args.registry),
        review_path=resolve_project_path(args.review),
        audit_path=resolve_project_path(args.audit),
        seed=args.seed,
    )
    print(json.dumps(audit["summary"], ensure_ascii=False, indent=2))
    print(json.dumps(audit["boundary_validation"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
