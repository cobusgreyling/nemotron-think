# Documentation

This folder contains the full documentation for nemotron-think plus the interactive landing page.

## For GitHub Pages (recommended)

1. Go to your repo → **Settings** → **Pages**
2. Under "Build and deployment", set **Source** to **Deploy from a branch**
3. Set branch to `main` (or master) and folder to `/docs`
4. Save

Your landing page will be live at `https://<user>.github.io/nemotron-think/`

The `index.html` is a fully self-contained modern landing page with interactive trace replay (no backend needed).

## Local development / preview

Simply open `docs/index.html` in any browser:

```bash
# macOS
open docs/index.html

# Linux
xdg-open docs/index.html

# Or with python (any OS)
python -m http.server 8080 --directory docs
# then visit http://localhost:8080
```

All links between markdown files work when browsing the folder on GitHub.

## Contents

- `index.html` — The beautiful landing page + fully working demo
- `index.md` — Docs hub
- `getting-started.md`
- `traces.md`
- `api-reference.md`
- `extending-tools.md`
- `configuration.md`
- `math_tool_example.json` — the trace used in the interactive demo

## Updating the landing page

The page is a single file. Edit `docs/index.html` directly. Tailwind is loaded via CDN for zero-build experience.
