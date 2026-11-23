# Collaboration

Preserve the MIT upstream copyright and Git history. Work in review branches,
push ordinary review branches and create PRs. Do not push the default branch,
force push or merge. Keep machine state, transcripts and credentials out of Git.

This fork is a deliberately narrow Codex Desktop profile. Never add foreground
activation, global input, clipboard access, approval handling or automatic
message delivery. Use native Codex tools for thread lifecycle and messaging.
The desktop adapter must preserve all Codex-Window backend protection refusals.

Run `python -m unittest -v` and `python scripts/smoke.py --config <config.toml>`.
Smoke is read only and must not submit a prompt or change a live call.
Pin dependencies, review code and advisories, scan the deployed payload, verify
the exact registered command via MCP SDK. Do not restart Codex to test discovery.
No startup task is needed for stdio MCP. Preserve unrelated registrations.
Remove superseded installs only after verification and process/reference checks.
