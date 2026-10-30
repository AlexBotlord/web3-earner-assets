#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Minimal MCP client for the Agent Bounty Feed.

Talks to the public Model Context Protocol server over Streamable HTTP
(JSON-RPC 2.0) using nothing but the Python standard library: no pip install,
no API key, no account.

Server: https://agent-bounty-feed.dailydollar.workers.dev/mcp
Feed:   https://dailydollar-bot.github.io/agent-bounty-feed/feed.json

Usage:
    python mcp_client.py                      # list open bounties (default)
    python mcp_client.py --limit 3            # list at most 3 bounties
    python mcp_client.py --tool get_feed_stats
    python mcp_client.py --tool get_bounty --arg id=frantic:142
    python mcp_client.py --tools              # print the server tool list
    python mcp_client.py --raw                # dump the raw JSON result

Exit codes: 0 = ok, 1 = transport/protocol error, 2 = bad arguments.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request

DEFAULT_URL = "https://agent-bounty-feed.dailydollar.workers.dev/mcp"
PROTOCOL_VERSION = "2025-06-18"
CLIENT_INFO = {"name": "agent-bounty-feed-minimal-client", "version": "1.0.0"}
TIMEOUT = 45


# --------------------------------------------------------------------------- #
# Transport: Streamable HTTP (POST JSON-RPC, response is JSON or SSE)
# --------------------------------------------------------------------------- #
class McpHttp:
    """One MCP session over Streamable HTTP."""

    def __init__(self, url: str, verbose: bool = False) -> None:
        self.url = url
        self.verbose = verbose
        self.session_id = None      # set from the Mcp-Session-Id response header
        self.protocol_version = None
        self._next_id = 0

    def _headers(self):
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "User-Agent": "agent-bounty-feed-minimal-client/1.0",
        }
        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id
        if self.protocol_version:
            headers["MCP-Protocol-Version"] = self.protocol_version
        return headers

    def _post(self, payload):
        """POST one JSON-RPC message; returns (http_status, rpc_message_or_None, raw_body)."""
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(self.url, data=data, headers=self._headers(), method="POST")
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                status = resp.status
                sid = resp.headers.get("Mcp-Session-Id")
                if sid:
                    self.session_id = sid
                body = resp.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as exc:  # 4xx/5xx can still carry a JSON-RPC error
            status = exc.code
            body = exc.read().decode("utf-8", "replace")
            sid = exc.headers.get("Mcp-Session-Id") if exc.headers else None
            if sid:
                self.session_id = sid
        if self.verbose:
            sys.stderr.write("[http] %-26s -> %s (%d bytes)\n"
                             % (payload.get("method"), status, len(body)))
        return status, _parse_body(body), body

    def _request(self, method, params=None):
        self._next_id += 1
        payload = {"jsonrpc": "2.0", "id": self._next_id, "method": method}
        if params is not None:
            payload["params"] = params
        status, msg, body = self._post(payload)
        if msg is None:
            raise RuntimeError("%s: empty or unparsable response (HTTP %s): %r"
                               % (method, status, body[:300]))
        if "error" in msg:
            err = msg["error"] or {}
            raise RuntimeError("%s: JSON-RPC error %s: %s"
                               % (method, err.get("code"), err.get("message")))
        return msg.get("result") or {}

    def _notify(self, method):
        self._post({"jsonrpc": "2.0", "method": method})   # server answers 202, no body

    # -- MCP handshake and calls ------------------------------------------- #
    def initialize(self):
        result = self._request("initialize", {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {},
            "clientInfo": CLIENT_INFO,
        })
        self.protocol_version = result.get("protocolVersion") or PROTOCOL_VERSION
        self._notify("notifications/initialized")
        return result

    def list_tools(self):
        return self._request("tools/list").get("tools") or []

    def call_tool(self, name, arguments=None):
        return self._request("tools/call", {"name": name, "arguments": arguments or {}})


def _parse_body(body):
    """Accept a plain JSON body or an SSE stream (`event: message` + `data: {...}`)."""
    text = (body or "").strip()
    if not text:
        return None
    if text.startswith("{"):
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return None
    message = None
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("data:"):
            continue
        chunk = line[5:].strip()
        if not chunk or chunk == "[DONE]":
            continue
        try:
            parsed = json.loads(chunk)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict) and ("result" in parsed or "error" in parsed):
            message = parsed      # keep the last complete JSON-RPC message
    return message


# --------------------------------------------------------------------------- #
# Presentation helpers
# --------------------------------------------------------------------------- #
def tool_payload(result):
    """Unwrap a tools/call result into plain Python data.

    MCP servers return either `structuredContent` (already an object) or a
    `content` array whose text parts carry the JSON payload as a string.
    """
    if isinstance(result.get("structuredContent"), (dict, list)):
        return result["structuredContent"]
    parts = []
    for item in result.get("content") or []:
        if isinstance(item, dict) and item.get("type") == "text":
            parts.append(item.get("text") or "")
    joined = "\n".join(parts).strip()
    if not joined:
        return {}
    try:
        return json.loads(joined)
    except json.JSONDecodeError:
        return {"text": joined}


def pick(obj, *names, **kwargs):
    """First present, non-empty field among `names`."""
    default = kwargs.get("default")
    for name in names:
        value = obj.get(name)
        if value not in (None, "", [], {}):
            return value
    return default


