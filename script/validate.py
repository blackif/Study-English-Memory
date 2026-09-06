"""Deterministic validation checks for Study-English-Memory.

This script automates the parts of VALIDATION.md that have a single
objectively correct answer: schema/structure conformance against
templates/, recomputed aggregate statistics, the review_count invariant,
the next_unit reference chain, and Error Index field completeness.

It deliberately does NOT judge teaching quality, error-severity
classification, or whether a design choice (e.g. which words belong in a
Unit) is pedagogically sound -- those still require human/AI judgement and
are left to VALIDATION.md's manual sections.

Usage:
    python3 script/validate.py

Exit code is 0 if there are no FAIL results, 1 otherwise. WARN results do
not affect the exit code -- they flag things a human should look at, not
things that are definitely wrong.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
CURRICULUM = ROOT / "curriculum"
TEMPLATES = ROOT / "templates"
TESTS = ROOT / "tests"

STOPWORDS = {"a", "an", "the", "to", "in", "at", "on", "up", "for", "of"}

results: list[tuple[str, str, str]] = []  # (section, status, message)


def record(section: str, status: str, message: str) -> None:
    results.append((section, status, message))


def load(path: Path) -> Any:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def load_optional(path: Path) -> Any | None:
    return load(path) if path.exists() else None


# ---------------------------------------------------------------------------
# Section 2: structural conformance against templates/
# ---------------------------------------------------------------------------

def key_shape(obj: Any) -> Any:
    """Reduce a JSON value to its key structure, ignoring actual content.

    Dicts -> dict of {key: key_shape(value)}
    Non-empty lists of dicts -> [key_shape(first_item)]
    Any other list -> "list"
    Scalars -> "scalar"
    """
    if obj is None:
        # A null in a template is a placeholder for "not yet populated" and
        # carries no structural information (e.g. last_session before any
        # Unit has completed). Treat it as compatible with anything.
        return "any"
    if isinstance(obj, dict):
        return {k: key_shape(v) for k, v in obj.items()}
    if isinstance(obj, list):
        if obj and isinstance(obj[0], dict):
            return [key_shape(obj[0])]
        return "list"
    return "scalar"


def diff_shape(template_shape: Any, actual_shape: Any, path: str, missing: list[str], extra: list[str]) -> None:
    if template_shape == "any" or actual_shape == "any":
        # Either side being null (a legitimate "not applicable" value, e.g.
        # a resolved error's next_review) carries no structural information
        # to compare.
        return
    if isinstance(template_shape, dict) and isinstance(actual_shape, dict):
        for k, v in template_shape.items():
            child = f"{path}.{k}" if path else k
            if k not in actual_shape:
                missing.append(child)
            else:
                diff_shape(v, actual_shape[k], child, missing, extra)
        for k in actual_shape:
            if k not in template_shape:
                extra.append(f"{path}.{k}" if path else k)
    elif isinstance(template_shape, list) and isinstance(actual_shape, list):
        if template_shape and actual_shape:
            diff_shape(template_shape[0], actual_shape[0], f"{path}[]", missing, extra)
    elif template_shape != actual_shape:
        # e.g. template has a list of records but actual is empty list ("list"
        # vs "list" always matches; this branch mostly covers scalar-vs-dict
        # mismatches which are worth flagging as a shape problem.
        if not (template_shape == "list" and actual_shape == "list"):
            missing.append(f"{path} (shape mismatch)")


def check_structural_conformance() -> None:
    section = "2-structure"
    pairs = [
        (TEMPLATES / "Study English Memory.json", DATA / "Study English Memory.json"),
        (TEMPLATES / "Vocabulary Index.json", DATA / "Vocabulary Index.json"),
        (TEMPLATES / "Grammar Index.json", DATA / "Grammar Index.json"),
        (TEMPLATES / "Error Index.json", DATA / "Error Index.json"),
        (TEMPLATES / "Curriculum Memory.json", DATA / "Curriculum Memory.json"),
    ]
    for unit_file in sorted(CURRICULUM.glob("unit-*.json")):
        pairs.append((TEMPLATES / "curriculum-unit.json", unit_file))
    if TESTS.exists():
        for test_file in sorted(TESTS.glob("*.json")):
            pairs.append((TEMPLATES / "test.json", test_file))

    for template_path, data_path in pairs:
        if not data_path.exists():
            continue
        template = load(template_path)
        data = load(data_path)

        if template.get("schema_version") != data.get("schema_version"):
            record(
                section, "FAIL",
                f"{data_path.name}: schema_version {data.get('schema_version')!r} "
                f"!= template {template.get('schema_version')!r}",
            )

        missing: list[str] = []
        extra: list[str] = []
        diff_shape(key_shape(template), key_shape(data), "", missing, extra)
        if missing:
            record(section, "FAIL", f"{data_path.name}: missing/mismatched fields: {missing}")
        if extra:
            record(section, "FAIL", f"{data_path.name}: unexpected extra fields: {extra}")
        if not missing and not extra and template.get("schema_version") == data.get("schema_version"):
            record(section, "PASS", f"{data_path.name} matches its template structure")


# ---------------------------------------------------------------------------
# Section 3: recomputed aggregates
# ---------------------------------------------------------------------------

def recompute_mastery(records_list: list[dict]) -> dict:
    n = len(records_list)
    active = sum(1 for r in records_list if r.get("status") == "active")
    mastered = sum(1 for r in records_list if r.get("status") == "mastered")
    needs_review = sum(1 for r in records_list if r.get("status") == "needs_review")
    total_overall = sum(r["mastery"]["overall"] for r in records_list)
    average = round((total_overall / n) / 5, 2) if n else 0
    return {
        "introduced": n,
        "active": active,
        "mastered": mastered,
        "needs_review": needs_review,
        "average_score": average,
    }


def check_recomputed_aggregates() -> None:
    section = "3-recompute"
    state = load_optional(DATA / "Study English Memory.json")
    vocab = load_optional(DATA / "Vocabulary Index.json")
    grammar = load_optional(DATA / "Grammar Index.json")
    if not state:
        record(section, "WARN", "Study English Memory.json not found, skipping")
        return

    if vocab is not None:
        expected = recompute_mastery(vocab["words"])
        actual = state.get("vocabulary_mastery", {})
        for key, exp_val in expected.items():
            act_val = actual.get(key)
            if act_val != exp_val:
                record(
                    section, "FAIL",
                    f"vocabulary_mastery.{key}: computed {exp_val}, file has {act_val}",
                )
            else:
                record(section, "PASS", f"vocabulary_mastery.{key} == {exp_val}")

    if grammar is not None:
        expected = recompute_mastery(grammar["grammar"])
        actual = state.get("grammar_mastery", {})
        for key, exp_val in expected.items():
            act_val = actual.get(key)
            if act_val != exp_val:
                record(
                    section, "FAIL",
                    f"grammar_mastery.{key}: computed {exp_val}, file has {act_val}",
                )
            else:
                record(section, "PASS", f"grammar_mastery.{key} == {exp_val}")


# ---------------------------------------------------------------------------
# Section 4: review_count invariant (review_count == len(units) - 1)
# ---------------------------------------------------------------------------

def check_review_count_invariant() -> None:
    section = "4-review_count"
    vocab = load_optional(DATA / "Vocabulary Index.json")
    grammar = load_optional(DATA / "Grammar Index.json")

    if vocab is not None:
        for w in vocab["words"]:
            expected = max(len(w["units"]) - 1, 0)
            if w["review_count"] != expected:
                record(
                    section, "FAIL",
                    f"vocabulary '{w['word']}': review_count={w['review_count']}, "
                    f"expected {expected} from units={w['units']}",
                )
        record(section, "PASS", "vocabulary review_count invariant checked for all words") \
            if all(w["review_count"] == max(len(w["units"]) - 1, 0) for w in vocab["words"]) else None

    if grammar is not None:
        for g in grammar["grammar"]:
            expected = max(len(g["units"]) - 1, 0)
            if g["review_count"] != expected:
                record(
                    section, "FAIL",
                    f"grammar '{g['topic']}': review_count={g['review_count']}, "
                    f"expected {expected} from units={g['units']}",
                )
        record(section, "PASS", "grammar review_count invariant checked for all topics") \
            if all(g["review_count"] == max(len(g["units"]) - 1, 0) for g in grammar["grammar"]) else None


# ---------------------------------------------------------------------------
# Section 6: collocation / vocabulary coverage (WARN, needs human judgement
# for word-form questions like shop/shopping)
# ---------------------------------------------------------------------------

def tokenize(phrase: str) -> list[str]:
    words = re.findall(r"[A-Za-z']+", phrase.lower())
    return [w for w in words if w not in STOPWORDS]


def check_collocation_coverage() -> None:
    section = "6-collocation_coverage"
    for unit_file in sorted(CURRICULUM.glob("unit-*.json")):
        unit = load(unit_file)
        vocab = unit.get("vocabulary", {})
        known = set()
        for bucket in ("core", "supporting", "review"):
            for item in vocab.get(bucket, []):
                known.update(tokenize(item))
        for colloc in unit.get("collocations", []):
            for token in tokenize(colloc):
                if token not in known:
                    record(
                        section, "WARN",
                        f"{unit_file.name}: collocation '{colloc}' uses '{token}', "
                        f"not found in this unit's vocabulary.core/supporting/review "
                        f"(check whether it needs to be added, or is a known word form variant)",
                    )


# ---------------------------------------------------------------------------
# Section 7: position / next_unit reference chain
# ---------------------------------------------------------------------------

def check_position_chain() -> None:
    section = "7-position_chain"
    state = load_optional(DATA / "Study English Memory.json")
    if not state:
        record(section, "WARN", "Study English Memory.json not found, skipping")
        return

    pos = state.get("current_position", {})
    if "unit" in pos or "status" in pos:
        record(section, "FAIL", f"current_position has leftover key(s): {list(pos.keys())}")
    else:
        record(section, "PASS", "current_position has no leftover unit/status keys")

    next_unit = pos.get("next_unit")
    if next_unit:
        candidate = CURRICULUM / f"{next_unit}.json"
        test_candidate = TESTS / f"{next_unit}.json" if TESTS.exists() else None
        if candidate.exists():
            data = load(candidate)
            actual_id = data.get("unit", {}).get("id")
            if actual_id != next_unit:
                record(section, "FAIL", f"{candidate.name}: unit.id={actual_id!r} != filename {next_unit!r}")
            else:
                record(section, "PASS", f"next_unit '{next_unit}' file exists with matching id")
        elif test_candidate and test_candidate.exists():
            record(section, "PASS", f"next_unit '{next_unit}' resolves to a test/review file")
        else:
            record(section, "WARN", f"next_unit '{next_unit}' has no corresponding file yet (may not be authored yet)")

    last_completed = pos.get("last_completed_unit")
    if last_completed:
        completed_file = CURRICULUM / f"{last_completed}.json"
        if completed_file.exists():
            data = load(completed_file)
            if data.get("next_unit") != next_unit:
                record(
                    section, "FAIL",
                    f"{completed_file.name}: next_unit={data.get('next_unit')!r} "
                    f"!= current_position.next_unit {next_unit!r}",
                )
            else:
                record(section, "PASS", f"{last_completed}'s declared next_unit matches current_position")


# ---------------------------------------------------------------------------
# Section 5: Error Index field completeness and internal consistency
# ---------------------------------------------------------------------------

REQUIRED_ERROR_FIELDS = {
    "id", "type", "category", "incorrect", "correct", "first_seen", "last_seen",
    "frequency", "severity", "status", "related_grammar", "review_history", "next_review",
}
ALLOWED_STATUS = {"needs_review", "resolved"}
ALLOWED_SEVERITY = {"low", "medium", "high"}


def check_error_index() -> None:
    section = "5-error_index"
    errors = load_optional(DATA / "Error Index.json")
    if errors is None:
        record(section, "WARN", "Error Index.json not found, skipping")
        return

    ids_seen = set()
    for err in errors["errors"]:
        missing = REQUIRED_ERROR_FIELDS - set(err.keys())
        if missing:
            record(section, "FAIL", f"{err.get('id', '?')}: missing fields {missing}")
        if err.get("id") in ids_seen:
            record(section, "FAIL", f"duplicate error id {err.get('id')}")
        ids_seen.add(err.get("id"))
        if err.get("status") not in ALLOWED_STATUS:
            record(section, "FAIL", f"{err.get('id')}: invalid status {err.get('status')!r}")
        if err.get("severity") not in ALLOWED_SEVERITY:
            record(section, "FAIL", f"{err.get('id')}: invalid severity {err.get('severity')!r}")
        if err.get("status") == "resolved" and err.get("next_review") is not None:
            record(section, "WARN", f"{err.get('id')}: resolved but next_review is not null")
        if err.get("status") == "needs_review" and not err.get("next_review"):
            record(section, "WARN", f"{err.get('id')}: needs_review but next_review is empty")

    if not any(s == "FAIL" for sec, s, _ in results if sec == section):
        record(section, "PASS", f"all {len(errors['errors'])} Error Index entries have required fields and valid status/severity")


# ---------------------------------------------------------------------------
# Section 8 (best-effort): aggregates should only change when their source
# index changed in the same commit range. Requires git; degrades gracefully.
# ---------------------------------------------------------------------------

def check_no_copy_forward_git() -> None:
    section = "8-no_copy_forward(git, best-effort)"
    try:
        changed = subprocess.run(
            ["git", "diff", "--name-only", "HEAD~1", "HEAD"],
            cwd=ROOT, capture_output=True, text=True, check=True,
        ).stdout.splitlines()
    except Exception as exc:  # noqa: BLE001
        record(section, "WARN", f"skipped (git history unavailable: {exc})")
        return

    vocab_changed = "data/Vocabulary Index.json" in changed
    grammar_changed = "data/Grammar Index.json" in changed
    state_changed = "data/Study English Memory.json" in changed

    if not state_changed:
        record(section, "WARN", "Study English Memory.json unchanged in last commit, nothing to check")
        return

    try:
        old_state = json.loads(
            subprocess.run(
                ["git", "show", "HEAD~1:data/Study English Memory.json"],
                cwd=ROOT, capture_output=True, text=True, check=True,
            ).stdout
        )
        new_state = load(DATA / "Study English Memory.json")
    except Exception as exc:  # noqa: BLE001
        record(section, "WARN", f"skipped (could not read previous revision: {exc})")
        return

    vocab_stat_changed = old_state.get("vocabulary_mastery") != new_state.get("vocabulary_mastery")
    grammar_stat_changed = old_state.get("grammar_mastery") != new_state.get("grammar_mastery")

    if vocab_stat_changed and not vocab_changed:
        record(section, "FAIL", "vocabulary_mastery changed but Vocabulary Index.json did not (fabricated numbers)")
    elif vocab_changed and not vocab_stat_changed:
        record(section, "WARN", "Vocabulary Index.json changed but vocabulary_mastery did not (double-check average_score didn't shift)")
    else:
        record(section, "PASS", "vocabulary_mastery change is consistent with Vocabulary Index.json change")

    if grammar_stat_changed and not grammar_changed:
        record(section, "FAIL", "grammar_mastery changed but Grammar Index.json did not (fabricated numbers)")
    elif grammar_changed and not grammar_stat_changed:
        record(section, "WARN", "Grammar Index.json changed but grammar_mastery did not (double-check average_score didn't shift)")
    else:
        record(section, "PASS", "grammar_mastery change is consistent with Grammar Index.json change")


# ---------------------------------------------------------------------------

def main() -> int:
    check_structural_conformance()
    check_recomputed_aggregates()
    check_review_count_invariant()
    check_error_index()
    check_collocation_coverage()
    check_position_chain()
    check_no_copy_forward_git()

    fail_count = sum(1 for _, status, _ in results if status == "FAIL")
    warn_count = sum(1 for _, status, _ in results if status == "WARN")
    pass_count = sum(1 for _, status, _ in results if status == "PASS")

    current_section = None
    for section, status, message in results:
        if section != current_section:
            print(f"\n=== {section} ===")
            current_section = section
        print(f"[{status}] {message}")

    print(f"\n{pass_count} PASS, {warn_count} WARN, {fail_count} FAIL")
    if fail_count:
        print("Result: FAIL -- fix the above before reporting Unit completion.")
        return 1
    print("Result: PASS (deterministic checks only -- still review VALIDATION.md's manual sections).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
