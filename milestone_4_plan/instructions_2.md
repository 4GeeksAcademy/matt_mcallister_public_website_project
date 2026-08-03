Agent Infrastructure

Create the memory-bank/ folder at the root of the monorepo with at least the following files:

projectbrief.md — business description, project objectives, and the problem it solves
techContext.md — tech stack, architectural decisions made, and technical constraints
progress.md — current state of development and planned next steps


Create the AGENTS.md file at the root of the monorepo defining:

Which memory bank files the agent must read at the start of each session
The mandatory workflow before each commit (minimum 4 ordered, explicit steps)
The folders and files the agent must not modify without explicit developer confirmation


Create the .agents/ folder with at least one development rule documented with its scope (always active, file-pattern based, or agent-requested)
Implement at least one agent skill for a recurring workflow task, with:

A single, clearly defined objective
Documented inputs
Explicit and verifiable acceptance criteria