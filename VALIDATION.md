# Unit Completion Validation Checklist

## Purpose
This is a mandatory gate, not a suggestion. It must be run **every time** a
learning Unit, Group Review, or Major Test is completed — after the
completion steps in `SKILL.md` §10 have been drafted, and **before** telling
the user the Unit is done or moving on to the next one.

**Run `python3 script/validate.py` first.** It has a single, deterministic,
correct answer for §§2, 3, 4, 5, and 7 below (structure conformance,
recomputed aggregates, the review_count invariant, Error Index field
completeness, and the next_unit chain), plus a best-effort check for §8 when
git history is available. Trust its output over your own arithmetic — the
whole reason it exists is that hand-computed sums and manual key-by-key
diffing are exactly where past executions of this skill went wrong. A
non-zero exit code is a hard stop: fix the file it points to and re-run
until it exits 0.

What the script does **not** and cannot judge — §1, §6, and part of §5 below
— still needs a human/AI read of `history/unit-XXX.md` and the curriculum
files:
- whether an index file *should* have changed at all this Unit (§1),
- whether an error's severity/category classification is actually sound,
  not just structurally well-formed (§5),
- whether a collocation word missing from the vocabulary list (flagged by
  the script as WARN) is a genuine gap or an acceptable word-form variant
  like shop/shopping (§6).

Every check below must be answered with an actual computed value (from the
script) or an explicit judgement call written out in words, not a general
impression like "looks consistent". Show your work inline as you go, then
end with the PASS/FAIL table in §9, folding in the script's exit status.

---

## 1. File-touch check *(manual judgement)*
List every file that *should* have changed for this completion, and confirm
each one actually did:

- [ ] `history/unit-XXX.md` — created (never edited retroactively for a
      past Unit).
- [ ] `data/Vocabulary Index.json` — modified, **if and only if** the Unit
      introduced or deliberately reviewed any vocabulary. If the Unit used
      zero vocabulary from Vocabulary Index or `vocabulary.core` /
      `vocabulary.supporting`, this is impossible in practice — treat an
      unmodified Vocabulary Index as a failure by default.
- [ ] `data/Grammar Index.json` — modified, same logic as above for grammar
      topics.
- [ ] `data/Error Index.json` — modified whenever the Unit's history records
      any error, OR the history explicitly states "no meaningful errors
      observed" (see §5). An unmodified Error Index alongside a history file
      that lists errors is always a failure.
- [ ] `curriculum/unit-(N+1).json` (or the scheduled review/test file)
      created, unless it already exists.
- [ ] `data/Study English Memory.json` — modified.

If any expected file is missing from the diff, stop here and fix it before
continuing to the next sections — the recomputation checks below are
meaningless if the underlying index wasn't actually touched.

## 2. Structural conformance check *(automated by `script/validate.py`)*
For every JSON file changed in this completion, compare its **top-level and
nested key structure** against its corresponding file in `templates/`:

- Curriculum unit files must have: `schema_version`, `unit` (containing
  `id`, `level`, `group`, `number`, `type`, `title`, `overview`),
  `objectives`, `grammar` (`new`, `review`, `focus`), `vocabulary` (`theme`,
  `core`, `supporting`, `review`), `collocations` (top-level, not nested
  inside `vocabulary`), `sentence_patterns`, `lesson_flow`, `practice`
  (`grammar`, `vocabulary`, `output`), `assessment` (`grammar`, `vocabulary`,
  `output`), `completion_criteria` (`minimum_understanding`,
  `minimum_output`), `next_unit`.
- Central state file must match `templates/Study English Memory.json`
  exactly at every nesting level, including `current_position` containing
  only `group`, `unit_type`, `last_completed_unit`, `next_unit`.
- Index files (`Vocabulary Index.json`, `Grammar Index.json`,
  `Error Index.json`) must match their template's per-record field set.

Explicitly list any key that is present in the new file but absent from the
template, or vice versa. Do not add, rename, flatten, or restructure any
field. If the data model genuinely needs to change, stop and follow the
`SKILL.md` §3 migration rule (bump `schema_version` in the template first)
instead of silently diverging in one file.

## 3. Recomputation check *(automated by `script/validate.py`)*
For `vocabulary_mastery` and `grammar_mastery` in the central state file,
actually recompute each field from the corresponding index **after** its
update in this completion, and compare to what was written:

