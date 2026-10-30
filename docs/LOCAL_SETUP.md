# Run Claim Sense on your laptop (Windows and VS Code)

These steps run the whole app on your own Windows laptop with VS Code. Every command goes in a terminal on the laptop: in VS Code open one with **Terminal → New Terminal** (it is PowerShell by default). Mac and Linux differences are noted where they matter.

## 1. Install the tools (one time)

| Tool | Get it from | Check it |
|---|---|---|
| Git | https://git-scm.com/downloads (keep the default options) | `git --version` |
| Python 3.11 or newer (3.12 recommended) | https://www.python.org/downloads/ and tick **Add python.exe to PATH** | `python --version` |
| Node.js 22 LTS | https://nodejs.org/ | `node --version` |
| VS Code | https://code.visualstudio.com/ | |
| Docker Desktop (optional, for the PostgreSQL stack) | https://www.docker.com/products/docker-desktop/ | `docker --version` |

Close and reopen VS Code after installing so the new commands are found.

If PowerShell refuses to run `activate` with "running scripts is disabled", run this once:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

## 2. Get the code

```powershell
git clone https://github.com/sricharansk/CLAIM-SENSE.git
cd CLAIM-SENSE
code .
```

If you already have it, update it instead: `git checkout main` then `git pull origin main`.

When VS Code opens the folder it offers the recommended extensions (Python, Ruff, Playwright, Docker). Accept them.

## 3. Set up the backend (one time)

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate          # Mac/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
cd ..
```

Then in VS Code press `Ctrl+Shift+P`, choose **Python: Select Interpreter** and pick `backend\.venv`. (On Mac or Linux the workspace setting points at the Windows path; pick `backend/.venv/bin/python` here instead.)

## 4. Set up the frontend (one time)

```powershell
cd frontend
npm install
cd ..
```

## 5. Start the app

Easiest: `Ctrl+Shift+P` → **Tasks: Run Task** → **Start app (API + UI)**. It opens two terminals, one for the API and one for the UI.

By hand, in two terminals:

```powershell
# terminal 1: API on http://localhost:8000 (API docs at /docs)
cd backend
.venv\Scripts\activate
uvicorn app.main:app --reload --port 8000

# terminal 2: UI on http://localhost:5173
cd frontend
npm run dev
```

Open http://localhost:5173. On first start the API creates `backend\claimsense.db` and seeds 5 policy wordings and 57 synthetic claims.

Sign in as `adjuster`, `supervisor` or `auditor`. Locally the password is the default `claimsense-demo`, unless you set the `DEMO_PASSWORD` environment variable before starting the API. (The live site uses a different password, kept only in Render and the GitHub secret.)

To start again from a clean database, stop the API (`Ctrl+C`) and delete `backend\claimsense.db` and `backend\storage`.

## 6. Run the tests

From VS Code: **Tasks: Run Task** → **Run backend tests**, **Run golden evaluation** and **Run claims report**. The Testing panel (flask icon) also lists the backend tests.

By hand, from the repository folder with the virtual environment active:

```powershell
cd backend
ruff check app tests ../scripts
python -m pytest -q                 # 127 tests
cd ..
python scripts/provenance.py --check
python scripts/evaluate.py          # 803/803 checks -> reports/evaluation.md
python scripts/claims_report.py     # 58 claims -> reports/claims_results.md
cd frontend
npm run build
cd ..
```

The evaluation and claims report rewrite the files in `reports/`; only the "Generated" time changes when nothing else has.

## 7. Full stack in Docker (optional)

With Docker Desktop running:

```powershell
docker compose up --build -d
python scripts/smoke_test.py http://localhost:8080
```

Open http://localhost:8080. This runs the app on PostgreSQL. The browser tests need a freshly started stack:

```powershell
docker compose down -v
docker compose up -d
cd e2e
npm ci
npx playwright install chromium
npx playwright test                 # 12 tests
```

Stop it with `docker compose down` (add `-v` to delete the database).

## 8. Save your changes to GitHub

```powershell
git checkout -b my-change
git add -A
git commit -m "Describe what you changed"
git push -u origin my-change
```

Open the repository on GitHub, create the pull request and merge it once the checks are green. After a merge, deploy on Render (*Manual Deploy → Deploy latest commit*) and run the **Verify deployment** workflow, as described in `CLAUDE.md`.

## Common problems

- **`python` opens the Microsoft Store**: reinstall Python from python.org with *Add python.exe to PATH* ticked, or turn off the `python.exe` App execution alias in Windows settings.
- **Port 8000 or 5173 already in use**: another copy is still running. Close its terminal, or start the API with `--port 8001` and change the proxy in `frontend/vite.config.ts` to match.
- **Sign-in is refused after several wrong passwords**: five failures lock that username for 5 minutes. Wait, or restart the API.
- **The UI loads but shows no data**: the API is not running on port 8000. Start terminal 1.
