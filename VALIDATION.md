# Unit Completion Validation Checklist

## Purpose
This is a mandatory gate, not a suggestion. It must be run **every time** a
learning Unit, Group Review, or Major Test is completed — after the
completion steps in `SKILL.md` §10 have been drafted, and **before** telling
the user the Unit is done or moving on to the next one.

Every check below must be answered with an actual computed value or an
explicit diff, not a general impression like "looks consistent". If any
check fails, go back and fix the underlying file — do not report completion
with a known failing check.

Run this checklist yourself as the AI executing the skill. Show your work
(the numbers, the diff) inline as you go, then end with the PASS/FAIL table
in §10.

---

## 1. File-touch check
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
      observed" (see §6). An unmodified Error Index alongside a history file
      that lists errors is always a failure.
- [ ] `curriculum/unit-(N+1).json` (or the scheduled review/test file)
      created, unless it already exists.
- [ ] `data/Study English Memory.json` — modified.

If any expected file is missing from the diff, stop here and fix it before
continuing to the next sections — the recomputation checks below are
meaningless if the underlying index wasn't actually touched.

## 2. Structural conformance check
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

## 3. Recomputation check (show the arithmetic)
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

## 4. Review-count check
This check is broader than "items the curriculum file happens to label
`review`". It applies to **every** record in `Vocabulary Index.json` and
`Grammar Index.json`, regardless of which bucket (`core`/`new`,
`supporting`, `review`) the current Unit's curriculum file put it in, and
even if the current Unit's curriculum file doesn't mention it at all (e.g.
a word the learner used spontaneously that still got added to the index).

The rule is a simple, checkable invariant:

> For every record, `review_count` must equal `len(units) - 1`.

Reasoning: the first entry in `units` is when the item was introduced; every
later entry is, by definition, a moment the item was encountered again in a
completed Unit -- which is what `review_count` is supposed to be counting.
It does not matter whether the curriculum file tagged that word `review`,
`supporting`, or didn't mention it at all -- if `units` grew, `review_count`
must grow with it.

For every record whose `units` array includes this Unit's id, confirm:
- `review_count` now equals `len(units) - 1` exactly (not just "increased").
- This Unit's id appears in `units` at most once.

List every such record with its `units` array and `review_count`, and mark
mismatches explicitly -- do not eyeball it, count the array length.

## 5. Vocabulary/grammar re-introduction check
For every item in this Unit's `vocabulary.core` (or `grammar.new`), check
whether a record for it **already exists** in `Vocabulary Index.json` /
`Grammar Index.json` from an earlier Unit.

- If no prior record exists, the item is genuinely new -- fine as-is.
- If a prior record exists, this item must **not** stay in `core`/`new`.
  Move it to `vocabulary.review` / `grammar.review` in the curriculum file,
  unless the Unit is deliberately introducing a distinct new sense or use of
  the word/topic -- in which case write a one-line justification in the
  Unit's `overview` or `objectives` explaining what is new about it (e.g. a
  word gaining a new grammatical role, not just being repeated).

An existing item silently left in `core`/`new` with no such justification is
a failure: it mislabels review material as new material, which both
misleads the learner about what's actually new this Unit and would let it
skip the review bookkeeping in §4.

## 6. Error Index completeness check
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

## 7. Vocabulary/collocation coverage check
For every collocation in this Unit's `collocations` list, confirm every
meaningful word in it appears in `vocabulary.core`, `vocabulary.supporting`,
or `vocabulary.review` of the same Unit, and (after this completion) has a
matching entry in `Vocabulary Index.json`. List any collocation word that
fails this.

Note the boundary with §5: a word the learner used spontaneously, outside
anything planned in the curriculum file, does not need to be retrofitted
into that Unit's vocabulary lists just because it ended up in the index —
the curriculum file describes what the Unit intended to teach, not
everything the learner happened to say. This check is only about words that
appear inside the Unit's own planned `collocations`.

## 8. Position/reference chain check
- `last_completed_unit` equals this Unit's id.
- `next_unit` equals the correct next id per `Curriculum Memory.json`'s
  group/unit list — the next learning Unit, or the Group's review id if this
  was the last Unit in the group, or the Major Test id if this was the last
  Group Review in the level.
- No `current_position.unit` or `current_position.status` key exists.
- The newly created next Unit/review/test file's own `id` matches what
  `next_unit` points to, and its schema-appropriate `next_unit` field points
  correctly onward.

## 9. No-copy-forward / no-fabrication check
This check catches both failure directions seen in past executions:
- If an index file was **not modified** this completion, the corresponding
  central-state aggregate numbers must be **byte-identical** to their
  previous value — because nothing changed to recompute from. A changed
  aggregate number next to an unmodified index is fabrication.
- If an index file **was modified**, the corresponding aggregate numbers
  must differ from their previous value (unless the recomputed value
  genuinely happens to match, which should be rare) and must match §3's
  fresh recomputation, not the previous state's value copied forward.

## 10. Result table
Fill in explicitly before reporting completion to the user:

| # | Check | Result | Note |
|---|-------|--------|------|
| 1 | File-touch | PASS/FAIL | |
| 2 | Structural conformance | PASS/FAIL | |
| 3 | Recomputation (10 values) | PASS/FAIL | |
| 4 | Review-count invariant (all records) | PASS/FAIL | |
| 5 | Vocabulary/grammar re-introduction | PASS/FAIL | |
| 6 | Error Index completeness | PASS/FAIL | |
| 7 | Vocabulary/collocation coverage | PASS/FAIL | |
| 8 | Position/reference chain | PASS/FAIL | |
| 9 | No-copy-forward/no-fabrication | PASS/FAIL | |

If every row is PASS, the Unit completion may be reported to the user. If
any row is FAIL, fix the underlying file(s) and re-run the whole checklist
before proceeding — do not patch a single number and skip re-verification
of the rest.
