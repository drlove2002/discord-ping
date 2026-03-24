#!/usr/bin/env python3
"""discord-ping — Live Discord REST API and Gateway latency monitor."""

import asyncio
import time
import sys
import json
import argparse
import os
import signal
import getpass

try:
    import aiohttp
except ImportError:
    print("Error: aiohttp required. Run: pip install aiohttp", file=sys.stderr)
    sys.exit(1)

DISCORD_API = "https://discord.com/api/v10"
DISCORD_GW = "wss://gateway.discord.gg/?v=10&encoding=json"
RUNS = 3

# ── Helpers ───────────────────────────────────────────────────────────────────


def clr(text, code):
    return f"\033[{code}m{text}\033[0m" if sys.stdout.isatty() else text


def fmt_ms(ms):
    if ms is None:
        return clr("N/A      ", "90")
    if ms < 100:
        return clr(f"{ms:.2f} ms", "92")
    if ms < 200:
        return clr(f"{ms:.2f} ms", "93")
    return clr(f"{ms:.2f} ms", "91")


def bar(ms, max_ms=500, width=30):
    if ms is None:
        return clr("─" * width, "90")
    filled = int(min(ms / max_ms, 1.0) * width)
    color = "92" if ms < 100 else "93" if ms < 200 else "91"
    return clr("█" * filled, color) + clr("░" * (width - filled), "90")


def sparkline(data, width=30):
    blocks = " ▁▂▃▄▅▆▇█"
    recent = data[-width:]
    valid = [v for v in recent if v is not None]
    if not valid:
        return clr("─" * len(recent), "90")
    lo, hi = min(valid), max(valid)
    out = ""
    for v in recent:
        if v is None:
            out += clr("?", "90")
            continue
        idx = int((v - lo) / (hi - lo + 1e-9) * (len(blocks) - 1))
        color = "92" if v < 100 else "93" if v < 200 else "91"
        out += clr(blocks[idx], color)
    return out


# ── Token prompt ──────────────────────────────────────────────────────────────


def prompt_token() -> str | None:
    print()
    print(clr("  No token provided.", "33"))
    print(
        f"  {clr('→', '90')} Without a token, only REST + WebSocket connect latency is measured."
    )
    print(f"  {clr('→', '90')} For true heartbeat latency, a bot token is needed.")
    print()
    print(f"  {clr('[h]', '1;36')} How to get a token")
    print(f"  {clr('[p]', '1;36')} Paste token")
    print(f"  {clr('[s]', '1;36')} Skip")
    print()

    while True:
        try:
            choice = input(clr("  Your choice [h/p/s]: ", "1")).strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return None

        if choice == "h":
            print()
            print(clr("  How to get a Discord Bot Token", "1;33"))
            print(clr("  " + "─" * 48, "90"))
            for n, verb, detail in [
                ("1", "Go to", "https://discord.com/developers/applications"),
                ("2", "Click", '"New Application" → give it any name'),
                ("3", "Open", 'the "Bot" tab in the sidebar'),
                ("4", "Click", '"Reset Token" → copy the token shown'),
            ]:
                print(f"  {clr(n + '.', '1;36')} {verb} {clr(detail, '36')}")
            print(clr("  " + "─" * 48, "90"))
            print(clr("  ⚠  Never share your token.", "33"))
            print()
            choice = "p"  # fall through to paste

        if choice == "p":
            try:
                token = getpass.getpass(clr("  Paste token (hidden): ", "1")).strip()
                return token or None
            except (EOFError, KeyboardInterrupt):
                print()
                return None

        elif choice == "s":
            return None

        else:
            print(clr("  Please enter h, p, or s.", "91"))


# ── Measurements ──────────────────────────────────────────────────────────────


async def measure_rest(session: aiohttp.ClientSession):
    times = []
    for _ in range(RUNS):
        t = time.perf_counter()
        async with session.get(f"{DISCORD_API}/gateway") as r:
            await r.read()
        times.append((time.perf_counter() - t) * 1000)
    return sum(times) / len(times), min(times), max(times)


