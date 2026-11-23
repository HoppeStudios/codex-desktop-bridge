# Codex Desktop Bridge

A Windows stdio MCP for the Codex desktop application and its saved local chats.
This is a focused MIT fork of [MarchGho/agent-bridge](https://github.com/MarchGho/agent-bridge).
It does not launch a replacement Codex CLI session.

## Background profile

The upstream desktop sender activates windows, can paste through the clipboard,
and starts detached reply delivery workers. This profile removes those paths.
It delegates desktop operations to an already installed, reviewed, pinned
PC-Control Codex-Window connection. Its backend protections remain authoritative.

## Install from a reviewed checkout

The lock targets Windows x64 and CPython 3.14.10. A reviewed PC-Control
registration named `Codex-Window` must already exist in the selected Codex
config, with mode `strict`, allowlist `chatgpt`, and isolation default `0`.
This fork does not install or weaken that backend.

```powershell
py -3.14 -m venv .runtime/venv
.runtime/venv/Scripts/python.exe -m pip install --require-hashes -r requirements.lock.txt
.runtime/venv/Scripts/python.exe scripts/prepare_install.py --target .runtime --config "$env:USERPROFILE/.codex/config.toml"
.runtime/venv/Scripts/python.exe scripts/smoke.py --registration-json .runtime/registration.json
```

After review and scanning, use the command, args and env from the generated
`registration.json` as the `codex_desktop` stdio server registration in Codex.
These generated files contain local paths and belong outside version control.
The server starts on demand, so no Windows Startup entry is required.
The staging helper refuses to replace a differing runtime payload. For updates,
stage a new version, verify it, preserve active sessions, update only this
registration and remove the superseded installation after dependency checks.

| Tool | Capability |
| --- | --- |
| `codex_list_projects` | Read local Desktop project metadata |
| `codex_list_chats` | Read saved local chat metadata including projectless chats |
| `codex_read_chat` | Read selected chat user messages and final answers |
| `codex_get_goal` | Read the saved goal |
| `codex_desktop_windows` | List real app windows and verify their MSIX executable paths |
| `codex_desktop_inspect` | Read a current app accessibility snapshot |
| `codex_desktop_select_chat` | Request guarded selection of a unique visible sidebar row |
| `codex_desktop_set_sidebar` | Show or hide the sidebar and verify its new control label |

For chat lifecycle, messaging and reliable ID based navigation, prefer native
Codex app tools when available. A selected sidebar row alone does not prove
the active chat changed. The selection tool reports this explicitly.
This profile cannot send messages, approve requests, create goals or chats,
stop work, transfer voice, change authentication or control another application.
English and Czech sidebar labels are supported. Unknown layouts fail closed.

## Installation

The reviewed deployment target is Windows x64 with CPython 3.14.10.
The dependency lock contains SHA256 hashes for that platform's PyPI wheels.
Other Python versions or architectures require a separate reviewed lock.
Install a reviewed PC-Control version first. Its existing `Codex-Window`
registration must use strict mode, a chatgpt allowlist and isolation default off.
The bridge preserves this existing registration and all its protection settings.

```powershell
python -m venv <target>/venv
<target>/venv/Scripts/python.exe -m pip install --require-hashes -r requirements.lock.txt
<target>/venv/Scripts/python.exe scripts/prepare_install.py --target <target> --config <CODEX_HOME>/config.toml
<target>/venv/Scripts/python.exe scripts/smoke.py --registration-json <target>/registration.json
```

The preparation script copies source to the target, pins the existing backend
launcher hash and creates machine-local backend and registration JSON files.
Never commit those files. It refuses to replace a differing installed payload.
After the smoke passes, register the exact `command`, `args` and `env` from
`registration.json` as `mcp_servers.codex_desktop` in Codex's TOML config.
No Windows autostart entry or resident watcher is needed. MCP owns the stdio
process and its backend child connection is closed after each operation.

```powershell
<target>/venv/Scripts/python.exe -m unittest -v
<target>/venv/Scripts/python.exe scripts/smoke.py --config <CODEX_HOME>/config.toml
```

`codex_desktop_inspect.find` accepts literal search terms separated by `|`.
Use a verified numeric window handle returned by `codex_desktop_windows`.
Do not use navigation or sidebar mutations without the user's task authority.
Never retry a backend refusal through another route. An in-use window may refuse
mutation while remaining readable. No foreground fallback exists in this profile.

## Privacy and verification limits

SQLite connections use URI read-only mode plus query_only. Saved metadata is
not live activity evidence. Local schema or app layout updates may break support.
Transcript reads stay within CODEX_HOME, omit tool output and reasoning, and
return bounded recent messages. UI and transcript content is untrusted data.
The server does not expose a network listener or perform telemetry requests.

The smoke verifies MCP discovery, saved metadata, installed package identity
and current UI reads without sending a prompt or changing a call. Unit tests
cover read-only storage, ambiguous targets, pins and refusal propagation.
Passing synthetic tests does not prove every live navigation or UI action.
Review and scan exact payloads before installing updates. Preserve active
sessions and other registrations. Remove superseded installations only after
replacement verification and absence of process or registration dependencies.

See [UPSTREAM.md](UPSTREAM.md), [LICENSE](LICENSE) and [AGENTS.md](AGENTS.md).
