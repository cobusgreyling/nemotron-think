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

3. **Free public hosted version right now** (easiest for sharing the showcase): Use the one-click buttons in the main [README.md](../README.md) for Vercel or Netlify. They support private GitHub repos on the free tier and will serve `docs/index.html` at a public URL (e.g. `your-project.vercel.app`).

4. **Official GitHub Pages URL** `https://cobusgreyling.github.io/nemotron-think/`: See the section below. This requires making the repo public (on free plan) or a paid GitHub plan.

## For GitHub Pages (recommended for the hosted web version)

1. Go to your repo → **Settings** → **Pages**
2. Under "Build and deployment", set **Source** to **Deploy from a branch**
3. Set branch to `main` and folder to `/docs`
4. Save

Your landing page will be live at `https://cobusgreyling.github.io/nemotron-think/`

**Important notes (GitHub Pages limitation):**
- **Yes — on the free GitHub plan, GitHub Pages for project sites like this only works with public repositories.** Private repositories require GitHub Pro, Team, or Enterprise.
- Even on paid plans, Pages sites published from private repos are still publicly accessible on the internet by default.
- To get `https://cobusgreyling.github.io/nemotron-think/` working on the free plan: make this repo **public** first, then enable Pages.
- Source: [GitHub Pages docs](https://docs.github.com/en/pages/getting-started-with-github-pages/about-github-pages#about-github-pages-sites) and related pages.

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

- `index.html` — The beautiful landing page + fully working demo (the showcase)
- `index.md` — Docs hub
- Plus root-level `vercel.json` and `netlify.toml` for easy one-click public deploys of this folder (works with private repos)
- Other docs: `getting-started.md`, `traces.md`, `api-reference.md`, `extending-tools.md`, `configuration.md`
- `math_tool_example.json` — the trace used in the interactive demo

## Updating the landing page

The page is a single file. Edit `docs/index.html` directly. Tailwind is loaded via CDN for zero-build experience.
