# Documentation

This folder contains the full documentation for nemotron-think plus the interactive landing page (`docs/index.html`).

## Current best ways to view the interactive landing page

Because the repository is currently **private**:

1. **Easiest right now (full beautiful experience)**: Clone the repo and open the file locally:
   ```bash
   git clone https://github.com/cobusgreyling/nemotron-think.git
   cd nemotron-think
   open docs/index.html     # macOS
   # or double-click the file, or use xdg-open / python -m http.server
   ```
   The page is 100% self-contained (Tailwind via CDN + embedded demo data).

2. **On GitHub** (while logged in as owner/collaborator):
   Go to https://github.com/cobusgreyling/nemotron-think/blob/main/docs/index.html
   Then click the **Raw** button in the top right. This renders the full interactive page.

3. **Future hosted version** (public URL): `https://cobusgreyling.github.io/nemotron-think/`
   See the "For GitHub Pages" section below to enable it. You will likely need to make the repo public first.

## For GitHub Pages (recommended for the hosted web version)

1. Go to your repo → **Settings** → **Pages**
2. Under "Build and deployment", set **Source** to **Deploy from a branch**
3. Set branch to `main` and folder to `/docs`
4. Save

Your landing page will be live at `https://cobusgreyling.github.io/nemotron-think/`

**Important notes:**
- The repo is currently **private**. GitHub Pages for private repositories requires a paid plan (GitHub Pro or higher).
- For a public showcase/landing page that anyone can visit, make the repository public first (Settings → General → "Make public").
- Once enabled, it can take a minute or two for the site to build and become available.

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