def find_bounties(data):
    """Locate the list of bounty objects inside an arbitrary feed payload."""
    if isinstance(data, list):
        return data
    if not isinstance(data, dict):
        return []
    for key in ("items", "bounties", "data", "results", "feed"):
        value = data.get(key)
        if isinstance(value, list):
            return value
        if isinstance(value, dict):
            nested = find_bounties(value)
            if nested:
                return nested
    return []


def fmt_reward(bounty):
    reward = pick(bounty, "reward", "rewardUsdc", "amount", "payout", "prize")
    if isinstance(reward, dict):
        amount = pick(reward, "amount", "usdc", "value", "total")
        currency = pick(reward, "currency", "token", "asset", default="USDC")
        return "%s %s" % (amount, currency) if amount is not None else json.dumps(reward, ensure_ascii=False)
    if reward is None:
        return "unknown"
    text = "%s %s" % (reward, pick(bounty, "currency", "token", "asset", default="USDC"))
    est = bounty.get("est_usd")
    if isinstance(est, (int, float)) and est != reward:
        text += " (~%s USD)" % est
    return text


def print_bounties(bounties):
    if not bounties:
        print("No bounties returned (empty feed response).")
        return
    print("Open bounties: %d" % len(bounties))
    print("=" * 78)
    for index, bounty in enumerate(bounties, 1):
        if not isinstance(bounty, dict):
            print("%2d. %s" % (index, bounty))
            continue
        title = pick(bounty, "title", "name", "summary", default="(no title)")
        print("%2d. %s" % (index, title))
        print("    id:       %s" % pick(bounty, "id", "bountyId", "slug", default="?"))
        print("    reward:   %s" % fmt_reward(bounty))
        print("    deadline: %s" % pick(bounty, "deadline", "deadlineAt", "expiresAt",
                                        "expiry", default="no deadline"))
        source = pick(bounty, "source", "board", "platform")
        if source:
            print("    source:   %s" % source)
        url = pick(bounty, "url", "issueUrl", "link", "href")
        if url:
            print("    url:      %s" % url)
        requires = bounty.get("requires")
        if isinstance(requires, list) and requires:
            print("    requires: %s" % ", ".join(str(item) for item in requires))
    print("=" * 78)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def parse_arguments(pairs):
    out = {}
    for pair in pairs or []:
        if "=" not in pair:
            raise ValueError("tool arguments are key=value, got: %r" % pair)
        key, value = pair.split("=", 1)
        if value.lower() in ("true", "false"):
            out[key] = value.lower() == "true"
        elif value.lstrip("-").isdigit():
            out[key] = int(value)
        else:
            out[key] = value
    return out


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    parser = argparse.ArgumentParser(
        description="Minimal MCP client for the Agent Bounty Feed (standard library only).")
    parser.add_argument("--url", default=DEFAULT_URL, help="MCP endpoint")
    parser.add_argument("--tool", default="list_bounties",
                        help="list_bounties | get_new_bounties | get_bounty | get_feed_stats")
    parser.add_argument("--arg", action="append", metavar="KEY=VALUE",
                        help="tool argument, repeatable (e.g. --arg limit=5)")
    parser.add_argument("--limit", type=int, default=None, help="trim the printed list to N items")
    parser.add_argument("--tools", action="store_true", help="print the server tool list and exit")
    parser.add_argument("--raw", action="store_true", help="print the raw JSON result")
    parser.add_argument("--verbose", action="store_true", help="transport diagnostics on stderr")
    args = parser.parse_args(argv)

    try:
        tool_args = parse_arguments(args.arg)
    except ValueError as exc:
        print("ERROR: %s" % exc, file=sys.stderr)
        return 2

    client = McpHttp(args.url, verbose=args.verbose)
    try:
        info = client.initialize()
        if args.verbose:
            server = info.get("serverInfo") or {}
            sys.stderr.write("[mcp] server=%s %s protocol=%s session=%s\n"
                             % (server.get("name"), server.get("version"),
                                info.get("protocolVersion"), client.session_id))

        if args.tools:
            for tool in client.list_tools():
                print("- %s: %s" % (tool.get("name"), (tool.get("description") or "").strip()[:160]))
            return 0

        result = client.call_tool(args.tool, tool_args)
        if result.get("isError"):
            print("ERROR from tool %s: %s"
                  % (args.tool, json.dumps(result, ensure_ascii=False)[:400]), file=sys.stderr)
            return 1
        data = tool_payload(result)
    except (urllib.error.URLError, RuntimeError, TimeoutError, OSError) as exc:
        print("ERROR: network/protocol failure: %s" % exc, file=sys.stderr)
        return 1

    if args.raw:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return 0

    if args.tool in ("list_bounties", "get_new_bounties"):
        bounties = find_bounties(data)
        if args.limit is not None:
            bounties = bounties[: args.limit]
        print_bounties(bounties)
        if isinstance(data, dict):
            returned = pick(data, "count", default=len(bounties))
            total = data.get("total_matching")
            extra = " | matching: %s" % total if total is not None else ""
            print("Server returned %s item(s)%s | has_more: %s"
                  % (returned, extra, data.get("has_more")))
            if args.limit is not None and returned and args.limit < len(bounties) + 1:
                print("(printed first %d)" % len(bounties))
        return 0

    if args.tool == "get_feed_stats":
        stats = data.get("stats", data) if isinstance(data, dict) else data
        if isinstance(stats, dict):
            for key, value in stats.items():
                if isinstance(value, (dict, list)):
                    value = json.dumps(value, ensure_ascii=False)
                print("%-26s %s" % (key + ":", value))
        else:
            print(json.dumps(stats, ensure_ascii=False, indent=2))
        return 0

    print(json.dumps(data, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
