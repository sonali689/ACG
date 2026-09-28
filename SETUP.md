# Setup — VS Code, then GitHub

Two parts. Part A gets it running locally. Part B puts it on GitHub.
Budget about 20 minutes for A and 10 for B.

---

# Part A — Run it in VS Code

## A1. Install the three things you need

| | What | Where | Note |
|---|---|---|---|
| 1 | **Python 3.11 or 3.12** | python.org/downloads | On Windows, tick **"Add Python to PATH"** on the first installer screen. Missing this causes most setup failures. Avoid 3.13 for now — LightGBM wheels lag. |
| 2 | **VS Code** | code.visualstudio.com | |
| 3 | **Git** | git-scm.com | macOS: `xcode-select --install` also works |

Then in VS Code, install the **Python** extension (Microsoft). Pylance comes with it.

Check both are visible — open a terminal (`` Ctrl+` ``) and run:

```bash
python --version     # Windows; use python3 on macOS/Linux
git --version
```

If `python` isn't found on Windows, try `py --version`. If that works, use `py` in place of `python` everywhere below.

## A2. Open the project

**File → Open Folder** → select `ACG/smartbuy`.

Open the folder that *contains* `src/`, `dashboard/` and `outputs/` — not `ACG/`, and not one level deeper. Every script resolves its paths from its own location, and this is where they expect to be.

## A3. Create a virtual environment

A venv keeps these packages out of your system Python, so nothing you install here can break another project.

**macOS / Linux**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows (PowerShell)**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

If PowerShell blocks the activate script, run this once and try again:
```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

**Windows (Command Prompt)**
```cmd
python -m venv .venv
.venv\Scripts\activate.bat
```

Your prompt should now start with `(.venv)`.

Then point VS Code at it: **Ctrl+Shift+P** → `Python: Select Interpreter` → choose the one showing `.venv`. The included `.vscode/settings.json` already suggests it, but confirm it stuck — the status bar bottom-left should read `.venv`.

## A4. Install the packages

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Two or three minutes. That covers everything needed to produce the corrected scorecard, the replay, the dashboard data and the deck.

**You do not need PyTorch** unless you plan to re-train the LSTM and N-BEATS models. Everything downstream reads saved predictions from `outputs/scorecards/`. If you do want to re-train:

```bash
pip install -r requirements-torch.txt
```

That pulls ~2 GB. Skip it unless you need it.

## A5. Install Poppins

The deck is built in the Round 1 typeface. Without it, PowerPoint substitutes and the design breaks.

Download from `fonts.google.com/specimen/Poppins` → select all weights → install.
- **Windows:** select the `.ttf` files → right-click → *Install for all users*
- **macOS:** select the `.ttf` files → double-click → *Install Font*

Also worth installing **IBM Plex Sans** and **IBM Plex Mono** if you want the offline dashboard to look identical to the hosted one.

## A6. Pre-flight check

Before running anything, confirm the environment is sane:

```bash
python check_env.py
```

It reports **everything** wrong at once — wrong folder, venv not active, missing
packages, missing scripts, missing input data — rather than failing on the first
problem. Fix any `XX` lines, re-run until it passes.

## A7. Run the pipeline

```bash
python src/validation/leakfree_all_horizons.py   # corrected scorecard
python src/decision/replay_leakfree.py           # replay on corrected forecasts
python dashboard/build_data.py                   # -> dashboard/data.json
python dashboard/build_dashboard.py              # bakes data into index.html
python src/deck/make_charts_acg.py               # ACG-palette charts
python src/deck/build_deck_round1_style.py       # the 15-slide deck
```

Or just `make` (macOS/Linux; on Windows paste the six lines, or install `make`
via `choco install make`).

Order matters. Steps 3–6 all depend on 1 and 2, and step 4 depends on 3.

**Why step 4 exists.** The dashboard is one self-contained file so it opens from
disk with no server and no CORS problems. That means the data has to be baked in
rather than fetched. `build_dashboard.py` does the baking, so the page stays in
sync with the pipeline instead of drifting out of date.

**What you should see:** two scorecard tables printed, then replay figures, then `wrote .../data.json`, then a list of chart filenames, then `saved .../SmartBuy_Round2_15Slides.pptx`.

## A8. View the dashboard

Simplest: double-click `dashboard/index.html`.

Better, if you want it to behave exactly as when hosted:

```bash
python -m http.server 8000 --directory dashboard
```
Then open `http://localhost:8000`.

Even better — install the **Live Server** extension, right-click `index.html` → *Open with Live Server*. It reloads when you edit.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `python: command not found` (Windows) | Use `py` instead, or reinstall Python with "Add to PATH" ticked |
| `ModuleNotFoundError: pandas` | venv not active. Re-run the activate command; check the prompt shows `(.venv)` |
| `FileNotFoundError` with a path like `\\home\\claude\\...` | An old copy of the script with a hardcoded path. Re-copy it from the bundle. |
| `FileNotFoundError: .../outputs/scorecards/...` | You opened the wrong folder. It must be the one containing `src/` |
| LightGBM fails to install | You're on Python 3.13. Use 3.11 or 3.12 |
| Deck fonts look wrong | Poppins not installed, or PowerPoint was open during install — restart it |
| `cannot be loaded because running scripts is disabled` | The `Set-ExecutionPolicy` line in A3 |

---

# Part B — Private GitHub repo

## B1. Create the repo

On github.com → **New repository**:
- Name: `smartbuy-acg-round2`
- Visibility: **Private**
- **Do not** initialise with a README, .gitignore or licence — you already have files, and those would conflict

## B2. Check what you're about to commit

Before the first push, confirm nothing large or private is going in:

```bash
git init
git add -A
git status --short | head -40
du -sh data outputs
```

`data/` is about 4 MB and `outputs/` about 6 MB. That's fine for GitHub (the hard limit is 100 MB per file), and committing them makes your submission reproducible by a judge without re-downloading anything.

The included `.gitignore` excludes the two large raw spreadsheets by default. **For a competition submission I'd comment those two lines out** and commit everything, so the repo runs end to end for anyone who clones it. Reproducibility is worth 3 MB.

## B3. Push

```bash
git add -A
git commit -m "Smart Buy Round 2: leak-free validation, replay, dashboard, deck"
git branch -M main
git remote add origin https://github.com/<your-username>/smartbuy-acg-round2.git
git push -u origin main
```

If prompted for a password, GitHub no longer accepts your account password. Either:
- Install **GitHub CLI** (`cli.github.com`), run `gh auth login`, done; or
- Generate a **personal access token**: github.com → Settings → Developer settings → Personal access tokens → Tokens (classic) → Generate, scope `repo`. Use the token as the password.

VS Code's Source Control panel (Ctrl+Shift+G) handles auth for you if you sign in with the GitHub account — often the least friction.

## B4. Add your teammates

Repo → Settings → Collaborators → **Add people**. They then:

```bash
git clone https://github.com/<your-username>/smartbuy-acg-round2.git
cd smartbuy-acg-round2
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
make
```

## B5. Hosting from a private repo — the catch

**GitHub Pages does not serve private repositories on the free plan.** Three ways round it:

| | Approach | Effort |
|---|---|---|
| **1** | **GitHub Student Developer Pack** → free GitHub Pro → Pages works on private repos. You have `.ac.in` addresses, so approval is usually same-day. `education.github.com/pack` | 10 min + wait |
| **2** | **Netlify Drop.** Drag the `dashboard/` folder onto `app.netlify.com/drop`. Live URL immediately, code stays private. | 30 seconds |
| **3** | Second **public** repo containing only `index.html`, with Pages enabled on it. Model code stays private. | 5 min |

**Option 2 is what I'd do.** It decouples hosting from the repo entirely, so nothing about your source visibility affects whether the dashboard is up on presentation day.

## B6. Everyday workflow

```bash
git pull            # before you start
# ... work ...
git add -A
git commit -m "what changed"
git push
```

Or use VS Code's Source Control panel: stage with `+`, type a message, click ✓, then the sync arrows.

**One rule worth agreeing now:** `outputs/` files are generated. If two of you both re-run the pipeline and push, you'll get merge conflicts on CSVs, which are miserable to resolve. Agree that one person owns regeneration, or add `outputs/` to `.gitignore` and commit it only when you cut a submission tag:

```bash
git tag -a round2-submission -m "Final Round 2 submission"
git push --tags
```
