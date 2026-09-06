# Study English Memory Skill

## 1. Purpose
This Skill is the execution layer for the user's long-term English learning system. 

## 2. Source of truth and directory roles
- `SKILL.md`: execution rules. It must not contain current learner state.
- `data/`: current state and indexes.
- `curriculum/`: actual lesson definitions. One JSON file per learning Unit.
- `history/`: actual AI-user conversation records for completed Units, stored as Markdown. There is intentionally no history template JSON.
- `tests/`: complete Group Review and Major Test records.
- `templates/`: schemas/templates only. They define structure and are not the learner's current data.
- `script/`: maintenance utilities such as repository reset.

## 3. Template rule
Every actual JSON file must conform to its corresponding template. Do not casually add, remove, rename, or repurpose properties. If the data model must change, update the template and increment `schema_version` first, then migrate affected data.

## 4. `Study English Memory.json`
### `schema_version`
Schema version of the central state file. System-managed; change only with a template/schema change.
### `profile`
Stable learning preferences and long-term target.
- `target`: target examination or outcome.
- `target_timeframe_years`: approximate target horizon.
- `english_variant`: preferred language variety.
- `learning_language`: language being learned.
- `explanation_language`: language used for explanations.
### `current_level`
Current estimated learning level. Updated only after diagnostic or formal assessment justifies a change.
### `current_position`
Where the learner is now.
- `group`: current curriculum group number.
- `unit`: current learning Unit number.
- `unit_type`: `learning`, `group_review`, or `major_test` as applicable.
- `status`: current lifecycle state, normally `not_started`, `in_progress`, or `completed`.
- `last_completed_unit`: latest completed Unit ID or null.
- `next_unit`: next scheduled Unit/test ID.
### `progress`
Compact cumulative counters. Detailed history belongs in `history/` and `tests/`.
### `vocabulary_mastery`
Aggregate vocabulary statistics derived from `data/Vocabulary Index.json`.
- `encountered`: unique encountered words.
- `active`: words currently expected for active use.
- `mastered`: words meeting mastery criteria.
- `needs_review`: words requiring review.
- `average_score`: aggregate mastery score.
### `grammar_mastery`
Aggregate grammar statistics derived from `data/Grammar Index.json`.
### `skills`
Current 0–5 estimates for grammar, vocabulary, reading, writing, listening, speaking, and output.
### `assessment`
Latest assessment summary. Full assessment records remain in `tests/`.
### `learning_focus`
Current adaptive focus: grammar topics, vocabulary and recurring errors needing attention.
### `system`
System lifecycle metadata.
- `initialized`: whether repository initialization has completed.
- `last_updated`: last state update date/time.
- `last_session`: last learning session date/time.

## 5. `Curriculum Memory.json`
This is the curriculum map, not lesson content.
- `curriculum.id`: stable curriculum identifier.
- `version`: curriculum version.
- `title`: human-readable name.
- `rules.learning_units_per_group`: number of learning Units in each Group.
- `rules.group_review_after_units`: review cadence.
- `rules.major_test_after_groups`: major-test cadence.
- `levels`: ordered proficiency levels.
- Each level contains Groups; each Group lists Unit IDs and its review ID.

The curriculum numbering is stable. A weak result must increase reinforcement; it must not silently renumber or replace existing Units.

## 6. `Vocabulary Index.json`
One record per vocabulary item.
- `word`: canonical word/lexeme.
- `first_unit`: first Unit where it was intentionally introduced.
- `units`: Units where it was encountered or reviewed.
- `status`: learning state such as `active`, `mastered`, or `needs_review`.
- `mastery.recognition`: ability to recognise the word.
- `mastery.meaning`: ability to understand its meaning in context.
- `mastery.usage`: ability to use it correctly.
- `mastery.overall`: aggregate mastery.
- `encounter_count`: total meaningful encounters.
- `review_count`: deliberate reviews.
- `collocations`: important natural word combinations.
- `common_errors`: recurring learner errors.
- `last_reviewed`: latest review date.

Recognition and usage are deliberately separate. A recognised word is not automatically an active word.

## 7. `Grammar Index.json`
One record per grammar topic.
- `topic`: canonical grammar topic name.
- `first_unit`: first intentional introduction.
- `units`: Units where it was taught/reviewed.
- `status`: learning state.
- `mastery.recognition`: ability to identify the pattern.
- `mastery.formation`: ability to form it correctly.
- `mastery.usage`: ability to select/use it correctly in context.
- `mastery.output`: ability to produce it independently.
- `mastery.overall`: aggregate mastery.
- `encounter_count`: meaningful encounters.
- `review_count`: deliberate reviews.
- `common_errors`: recurring errors.
- `last_reviewed`: latest review date.

Previously learned grammar must be labelled as review/reinforcement/mastery check, not falsely introduced as new.

