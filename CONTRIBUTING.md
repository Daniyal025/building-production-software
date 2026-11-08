# Contributing

This plugin improves when engineers on other stacks and domains report where a rule helped, misled or was missing.

## Most useful contributions
1. **Rule feedback** (issue template "Rule feedback"). Tell us about a rule that was wrong, over-strict, in the wrong tier, or missing. Name your stack and tier.
2. **Real cases.** Rules marked *Source* come from industry practice. A real failure you saw (anonymised) makes a rule far more persuasive.
3. **Eval scenarios** (issue template "Eval scenario"). Tasks that separate strong answers from weak ones, especially ones that reward proportionality.
4. **Stack equivalents** for languages and databases we don't cover yet.

## Format of a rule
Each rule in `skills/*/references/*.md`:
- has a **checklist line** tagged `T1`, `T2` or `T3`;
- has 1–4 imperative bullets;
- has **Why**, then either **Real case** (something that happened) or **Source** (a named, checkable reference), then **Look up** (the concept name).

The tier is the cheapest correct one. If a rule only pays off with money, personal data, several teams or an AI that writes data, it is T3.

## Changing rules or evals
- Template changes must keep `skills/production-backend-and-data/templates/tests` green. CI runs them against Postgres.
- Don't tune rule text toward an eval rubric. Rubrics are written blind to the skills, and that is the point. If a rubric item seems wrong, open an issue about the rubric.
- Re-run the evals (`evals/v2/README.md`) when you change rules, and report the results honestly, regressions included.
