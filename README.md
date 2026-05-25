# Personal Portfolio Site

A small static-site engine for a personal portfolio / CV. Content lives in plain
YAML, renders to static HTML through Jinja templates, and ships with a serverless
"Ask my CV" chatbot and a build-time leak gate.

## What's here

- **CSS-variable theming.** One theme is included (`themes/neutral.css`). Themes are
  plain CSS-variable files in `themes/` (`tokens.css` holds shared variables; a theme
  file overrides them). Add more by dropping in a `themes/NAME.css` file and selecting
  it with `--theme NAME` at build time.
- **Build-time content tiering.** Content is split into a public (sanitized) tier
  and a private tier. The split happens at build time, not at render time, so private
  material is never present in a public build's source, markup, JS, or assets. The
  private tier lives in `content_internal/` and is git-ignored.
- **Leak gate.** `checks/leak_gate.py` scans the built site directory and the
  shipped chatbot knowledge bundle (`netlify/functions/`) for private markers
  (denylisted names, internal Slack links, screenshot references) and exits
  nonzero if anything leaks. Forbidden terms live in the committed
  `checks/denylist.txt`, which is enforced unconditionally, so the gate works on
  the public deploy without the git-ignored private tier. It runs as the last
  step of every build, including on Netlify.
- **"Ask my CV" chatbot.** A zero-dependency Netlify Function (`netlify/functions/ask.mjs`)
  answers questions grounded only in the site's content. It is provider-aware: it
  calls the Claude API or the OpenAI API, auto-detected by which API key environment
  variable is set (`ANTHROPIC_API_KEY` or `OPENAI_API_KEY`). The knowledge base is
  compiled from the public content at build time (`scripts/build_kb.py`), and the
  front-end widget renders the response client-side (`assets/js/chat.js`).
- **Tests.** `tests/` covers the tiering logic, the leak gate, and the build.

## Stack

Python; Jinja2; PyYAML; Netlify Functions; vanilla JS and CSS (self-hosted fonts,
no framework).

## Build

```bash
python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
python -m pytest -q                                         # tests gate the deploy
python scripts/build_kb.py                                  # compile the chatbot knowledge base
python build.py --theme neutral --tier public --out build/neutral
python checks/leak_gate.py build/neutral                    # leak gate (also runs in CI)
```

Serve the output locally with any static server, e.g. `python -m http.server -d build/neutral`.

## Tests

```bash
python -m pytest -q
```

## Chatbot configuration

The chatbot reads its API key from the environment and never commits it:

- Set `ANTHROPIC_API_KEY` to use the Claude API (model `claude-sonnet-4-6` by
  default; override with `CHAT_MODEL`).
- Set `OPENAI_API_KEY` to use the OpenAI API (model `gpt-4o-mini` by default;
  override with `OPENAI_MODEL`).

If both are set, the OpenAI key takes precedence. If neither is set, the chatbot
returns a configuration error.

The function rejects cross-origin browser requests (any request whose `Origin`
header is present and does not match the site's own origin) with a 403. There is
no rate limiting; for production, add Netlify rate-limiting or a shared token in
front of the function.

## Private tier

A private content tier exists for an access-controlled build. Its content lives in
`content_internal/` (git-ignored) and never ships to a public build. The leak gate
exists to guarantee that.