## 8. `Error Index.json`
Tracks recurring errors so future practice can target them.
- `id`: stable error ID.
- `type`: grammar, vocabulary, collocation, spelling, etc.
- `category`: normalised error category.
- `incorrect`: learner production.
- `correct`: corrected form.
- `first_seen` / `last_seen`: Unit IDs.
- `frequency`: number of observed occurrences.
- `severity`: relative impact, normally low/medium/high.
- `status`: e.g. `needs_review`, `improving`, `resolved`.
- `related_grammar`: linked grammar topics.
- `review_history`: Units where the error was deliberately reviewed.
- `next_review`: planned review Unit.

## 9. `curriculum-unit.json`
Defines one actual learning Unit.
- `unit`: identity, level, Group, number, type, title and overview.
- `objectives`: measurable learning objectives.
- `grammar.new`: genuinely new grammar only.
- `grammar.review`: existing grammar intentionally reviewed.
- `grammar.focus`: aspects receiving special attention.
- `vocabulary.theme`: semantic theme.
- `vocabulary.core`: active/core target words.
- `vocabulary.supporting`: supporting vocabulary.
- `vocabulary.review`: previously indexed words used for review.
- `collocations`: target collocations.
- `sentence_patterns`: reusable patterns.
- `lesson_flow`: required instructional sequence.
- `practice`: grammar/vocabulary/output activities.
- `assessment`: Unit assessment definitions.
- `completion_criteria.minimum_understanding`: minimum understanding ratio.
- `completion_criteria.minimum_output`: minimum output ratio.
- `next_unit`: scheduled next Unit ID.

A Unit should normally move from controlled recognition to guided output, independent output, and communicative output.

## 10. `test.json`
Used for Group Reviews and Major Tests.
- `test`: identity, type, scope and status.
- `assessment`: category scores and overall score.
- `analysis`: strengths, weaknesses and errors.
- `decision.pass`: whether requirements were met.
- `decision.next_action`: concrete next learning action.
- `decision.recommended_level`: level recommendation based on evidence.

Full test records stay in `tests/`. `Study English Memory.json` keeps only the latest/current summary needed for execution.

## 11. Vocabulary architecture
Each learning Unit should normally expose roughly 30–50 useful words through a mixture of:
- 15–20 active/core targets;
- 10–20 supporting words;
- 10–20 exposure/review words;
- about 5–10 important collocations.

Exact counts may vary according to the Unit. Do not force artificial vocabulary volume.

## 12. Deduplication
Before adding new vocabulary or grammar:
1. Read the relevant index.
2. If the item already exists, treat it as review/reinforcement/exposure unless there is a legitimate new sense or substantially new grammatical use.
3. Update the existing index record rather than creating a duplicate.
4. Do not mark an item as mastered merely because it was recognised.

## 13. Adaptive learning
Use `Error Index.json`, vocabulary usage scores and grammar output scores to choose practice intensity. A weak test does not rewrite the curriculum; it increases targeted reinforcement within the stable curriculum.

## 14. Starting a session
1. Read `data/Study English Memory.json`.
2. Validate that required properties exist and match the template.
3. Read the current `curriculum/unit-XXX.json` or current review/test file.
4. Read the relevant vocabulary, grammar and error indexes.
5. Teach the current Unit according to its flow.

For first-time initialization, establish the learner's level through diagnostic evidence before treating a level as final. Preserve known historical learning as prior knowledge.

## 15. Unit completion and history rule
The AI may decide that the Unit has met its completion criteria, but it must ask the user whether they want to end the Unit. Do not write `history/unit-XXX.md` before explicit user confirmation such as `结束`, `完成`, or equivalent confirmation.

After confirmation:
1. Write the actual AI-user Unit conversation to `history/unit-XXX.md`.
2. Append a concise final assessment/error section if useful, while preserving the dialogue itself as the primary record.
3. Update the central state and all relevant indexes.
4. Update progress and current position.
5. Apply Group Review or Major Test scheduling rules when the milestone is reached.
6. Design/save the next Unit when appropriate.

## 16. History format
`history/` has no JSON template. Each file is Markdown and is named exactly `unit-XXX.md`. It records the actual conversation for that Unit, not merely a summary. It should contain enough detail to reconstruct exercises, learner answers, corrections and assessment.

## 17. Review cadence
- Four learning Units form one Group.
- After Unit 4, 8, 12, etc., run the corresponding Group Review.
- After four Groups / twenty learning Units, run a Major Test.
- Reviews diagnose weak areas and feed the Error Index and mastery indexes.

## 18. Maintenance and validation
Do not edit files outside their defined role. Keep `data/Study English Memory.json` compact. Do not store full conversation history, full vocabulary lists, or full test details in the central state file.

Before committing updates, validate:
- JSON is syntactically valid.
- `schema_version` exists and matches its template.
- IDs and Unit references are consistent.
- Vocabulary/grammar duplicates are merged.
- History is not written early.
- Current position agrees with progress.
- Review/test scheduling agrees with curriculum rules.
