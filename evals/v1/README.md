# Evals

How this skill was tested, following the "no skill without a failing test" method: run the task without the skill, run it with the skill, and compare.

- `rubric.md`: 12 scoring items per scenario, fixed before the with-skill answers were read.
- `baseline/`: answers with no skill.
- `with-skill/`: answers with the skill.
- `results.md`: scores, what changed, cost and limits.

## Prompts

**S1.** We're adding a feature to an existing FastAPI + Postgres app: an LLM assistant can propose changing a product's price, and an admin confirms in chat. Prices must keep history. Plan the database change, the API route, the agent tool and the tests. Keep the plan to ~25 bullets.

**S2.** Add a nightly job to a Python + Postgres app that downloads a central bank's daily exchange-rate CSV and stores the rates. The bank sometimes revises past days and occasionally changes the CSV layout. Plan the schema, the job, the tests, and how we'll know if it breaks. Keep it to ~20 bullets.

**S3.** I finished a feature on a branch that is 3 weeks old. Two other branches are stacked on top of it, and main has moved 60 commits since. My tests pass locally, the feature adds one database migration, and a timing test showed the page got 40% faster. The feature also renames a few helper functions I touched. What exactly should I do before asking for review, and what should the PR description contain? Keep it to ~15 bullets.

Baseline runs were told: *"Answer from your own knowledge only. Do not read, search or create any files and do not use any skills."*

With-skill runs were told: *"You have a skill available at `<path>/SKILL.md`. Read it first and follow its 'How to use' steps."*
