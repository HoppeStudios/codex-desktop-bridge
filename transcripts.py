"""Transcript reader adapted from agent-bridge (MIT, Marchellino Ghorayeb)."""
import json

def _text(content):
    if isinstance(content, str):
        return content
    return "\n".join(c.get("text", "") for c in content or []
                     if isinstance(c, dict) and c.get("type") in ("text", "input_text", "output_text"))


def _events(app, path, start=0):
    """Yield ('user', text) for messages a person (or this bridge) sent and ('end', final answer) per turn."""
    msg_id, parts, ending = None, [], False
    with open(path, "rb") as f:
        f.seek(start)
        for raw in f:
            try:
                o = json.loads(raw)
            except ValueError:  # partial line at the seek point or at the end
                continue
            if app == "codex":
                p = o.get("payload") or {}
                if o.get("type") == "response_item" and p.get("type") == "message" and p.get("role") == "user":
                    t = _text(p.get("content"))
                    if t.strip() and not t.lstrip().startswith(("<", "# AGENTS.md")):
                        yield "user", t
                elif o.get("type") == "event_msg" and p.get("type") == "thread_goal_updated":  # a /goal message
                    yield "user", "/goal " + ((p.get("goal") or {}).get("objective") or "")
                elif o.get("type") == "event_msg" and p.get("type") == "task_complete":
                    yield "end", p.get("last_agent_message") or ""
                elif o.get("type") == "event_msg" and p.get("type") == "turn_aborted":
                    yield "end", "(turn stopped before it finished)"
                continue
            # Claude writes one line per content block (thinking, text, ...) and every line of the final
            # message carries the end stop_reason, so the turn ends once a line from another entry follows.
            m, att = o.get("message") or {}, o.get("attachment") or {}
            if ending and (o.get("type") != "assistant" or m.get("id") != msg_id):
                ending = False
                yield "end", "\n".join(parts)
            if att.get("type") == "queued_command":  # a message sent while the session was busy, absorbed mid-turn
                yield "user", att.get("prompt") or ""
            elif o.get("type") == "user" and not o.get("isMeta"):
                t = _text(m.get("content"))
                if t.strip() and not t.lstrip().startswith("<"):
                    yield "user", t
            elif o.get("type") == "assistant":
                if m.get("id") != msg_id:
                    msg_id, parts = m.get("id"), []
                if t := _text(m.get("content")):
                    parts.append(t)
                ending = m.get("stop_reason") in ("end_turn", "stop_sequence", "max_tokens")
    if ending and parts:  # last thing in the file; only trust it once its text has been written
        yield "end", "\n".join(parts)
