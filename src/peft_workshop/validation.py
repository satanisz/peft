from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .paths import SCHEMA_DIR


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


OUTPUT_SCHEMA = _load_json(SCHEMA_DIR / "financial_control_output.schema.json")
CASE_SCHEMA = _load_json(SCHEMA_DIR / "control_case.schema.json")
CASE_SCHEMA["properties"]["expected_output"] = OUTPUT_SCHEMA

OUTPUT_VALIDATOR = Draft202012Validator(OUTPUT_SCHEMA)
CASE_VALIDATOR = Draft202012Validator(CASE_SCHEMA)


def format_errors(errors: list[Any]) -> list[str]:
    formatted: list[str] = []
    for error in sorted(errors, key=lambda item: list(item.absolute_path)):
        location = ".".join(str(part) for part in error.absolute_path) or "$"
        formatted.append(f"{location}: {error.message}")
    return formatted


def validate_output(payload: dict[str, Any]) -> list[str]:
    return format_errors(list(OUTPUT_VALIDATOR.iter_errors(payload)))


def validate_case(payload: dict[str, Any]) -> list[str]:
    errors = format_errors(list(CASE_VALIDATOR.iter_errors(payload)))
    available_sources = {item["source_id"] for item in payload.get("input", {}).get("sources", [])}
    expected_sources = {
        item["source_id"] for item in payload.get("expected_output", {}).get("evidence", [])
    }
    unknown = sorted(expected_sources - available_sources)
    if unknown:
        errors.append(f"expected_output.evidence: nieznane source_id: {', '.join(unknown)}")
    if payload.get("control", {}).get("type") != payload.get("expected_output", {}).get("control_type"):
        errors.append("control.type: nie zgadza się z expected_output.control_type")
    if payload.get("control", {}).get("id") != payload.get("expected_output", {}).get("control_id"):
        errors.append("control.id: nie zgadza się z expected_output.control_id")
    return errors


def extract_json_object(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        first_newline = cleaned.find("\n")
        last_fence = cleaned.rfind("```")
        if first_newline != -1 and last_fence > first_newline:
            cleaned = cleaned[first_newline + 1:last_fence].strip()

    decoder = json.JSONDecoder()
    for index, character in enumerate(cleaned):
        if character != "{":
            continue
        try:
            value, _ = decoder.raw_decode(cleaned[index:])
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
    raise ValueError("Nie znaleziono poprawnego obiektu JSON w odpowiedzi modelu")


def validate_prediction_sources(case: dict[str, Any], output: dict[str, Any]) -> list[str]:
    available = {item["source_id"] for item in case["input"]["sources"]}
    evidence = output.get("evidence", [])
    if not isinstance(evidence, list):
        return ["Pole evidence nie jest listą"]
    if any(not isinstance(item, dict) for item in evidence):
        return ["Każdy element evidence musi być obiektem"]
    used = {item.get("source_id") for item in evidence}
    unknown = sorted(str(item) for item in used - available)
    return [f"Nieznany source_id w predykcji: {item}" for item in unknown]
