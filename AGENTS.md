# Repository instructions

Follow [CONTRIBUTING.md](./CONTRIBUTING.md) for issues, pull requests,
local gates, and worktree commands. Use [REVIEWING.md](./REVIEWING.md)
for reviews, [ARCHITECTURE.md](./ARCHITECTURE.md) for package layers,
[README.md](./README.md) for scope and examples, and
[REPOSITORY.md](./REPOSITORY.md) before changing workflows or settings.
See [SECURITY.md](./SECURITY.md) for vulnerability reporting.

Keep the primary checkout clean and on `main`; use a separate worktree
for each task, following the setup and cleanup commands in
`CONTRIBUTING.md`.

Choose the least capable model that can reliably complete the task;
greater capability adds cost and latency when it cannot improve reliability.
Use a fast model for straightforward execution, a reasoning-focused model
for multi-step work, and the most capable available model for difficult
or ambiguous problems. Increase capability if progress stalls.