- `introduced` = count of records in the index. State the count.
- `active` / `mastered` / `needs_review` = count of records whose `status`
  equals `active` / `mastered` / `needs_review` respectively. State each
  count.
- `average_score` = (sum of every record's `mastery.overall`) / (record
  count) / 5, rounded to exactly two decimal places. Show the sum, the
  count, and the resulting value.

Write out: "computed X, file says Y — match/mismatch" for each of the ten
values (5 fields × 2 mastery blocks). Any mismatch is a failure, even by
0.01 — do not round the check itself away.

## 4. Review-count check *(automated by `script/validate.py`)*
For every item listed in this Unit's `vocabulary.review` or `grammar.review`
that was actually practised in the session (not merely listed):

- Confirm its `review_count` in the index increased by exactly 1 compared to
  its value before this Unit.
- Confirm this Unit's id was appended to its `units` array.

List every reviewed item and its before/after `review_count`. An unchanged
`review_count` for a genuinely reviewed item is a failure.

## 5. Error Index completeness check *(structure automated; classification soundness is manual)*
Take every error mentioned in the "Errors" / "Errors reviewed" section of
`history/unit-XXX.md` and classify each one as exactly one of:

- **(a) Existing entry updated** — cite the `id`, confirm `last_seen`,
  `frequency`, `review_history`, and `status` were updated appropriately.
- **(b) New entry created** — cite the new `id` and confirm it has all
  required fields (`type`, `category`, `incorrect`, `correct`, `first_seen`,
  `last_seen`, `frequency`, `severity`, `status`, `related_grammar`,
  `review_history`, `next_review`).
- **(c) Explicitly excluded as non-trackable noise** — a one-line reason
  must appear in the history file itself (e.g. "one-off slip, not a pattern
  worth tracking"), decided at the time of writing history, not invented
  after the fact to excuse a missed update.

Any error mentioned in history that doesn't fall cleanly into (a), (b), or
(c) is a failure. This includes errors that only appear informally in
`learning_focus.errors` without a matching Error Index entry.

## 6. Vocabulary/collocation coverage check *(script WARNs candidates; final call is manual)*
For every collocation in this Unit's `collocations` list, confirm every
meaningful word in it appears in `vocabulary.core`, `vocabulary.supporting`,
or `vocabulary.review` of the same Unit, and (after this completion) has a
matching entry in `Vocabulary Index.json`. List any collocation word that
fails this.

## 7. Position/reference chain check *(automated by `script/validate.py`)*
- `last_completed_unit` equals this Unit's id.
- `next_unit` equals the correct next id per `Curriculum Memory.json`'s
  group/unit list — the next learning Unit, or the Group's review id if this
  was the last Unit in the group, or the Major Test id if this was the last
  Group Review in the level.
- No `current_position.unit` or `current_position.status` key exists.
- The newly created next Unit/review/test file's own `id` matches what
  `next_unit` points to, and its schema-appropriate `next_unit` field points
  correctly onward.

## 8. No-copy-forward / no-fabrication check *(best-effort automation via git history; confirm manually if git is unavailable)*
This check catches both failure directions seen in past executions:
- If an index file was **not modified** this completion, the corresponding
  central-state aggregate numbers must be **byte-identical** to their
  previous value — because nothing changed to recompute from. A changed
  aggregate number next to an unmodified index is fabrication.
- If an index file **was modified**, the corresponding aggregate numbers
  must differ from their previous value (unless the recomputed value
  genuinely happens to match, which should be rare) and must match §3's
  fresh recomputation, not the previous state's value copied forward.

## 9. Result table
Fill in explicitly before reporting completion to the user:

| # | Check | Result | Note |
|---|-------|--------|------|
| 1 | File-touch | PASS/FAIL | |
| 2 | Structural conformance | PASS/FAIL | |
| 3 | Recomputation (10 values) | PASS/FAIL | |
| 4 | Review-count | PASS/FAIL | |
| 5 | Error Index completeness | PASS/FAIL | |
| 6 | Vocabulary/collocation coverage | PASS/FAIL | |
| 7 | Position/reference chain | PASS/FAIL | |
| 8 | No-copy-forward/no-fabrication | PASS/FAIL | |

If every row is PASS, the Unit completion may be reported to the user. If
any row is FAIL, fix the underlying file(s) and re-run the whole checklist
before proceeding — do not patch a single number and skip re-verification
of the rest.
