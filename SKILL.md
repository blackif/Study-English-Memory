---
name: study-english-memory
description: Execution layer for the user's personal, long-term, curriculum-based English learning program. Tracks current level, unit progress, vocabulary/grammar mastery and recurring errors as JSON state across sessions in data/, curriculum/, history/, tests/. Use this skill whenever the user wants to continue or start an English lesson/Unit, asks about mastery/progress/errors, wants a Group Review or Major Test, wants to end a Unit, or wants to reset/reinitialize the repository.
---

# Study English Memory Skill

## 1. Purpose
This Skill is the execution layer for the user's long-term curriculum-based English learning system.

## 2. Source of truth and directory roles
- `SKILL.md`: execution rules; never store current learner state here.
- `data/`: current state and indexes.
- `curriculum/`: actual lesson definitions; one JSON file per learning Unit.
- `history/`: completed Unit conversation records in Markdown.
- `tests/`: Group Review and Major Test records.
- `templates/`: schemas/templates only.
- `script/`: maintenance utilities such as repository reset.

## 3. Schema and migration rule
Every actual JSON file must conform to its corresponding template. Do not casually add, remove, rename, or repurpose properties. If the data model changes, update the template and increment its `schema_version`, then migrate affected data before continuing.

Central-state schema `1.2` changes:
- Remove `current_position.unit`; the current Unit is represented by `next_unit`, while `last_completed_unit` records the completed Unit.
- Remove `current_position.status`; lifecycle status is redundant because current position, last completed Unit, history and next Unit provide the necessary state.
- Rename `vocabulary_mastery.encountered` to `vocabulary_mastery.introduced` so vocabulary and grammar use the same concept/field name.

## 4. Central state rules
`data/Study English Memory.json` contains compact execution state only.
- `current_position` contains `group`, `unit_type`, `last_completed_unit`, and `next_unit` only.
- `vocabulary_mastery` and `grammar_mastery` are derived summaries, never independently authored estimates.
- `introduced`: number of unique records in the corresponding index.
- `active`: number of records whose index `status` is `active`.
- `mastered`: number of records whose index `status` is `mastered`.
- `needs_review`: number of records whose index `status` is `needs_review`.
- `average_score`: arithmetic mean of `mastery.overall` across all index records, divided by 5 and rounded to two decimals. If there are no records, use 0.
- Never infer `mastered` from a score alone.
- A vocabulary/grammar record with `encounter_count == 0` must not be assigned a full mastery score. Its mastery must reflect the evidence actually obtained; unencountered newly introduced vocabulary should remain at the baseline mastery value until exercised.
- Before every state update, recompute all aggregate fields directly from the indexes.

## 5. Vocabulary Index
One record per vocabulary item. Use `word`, `first_unit`, `units`, `status`, `mastery`, encounter/review counts, collocations, common errors and last review date.
- Recognition, meaning and usage are separate dimensions.
- A recognised word is not automatically mastered.
- Existing items are review/reinforcement, not new vocabulary, unless a legitimate new sense/use is introduced.
- Whenever a Unit explicitly places an existing vocabulary item in `vocabulary.review` and that item is actually practised/reviewed, increment its `review_count` and include the Unit in `units`.
- Do not give full mastery to vocabulary that was listed but never actually encountered or exercised.

## 6. Grammar Index
One record per grammar topic with `topic`, `first_unit`, `units`, `status`, mastery dimensions, encounter/review counts, common errors and last review date.
- Previously learned grammar must be labelled as review/reinforcement/mastery check, not falsely introduced as new.
- When a Unit explicitly reviews an existing grammar topic and the topic is actually practised, increment `review_count` and include the Unit in `units`.
- Central-state `mastered` is derived strictly from index `status`, not from `mastery.overall`.

## 7. Curriculum Unit rules
Each learning Unit must define grammar, vocabulary, collocations, sentence patterns, lesson flow, practice, assessment and `next_unit` according to `templates/curriculum-unit.json`.
- `vocabulary.core`: active target vocabulary.
- `vocabulary.supporting`: supporting vocabulary that should appear in examples/exercises.
- `vocabulary.review`: previously indexed vocabulary intentionally reviewed.
- Every vocabulary item used as a deliberate target in a Unit, including meaningful words appearing in target collocations such as `watch TV`, must appear in `core`, `supporting`, or `review` and be represented in Vocabulary Index after completion.
- Do not create a collocation containing a meaningful target word absent from all three vocabulary lists.

