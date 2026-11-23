# Upstream and scope

This is an MIT fork of https://github.com/MarchGho/agent-bridge at
`f333caf31fd02dfdf5da3e893a5c08ccf09cb6b6` (verify the full upstream commit
with `git rev-parse origin/main` before the initial review).

The upstream server targets actual Windows Codex and Claude desktop chats.
Its desktop send path uses foreground activation and a clipboard/keyboard
fallback. Detached watchers can type replies into another desktop chat.
Those paths and Claude CLI execution are absent from this installed profile.
The retained transcript parser remains attributed to the upstream author.

The alternative aresyn/codex-control-plane-mcp was reviewed at
`a0756b4` for comparison. Its worker launches a separate `codex app-server`
process. That offers orchestration, but does not establish control of the
existing visible desktop window. It was not installed for this request.

This fork uses the existing reviewed Codex-Window PC-Control backend for
guarded background UI operations. It does not patch Codex, enable a debugging
port, change authentication, or grant authority to operate unrelated chats.
