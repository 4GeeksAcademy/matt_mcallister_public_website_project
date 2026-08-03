# AGENTS.md

## Memory Bank Files
Agents must read the following files at the start of each session:
- `memory-bank/projectbrief.md`
- `memory-bank/techContext.md`
- `memory-bank/progress.md`

## Mandatory Workflow Before Each Commit
1. Read the memory bank files to understand the project context.
2. Validate changes against the defined project objectives and constraints.
3. Run all tests to ensure no regressions.
4. Document changes in the `progress.md` file.

## Restricted Areas
Agents must not modify the following without explicit developer confirmation:
- Files in the `memory-bank/` folder.
- `AGENTS.md`.
- Any configuration files (e.g., `package.json`, `tsconfig.json`).