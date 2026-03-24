# discord-ping

A minimal CLI tool that measures Discord's REST API and Gateway latency live in your terminal.

```
  discord-ping                           12:25:01  tick #4
  ────────────────────────────────────────────────────────

  REST API   85.32 ms   ████████░░░░░░░░░░░░░░░░░░░░░░
  ↳ avg 85.32 ms  min 49.10 ms  max 157.20 ms

  Gateway    312.4 ms   ████████████████████░░░░░░░░░░
  ↳ heartbeat → ack

  REST history   ▂▁▃▂▄▃▂▁▃▂
  GW   history   ▄▅▃▄▅▄▃▅▄▃

  Press Ctrl+C to exit.
```

---

## Install

### curl (any Linux/macOS)

```bash
curl -fsSL https://raw.githubusercontent.com/drlove2002/discord-ping/main/install.sh | bash
```

### Nix

```bash
# Run without installing
nix run github:drlove2002/discord-ping

# Install permanently
nix profile install github:drlove2002/discord-ping
```

### pip

```bash
pip install git+https://github.com/drlove2002/discord-ping.git
```

---

## Usage

```bash
discord-ping                        # interactive prompt
discord-ping --token YOUR_TOKEN     # skip prompt
discord-ping --interval 5           # refresh every 5 seconds
discord-ping --no-prompt            # non-interactive, no token
```

### Environment variable

```bash
export DISCORD_TOKEN=your_token
discord-ping
```

---

## Token

A bot token is optional. Without one, discord-ping measures:

- **REST API** — round-trip to `discord.com/api/v10/gateway`
- **Gateway** — WebSocket connect → HELLO time

With a token, Gateway shows true **heartbeat → ack** latency which is what Discord bots actually experience.

To get a token:

1. Go to [discord.com/developers/applications](https://discord.com/developers/applications)
2. Click **New Application** → give it any name
3. Open the **Bot** tab in the sidebar
4. Click **Reset Token** → copy it

> **Never share your token.** It gives full access to your bot.

---

## Latency Reference

| Range | Meaning |
|-------|---------|
| `< 100 ms` 🟢 | Excellent |
| `100–200 ms` 🟡 | Acceptable |
| `> 200 ms` 🔴 | Degraded |

---

## Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--token`, `-t` | `$DISCORD_TOKEN` | Bot token for heartbeat latency |
| `--interval`, `-i` | `2.0` | Refresh interval in seconds |
| `--no-prompt` | off | Disable interactive token prompt |

---

## Requirements

- Python 3.9+
- [`aiohttp`](https://docs.aiohttp.org) (installed automatically)

---

## License

MIT
