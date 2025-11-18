# Team Checklist (OpenSpec)

In this project, every change follows spec-first development.

## Rules
1. Don't code first. Write/adjust specs first.
2. AI implements only what specs + tasks state.
3. After merge/release, archive the change to sync truth.

## Minimal Workflow
- Explore: `openspec list --specs` and `openspec list`
- Draft change: choose verb-led change-id (kebab-case)
- Create proposal + tasks + spec deltas under `openspec/changes/<id>/`
- Validate: `openspec validate <id> --strict`
- Implement strictly by `tasks.md` (one task at a time)
- Tests reflect scenarios from specs
- Archive: `openspec archive <id> --yes`

## Scenario Writing Tips
- Each `### Requirement:` must include ≥1 `#### Scenario:`
- Prefer testable GIVEN/WHEN/THEN phrasing
- Include happy path, validation errors, timeouts, and fallbacks