## 8. Session opening vocabulary protocol
At the beginning of every learning Unit, after reading the Unit and indexes, explicitly show a compact vocabulary preview before teaching:
1. Core vocabulary.
2. New supporting vocabulary not already in the index.
3. Review vocabulary, clearly labelled as review.
4. Important collocations.
5. Chinese meanings may be provided, while examples and exercises continue to use English.
The preview is instructional: every listed item must either be used in the lesson or explicitly marked as preview-only; preview-only items must not receive mastery credit.

## 9. Starting a session
1. Read central state and validate it against its template/schema.
2. Read the current Unit/review/test file.
3. Read Vocabulary, Grammar and Error indexes.
4. Display the Session Opening Vocabulary Preview defined in §8.
5. Teach according to the Unit's `lesson_flow`.
6. Adapt practice intensity using errors and mastery dimensions.

For first-time initialization, establish level through diagnostic evidence and preserve known prior learning.

## 10. Unit completion and next-Unit generation
The AI may determine that completion criteria are met, but must ask the user whether they want to end the Unit. Do not write history before explicit confirmation such as `结束` or `完成`.

After confirmation, execute these steps in order:
1. Write `history/unit-XXX.md` with enough detail to reconstruct the learner interaction, exercises, answers, corrections and assessment, including all meaningful errors observed during the Unit.
2. Update Vocabulary, Grammar, and **Error** indexes. Error Index update is mandatory, not optional. Record recurring/meaningful grammar, vocabulary, spelling, word-choice, preposition, subject or other errors with frequency, severity/status, related topics, review history and `next_review` according to the Error Index schema.
3. For every item intentionally reviewed in the Unit, increment `review_count` exactly once when the review actually occurred; do the same for reviewed grammar topics.
4. Recompute central-state aggregate statistics directly from the indexes. Do not copy or estimate prior values. `average_score` must be the arithmetic mean of index `mastery.overall` divided by 5 and rounded to exactly two decimal places.
5. Update progress and current position. `current_position` must contain no `unit` or `status` property.
6. Apply Group Review/Major Test scheduling rules.
7. **Create/save the next scheduled learning Unit JSON immediately after a learning Unit is completed**, unless the next scheduled item is a review/test file that already exists. This is mandatory, not optional planning.
8. Validate all changed JSON and cross-file references before finishing, including Error Index consistency and review counts.

The next Unit must be defined even though it has not yet been taught. Creating it does not start the Unit or advance the learner into it.

## 11. History
`history/unit-XXX.md` is Markdown and should preserve the actual conversation as the primary record, with a concise assessment/error section if useful.

## 12. Vocabulary architecture
A learning Unit normally exposes roughly 30–50 useful items through core, supporting and review vocabulary plus about 5–10 important collocations. Exact counts may vary; do not force artificial volume.

## 13. Adaptive learning
Use Error Index, vocabulary usage scores and grammar output scores to choose reinforcement. Errors with `status == needs_review` or repeated frequency must receive targeted reinforcement at their scheduled review. Weak results increase targeted reinforcement; they do not silently renumber or replace curriculum Units.

## 14. Review cadence
- Four learning Units form one Group.
- After Units 4, 8, 12, etc., run the corresponding Group Review.
- After four Groups / twenty learning Units, run a Major Test.

## 15. Validation checklist
Before committing any lesson-state change, validate:
- JSON syntax is valid.
- `schema_version` matches its template.
- Central-state `introduced/active/mastered/needs_review/average_score` values exactly match index data.
- `average_score` is rounded to two decimal places.
- `mastered` counts come only from index `status == mastered`.
- `current_position` contains exactly `group`, `unit_type`, `last_completed_unit`, and `next_unit`.
- No `current_position.unit` or `current_position.status` exists.
- Unit IDs and `next_unit` references exist and agree with the curriculum map.
- Every deliberate target vocabulary item is represented in the Unit vocabulary lists and Vocabulary Index.
- No duplicate vocabulary/grammar records.
- Every intentionally reviewed vocabulary/grammar item has its `review_count` incremented exactly once for the Unit.
- Every meaningful observed learner error is represented in Error Index or explicitly documented as non-trackable noise.
- Error Index entries have valid `next_review` scheduling.
- History is not written before explicit completion confirmation.
- Review/test scheduling matches curriculum rules.

## 16. Repository reset (`script/ini.py`)
`script/ini.py` is destructive and human-run. The AI must not invoke it automatically. It deletes `data/`, `curriculum/`, `history/`, and `tests/`, preserves `templates/`, `script/`, and `SKILL.md`, and requires the operator to type `RESET`. After reset, reinitialize required data files from templates and recreate `curriculum/unit-001.json` before teaching begins.