async def measure_gateway(session: aiohttp.ClientSession, token: str | None):
    async with session.ws_connect(DISCORD_GW) as ws:
        hello = json.loads((await ws.receive()).data)
        if hello.get("op") != 10:
            return None

        if not token:
            return (time.perf_counter() - time.perf_counter()) or (
                lambda t: (time.perf_counter() - t) * 1000
            )(time.perf_counter())

        await ws.send_str(
            json.dumps(
                {
                    "op": 2,
                    "d": {
                        "token": token,
                        "intents": 0,
                        "properties": {
                            "os": "linux",
                            "browser": "discord-ping",
                            "device": "discord-ping",
                        },
                    },
                }
            )
        )

        async for raw in ws:
            if raw.type == aiohttp.WSMsgType.CLOSE:
                return None
            msg = json.loads(raw.data)
            if msg.get("op") == 9:
                return None
            if msg.get("op") == 0 and msg.get("t") == "READY":
                break

        t = time.perf_counter()
        await ws.send_str(json.dumps({"op": 1, "d": None}))
        async for raw in ws:
            if raw.type != aiohttp.WSMsgType.TEXT:
                continue
            if json.loads(raw.data).get("op") == 11:
                return (time.perf_counter() - t) * 1000


# ── Render ────────────────────────────────────────────────────────────────────


def render(rest_avg, rest_lo, rest_hi, gw, tick, token, h_rest, h_gw):
    mode = "heartbeat → ack" if token else "ws connect → hello"
    lines = [
        clr("  discord-ping", "1;35")
        + clr(
            f"                       {time.strftime('%H:%M:%S')}  tick #{tick}", "90"
        ),
        clr("  " + "─" * 52, "90"),
        "",
        f"  {clr('REST API', '1;36')}   {fmt_ms(rest_avg)}   {bar(rest_avg)}",
        f"  {clr('↳', '90')} avg {fmt_ms(rest_avg)}  min {fmt_ms(rest_lo)}  max {fmt_ms(rest_hi)}",
        "",
        f"  {clr('Gateway', '1;36')}    {fmt_ms(gw)}   {bar(gw)}",
        f"  {clr('↳', '90')} {mode}",
        "",
        *(
            [
                f"  {clr('REST history', '90')}   {sparkline(h_rest)}",
                f"  {clr('GW   history', '90')}   {sparkline(h_gw)}",
                "",
            ]
            if len(h_rest) > 1
            else []
        ),
        clr("  Press Ctrl+C to exit.", "90"),
    ]
    print("\033[H", end="", flush=True)
    for line in lines:
        print(f"{line}\033[K")


# ── Main loop ─────────────────────────────────────────────────────────────────


async def live_loop(token: str | None, interval: float):
    loop = asyncio.get_running_loop()
    stop = asyncio.Event()

    def _shutdown(sig, _frame):
        print("\033[H\033[2J", end="", flush=True)
        print(clr("  Bye!", "90"))
        stop.set()

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    h_rest, h_gw = [], []
    tick = 0
    print("\033[H\033[2J", end="", flush=True)

    async with aiohttp.ClientSession() as session:
        while not stop.is_set():
            tick += 1
            try:
                rest_avg, rest_lo, rest_hi = await measure_rest(session)
            except Exception:
                rest_avg = rest_lo = rest_hi = None

            try:
                gw = await measure_gateway(session, token)
            except Exception:
                gw = None

            h_rest.append(rest_avg)
            h_gw.append(gw)
            render(rest_avg, rest_lo, rest_hi, gw, tick, token, h_rest, h_gw)
            await asyncio.sleep(interval)


# ── Entry point ───────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        prog="discord-ping", description="Live Discord latency monitor."
    )
    parser.add_argument(
        "--token", "-t", default=os.environ.get("DISCORD_TOKEN"), metavar="TOKEN"
    )
    parser.add_argument("--interval", "-i", type=float, default=2.0, metavar="SECS")
    parser.add_argument("--no-prompt", action="store_true")
    args = parser.parse_args()

    token = args.token
    if not token and not args.no_prompt and sys.stdin.isatty():
        token = prompt_token()

    asyncio.run(live_loop(token, args.interval))
