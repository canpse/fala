# fa: instructions for AI agents

`fa` (package `fala`) turns a plain-language request into a shell command:
`fa show the 5 biggest files` puts `find . -type f ... | head -5` on the shell prompt, and the
person checks it and presses Enter. If you were asked to install or configure fa, follow this.
These instructions are also printed by `fa --agent`.

The recommended way to install fa is exactly this: the person gives you the link to this
repository and asks you to install it. So you may get nothing more than "install this" and a
link. That is enough: follow the steps below without asking anything you can find out
yourself.

## 1. Install: two commands

```sh
pipx install fala                  # or: uv tool install fala · pip install --user fala
fa --install claude                # or codex, agy, pi, anthropic, openrouter... (see the table)
```

No pipx or uv? Use `python3 -m pip install --user fala`: it needs no sudo. Only install pipx
(with the system's package manager) if pip refuses with `externally-managed-environment`.

`fa --install` adds `eval "$(fa --init bash)"` to `~/.bashrc` (or the zsh one to `~/.zshrc`),
saves the provider and sends a test request. Running it again duplicates nothing. Without a
provider, it picks one from what it finds on the machine (an API key in the environment, or
claude/codex/agy/pi installed). It ends with `ok: ...` when it worked; otherwise it says what
is missing, for example `claude failed: Not logged in`: then ask the person to log into that
program (`claude`, then `/login`) and run it again. Needs Python 3.11 or newer. The
integration only applies to terminals opened afterwards: tell the person to open a new one
(or `source ~/.bashrc`).

**Which provider, when the person didn't say:** prefer the subscription you are running on,
since the person already has it and it is logged in: Claude Code → `claude`, Codex → `codex`,
Antigravity → `agy`, pi → `pi`. Otherwise use an API key that is already in the environment.
Only ask the person if neither works.

**When it's done**, tell the person in two lines: open a new terminal, and try something like
`fa show the 5 biggest files here`. Then offer `fa --scan` (section 4), explaining what it
sends, and run it only if they agree.

For what each provider is, or to adjust things later, see section 2.

## 2. Configure: `fa --config key=value ...`

No file editing needed. The command writes `~/.config/fa/config.toml` and shows the result.
Changing `provider` drops the previous provider's keys, so pass `model` along with it.
`key=` (empty) removes a key.

| key | what it is |
|---|---|
| `provider` | API: `anthropic`, `openai`, `openrouter`, `groq`, `ollama`, `compat`. Subscription (official program, already logged in, no key): `claude`, `codex`, `agy`, `pi` |
| `model` | the model's name at the provider (required for APIs except `anthropic`; subscriptions use the defaults below) |
| `url` | `compat` only: the OpenAI-compatible API address, e.g. `http://localhost:8080/v1` |
| `key_env` | name of the environment variable holding the key, if not the default one |
| `thinking` | the program's reasoning level: pi's `--thinking`, claude's and agy's `--effort`, codex's `model_reasoning_effort` |
| `pi_provider` | `pi` only: pi's `--provider` |
| `timeout` | seconds before giving up (default 30) |

Default key variables: `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `OPENROUTER_API_KEY`,
`GROQ_API_KEY`. `ollama` needs no key.

**The key never goes in config.toml.** It lives in an environment variable. If the person
doesn't have the variable yet, ask them to put it in `~/.bashrc` (or wherever they keep
secrets); don't write the key into any file yourself unless they ask.

**Subscription instead of a key.** If the person already uses Claude Code, Codex or
Antigravity (`agy`) logged in, fa calls that program once per request, with no tools, in a
neutral folder. Check the login first (`claude -p hi`, `codex exec hi`, `agy -p=hi`). Defaults
and time measured on an ordinary laptop: `claude` → haiku, ~3 s · `codex` → gpt-6-luna with
`low`, ~5 s · `agy` → gemini-3.8-flash-low, ~6 s · `pi` with `fa --service` → ~2 s.

Examples:

```sh
fa --config provider=anthropic model=claude-haiku-5-5
fa --config provider=openrouter model=google/gemma-4-31b-it
fa --config provider=ollama model=qwen2.5:7b timeout=120
fa --config provider=compat url=http://localhost:8080/v1 model=local key_env=MY_KEY
fa --config provider=claude                      # Claude subscription, haiku model
fa --config provider=codex model=gpt-6-luna thinking=low
fa --config provider=pi pi_provider=openai-codex model=gpt-6-luna thinking=off
```

How to choose: small, fast models are enough (it only turns one sentence into one command).
What matters is latency: prefer a model without long reasoning. With `pi`, also run
`fa --service` (keeps pi open as a systemd user service and saves ~3 s per request).
A local model needs a good machine: the context is a few thousand tokens.

## 3. Check: `fa --test`

Shows the settings in use and sends a real request. Exits 0 with `ok: ... → <command>` if it
worked; otherwise exits 1 and says what is missing (empty key, rejected key, missing model,
no answer). Always run it after configuring.

## 4. Optional

- `fa --scan`: reads the machine once (distribution, network, installed tools) for context.
  It makes the answers much better. **It sends the hostname, IPs and the list of services to
  the provider with every request**: tell the person before running it.
- Example packs: `~/.config/fa/packs/<name>.txt`, lines `request => command`, with a
  `# flag: x` line to enable it with `fa -x <request>`. `fa -h` lists the ones that exist.

## What not to do

- Don't run the commands fa suggests on the person's behalf: it exists so they can check them.
- Don't put an API key in config.toml, in the shell history or in a commit message.

Version 0.1 names (`--instalar`, `provedor=`, `modelo=`...) still work.
