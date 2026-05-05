# Data Engineering Tooling Reference

> **Purpose:** Living reference for terminal commands, query idioms, and common patterns across the tools in this project. Organized by tool. Updated as new patterns appear.
>
> **Platforms covered:**
> - **macOS** (zsh, default since Catalina)
> - **Linux / WSL2 on Windows** (bash, near-identical to macOS for most commands)
>
> Commands work identically on both unless explicitly noted with **🍎 macOS only** or **🐧 Linux/WSL2 only** tags.
>
> **Conventions used in this file:**
> - `<placeholder>` means "replace with your actual value" (e.g., `<your-bucket-name>`)
> - `# comments` explain what a command does or when to use it
> - Commands marked **⚠️ destructive** can't be undone — read carefully before running
>
> **Note:** This file was originally `terminal-cheatsheet.md` (Phase 0). Renamed in Phase 1 to reflect broader scope as we added SQL idioms (DuckDB), data tooling, and other non-shell references.

---

## Table of Contents

### Shell & System
1. [Platform Setup (One-Time)](#1-platform-setup-one-time)
2. [Shell Environment & PATH](#2-shell-environment--path)
3. [File System & Inspection](#8-file-system--inspection)
4. [Diagnostic & Network Tools](#9-diagnostic--network-tools)
5. [Platform-Specific Gotchas](#10-platform-specific-gotchas)

### Version Control & Containers
6. [Git & GitHub](#3-git--github)
7. [Docker & Docker Compose](#4-docker--docker-compose)

### Cloud & Data Tools
8. [AWS CLI](#5-aws-cli)
9. [Package Management](#6-package-management)
10. [Python Environments](#7-python-environments)

### SQL & Data Profiling
11. [DuckDB SQL Idioms](#11-duckdb-sql-idioms)
12. [DuckDB ↔ Pandas Equivalencies](#12-duckdb--pandas-equivalencies)

*(Sections renumber as the file grows; the anchors above match the current section headings.)*

---

## 1. Platform Setup (One-Time)

### 🐧 WSL2 on Windows — first-time setup

If you're on Windows, install WSL2 once and use it for the rest of the project. This gives you a real Linux shell where every other command in this file works unchanged.

```powershell
# Run in PowerShell (as Administrator) — one-time only
wsl --install                   # installs WSL2 + Ubuntu by default

# Reboot when prompted

# After reboot, Ubuntu launches automatically and prompts for a username/password
# (this is your Linux user, separate from your Windows user)
```

After install:

```bash
# Inside Ubuntu (the new "Ubuntu" app in your Start menu)
sudo apt update && sudo apt upgrade -y
```

### Docker Desktop integration with WSL2

```
1. Install Docker Desktop for Windows from docker.com
2. Open Docker Desktop → Settings → Resources → WSL Integration
3. Enable integration with your Ubuntu distro
4. Apply & Restart
```

After this, `docker` and `docker compose` work from inside WSL2 just like they do on macOS.

### Where your project files should live

```bash
# 🐧 IMPORTANT: keep your repo on the Linux filesystem, NOT the Windows filesystem
cd ~                            # ~ is your Linux home: /home/<username>
mkdir Projects && cd Projects
git clone git@github.com:<username>/nyc-taxi-elt.git
```

**Why:** WSL2 file I/O is dramatically faster on the Linux filesystem (`/home/...`) than on the Windows filesystem (mounted at `/mnt/c/Users/...`). Cloning into `/mnt/c/Users/...` works but Docker volume mounts and dbt builds slow to a crawl.

### Open the project from VS Code

```bash
# 🐧 From inside WSL2, in your project directory
code .
```

VS Code auto-detects WSL and opens a remote-WSL window. The terminal inside VS Code is your WSL2 shell. This is the standard workflow.

---

## 2. Shell Environment & PATH

```bash
# Check which shell you're using
echo $SHELL
# 🍎 macOS default since Catalina: /bin/zsh
# 🐧 Ubuntu default: /bin/bash

# View your current PATH
echo $PATH

# Add a directory to PATH permanently
# 🍎 macOS (zsh):
echo 'export PATH="/Applications/Docker.app/Contents/Resources/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc                 # reload shell config into current session

# 🐧 Linux/WSL2 (bash):
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Find where a command lives
which docker                    # path to the binary the shell will use
which python3

# Find what PATH a command would resolve to (and any aliases/functions)
type docker
```

**When to use:** Anytime a command works for someone else but returns "command not found" for you, the PATH is the first place to check.

---

## 3. Git & GitHub

### Repository setup

```bash
# Clone a repository via SSH (preferred — no password prompts after key setup)
git clone git@github.com:<username>/<repo>.git

# Initialize a new local repo
git init

# Set upstream branch on first push (so future `git push` and `git pull` know where to go)
git push -u origin main
```

### Preserving empty directories

```bash
# Git doesn't track empty directories. Use .gitkeep placeholders to preserve them.
touch airflow/dags/.gitkeep

# Idiom: create an empty dir AND its placeholder in one chained command
mkdir -p some/new/dir && touch some/new/dir/.gitkeep

# List all currently-tracked files (useful to verify what's actually committed)
git ls-files

# List tracked files matching a pattern (verify a folder's contents are committed)
git ls-files | grep -E "(airflow|dbt)/"
```

**When to use:** Anytime you create new directory structure that's intentionally empty (waiting for code to be added later). Without `.gitkeep`, the directory disappears on a fresh clone.

### Daily workflow

```bash
# See what's changed (staged, unstaged, untracked)
git status

# See files git is currently ignoring (verifies .gitignore is working)
git status --ignored

# Check whether a specific file is being ignored
git check-ignore .env           # outputs ".env" if ignored, nothing if not

# Stage specific files (preferred over `git add .`)
git add .gitignore .env.example docker-compose.yaml

# Stage everything (only safe with a robust .gitignore in place)
git add .

# See exactly what's staged for commit, line by line
git diff --cached

# See file-level summary of what's staged
git diff --cached --stat

# Commit with a structured message (Conventional Commits format)
git commit -m "feat: add Docker Compose stack and env template

- Airflow 2.10 with LocalExecutor + Postgres metadata DB
- Mounts ingestion/ and dbt/ for later phases
- .env.example documents required Snowflake + AWS variables"

# Push to remote
git push origin main
```

### Recovery & damage control

```bash
# Unstage a file (keep changes, just remove from staging)
git restore --staged <filename>

# Remove a file from git but keep it on disk (use this if .env was accidentally committed)
git rm --cached .env

# View commit history one-line per commit
git log --oneline --decorate --graph
```

**Critical safety rule:** **always run `git status` before `git commit`**. The Pre-commit Audit Discipline flashcard exists for a reason — committing `.env` to a public repo is the #1 way credentials leak.

---

## 4. Docker & Docker Compose

### Version & connectivity checks

```bash
docker --version                # Docker Engine version
docker compose version          # Compose v2 syntax (note the space)
docker ps                       # list running containers (empty list = fine)
docker images                   # list locally cached images
```

### Compose lifecycle (run from directory containing `docker-compose.yaml`)

```bash
# Validate the compose file parses correctly without starting anything
docker compose config > /dev/null && echo "✓ compose file is valid"

# One-shot init (used for first-time Airflow DB migration + admin user creation)
docker compose up airflow-init

# Start all services in detached/background mode
docker compose up -d

# See all services and their health status
docker compose ps

# Stop all services (preserves data in named volumes)
docker compose down

# ⚠️ destructive — Stop services AND delete named volumes (wipes Postgres metadata)
docker compose down -v
```

### Logs & debugging

```bash
# Tail logs from one service, live (Ctrl+C only stops the log stream, not the container)
docker compose logs -f airflow-webserver

# Last 80 lines from a service (useful for "what just happened?")
docker compose logs --tail=80 airflow-webserver

# Drop into a shell inside a running container
docker compose exec airflow-scheduler bash
```

### Image management

```bash
# Pull a specific image directly (bypasses compose's parallel pulls)
docker pull apache/airflow:2.10.3-python3.11

# Filter image list by name
docker images | grep airflow

# ⚠️ destructive — Clear caches, dead containers, half-pulled layers, unused volumes
docker system prune -af --volumes
```

**When to use prune:** if a Docker pull or build hangs after a Ctrl+C, run prune + restart Docker Desktop. Most "stuck" Docker issues clear with this combo.

### Common pattern: reset Docker when something is wedged

```bash
# 1. Cancel any compose operation
docker compose down

# 2. Clear orphaned state
docker system prune -af --volumes

# 3. Quit Docker Desktop entirely (whale icon → Quit Docker Desktop)
# 4. Wait ~10 seconds
# 5. Reopen Docker Desktop and wait for whale icon to stop animating
```

---

## 5. AWS CLI

### Install

```bash
# 🍎 macOS — official .pkg installer (recommended; avoids Homebrew Tier 2 issues on older Intel Macs)
curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o "AWSCLIV2.pkg"
sudo installer -pkg AWSCLIV2.pkg -target /

# 🐧 Linux/WSL2 — official installer
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
rm -rf awscliv2.zip aws/

# Verify (both platforms)
aws --version                   # should print: aws-cli/2.x.x ...
```

### Setup

```bash
# Configure credentials (will prompt for Access Key ID, Secret, Region, Output format)
aws configure

# Verify which credentials are active
aws sts get-caller-identity     # shows the IAM identity you're authenticated as
```

### S3 operations

```bash
# List contents of a bucket (empty result = bucket exists but empty; that's fine)
aws s3 ls s3://<your-bucket-name>/

# Copy a local file to S3
aws s3 cp /tmp/test.txt s3://<your-bucket-name>/test/test.txt

# ⚠️ Remove an object from S3 (irreversible without versioning)
aws s3 rm s3://<your-bucket-name>/test/test.txt

# Recursively list everything in a bucket prefix
aws s3 ls s3://<your-bucket-name>/yellow/ --recursive
```

**Habit worth building:** clean up test artifacts immediately. Stray files in landing zones cause confusion in future `LIST` calls and, in production, sometimes get accidentally picked up by ingestion jobs.

---

## 6. Package Management

### 🍎 macOS — Homebrew

```bash
# Verify Homebrew is installed
brew --version

# Install a CLI tool
brew install <package>          # example: brew install python@3.11

# Install a GUI/cask app (pre-built binary, avoids Tier 2 compile issues)
brew install --cask docker

# Update Homebrew's package index
brew update

# Find Homebrew's install prefix
brew --prefix                   # typically /usr/local on Intel, /opt/homebrew on Apple Silicon
```

**Tier 2 gotcha:** On older Intel Macs, some Homebrew formulas don't have pre-built bottles and must compile from source. Symptom: `brew install` runs for 30+ minutes. Workaround: use vendor-provided installers when available (e.g., AWS .pkg, Docker Desktop dmg).

### 🐧 Linux/WSL2 — apt (Debian/Ubuntu)

```bash
# Update the package index (do this before installing)
sudo apt update

# Install a package
sudo apt install -y <package>   # example: sudo apt install -y python3.11 python3-pip

# Upgrade all installed packages
sudo apt upgrade -y

# Search for a package by name
apt search <keyword>

# Show details about an installed package
apt show <package>

# ⚠️ Remove a package (and its config files)
sudo apt purge <package>
```

**WSL2 note:** `apt update` should be the first thing you run on a fresh WSL2 install. Ubuntu's package index is often stale on the first boot.

---

## 7. Python Environments

```bash
# Verify Python version (need 3.11+ for this project)
python3 --version

# 🍎 macOS — install Python 3.11 via Homebrew
brew install python@3.11

# 🐧 Linux/WSL2 — install Python 3.11 via apt
sudo apt install -y python3.11 python3.11-venv python3-pip
```

*(More entries will be added in Phase 2 when we set up venvs and pip for ingestion code.)*

---

## 8. File System & Inspection

### Navigation & inspection

```bash
pwd                             # print working directory
ls -la                          # list all files including hidden, with details
ls -la docker-compose.yaml      # check a specific file exists
cd ~/Projects/nyc-taxi-elt      # navigate to project root (~ = home dir on both platforms)
```

### File creation patterns used in this project

```bash
# Create a multi-line file using a heredoc (the 'EOF' is a delimiter you can name anything)
# Single-quoted 'EOF' prevents shell variable expansion inside the content
cat > .gitignore <<'EOF'
.env
.env.*
!.env.example
__pycache__/
EOF

# Create a directory and any missing parent directories at once
mkdir -p airflow/dags airflow/plugins ingestion/src dbt/models/staging
```

### Inspect file contents

```bash
cat <file>                      # print whole file
head -3 <file>                  # first 3 lines
tail -50 <file>                 # last 50 lines
wc -l <file>                    # count lines
```

### Find files

```bash
# Find files by name pattern (works on both platforms)
find . -name "*.py"                                   # Python files in current tree
find . -name "docker-compose.yaml" -type f            # restrict to regular files

# 🍎 macOS — find a specific file inside an .app bundle (e.g., Docker CLI)
find /Applications/Docker.app -name docker -type f 2>/dev/null
```

---

## 9. Diagnostic & Network Tools

### Network reachability

```bash
# HTTP HEAD request — does the server respond? Don't care about content.
curl -I https://registry-1.docker.io/v2/
# Expected: HTTP/1.1 401 Unauthorized (the 401 is correct — means we reached the server)

# Resolve a hostname to verify DNS is working
nslookup registry-1.docker.io

# Alternative DNS lookup (often more readable output)
dig registry-1.docker.io
```

### Port & process inspection

```bash
# Find what process is bound to a port (useful when "port already in use")
# 🍎 macOS — lsof works out of the box
lsof -i :8080

# 🐧 Linux/WSL2 — install lsof first if not present
sudo apt install -y lsof
sudo lsof -i :8080

# 🐧 Linux/WSL2 alternative — ss (often pre-installed)
ss -tulpn | grep :8080

# Check if a service inside Docker is listening (run from inside a container)
docker compose exec airflow-webserver curl --fail http://localhost:8080/health
```

---

## 10. Platform-Specific Gotchas

A small collection of "this works on platform A but not B" things you'll hit. These rarely come up in a tutorial but bite you in real work.

### File line endings (CRLF vs LF)

Windows tools sometimes save files with `\r\n` (CRLF) line endings; Linux/macOS tools expect `\n` (LF). Shell scripts with CRLF endings fail with cryptic "command not found" errors inside containers.

```bash
# 🐧 WSL2 — fix CRLF in a file edited on Windows
sudo apt install -y dos2unix
dos2unix <file>

# Tell git to auto-convert line endings on commit (run once, repo-wide)
git config --global core.autocrlf input    # on Linux/WSL2
git config --global core.autocrlf true     # on Windows native (rare for this project)
```

### Path conventions

```bash
# Both platforms — these all work in bash/zsh
cd ~/Projects                              # ~ = home directory
cd /home/<user>/Projects                   # 🐧 absolute Linux path
cd /Users/<user>/Projects                  # 🍎 absolute macOS path

# 🐧 WSL2 — accessing your Windows files (slow; avoid for project work)
cd /mnt/c/Users/<windows-user>/

# Open the current Linux directory in Windows Explorer (WSL2 only)
explorer.exe .
```

### Clipboard

```bash
# Copy a file's contents to clipboard
# 🍎 macOS:
cat <file> | pbcopy
# 🐧 WSL2:
cat <file> | clip.exe                      # uses Windows clipboard via interop
```

### Docker filesystem performance

🐧 **WSL2 specifically:** Docker volume mounts are dramatically faster on the Linux filesystem (`/home/...`) than on the Windows filesystem (`/mnt/c/...`). If a `dbt run` or container start feels slow, check that your project lives under `/home/`, not under `/mnt/c/`.

### Permissions on shared filesystems

🐧 **WSL2:** files created inside `/mnt/c/...` lose Linux permissions on each access. If you see "permission denied" on a script that should be executable, the file is probably on the Windows filesystem. Move it to `/home/...` and the issue disappears.

---

## 11. DuckDB SQL Idioms

DuckDB is an in-process columnar SQL engine — think "SQLite for analytics." It queries Parquet/CSV/JSON files directly without loading them entirely into memory, and its syntax is highly compatible with Snowflake, BigQuery, and Postgres.

### Install

```bash
# Inside an activated Python venv
pip install duckdb

# Verify
python3 -c "import duckdb; print(duckdb.__version__)"
```

### Query a Parquet file directly (no schema setup, no loading)

```python
import duckdb

# DuckDB streams chunks of the file through the query engine
result = duckdb.sql("""
    SELECT COUNT(*) FROM 'data/raw/yellow_tripdata_2024-01.parquet'
""")
print(result)
```

### Common profiling queries

```python
# Show schema (column names + types) without reading data rows
duckdb.sql("DESCRIBE SELECT * FROM 'file.parquet'")

# Summary statistics for every column at once
duckdb.sql("SUMMARIZE SELECT * FROM 'file.parquet'")

# Row count
duckdb.sql("SELECT COUNT(*) FROM 'file.parquet'")

# First 10 rows
duckdb.sql("SELECT * FROM 'file.parquet' LIMIT 10")

# Distinct values in a column
duckdb.sql("SELECT DISTINCT VendorID FROM 'file.parquet'")

# Count nulls per column (manual but useful pattern)
duckdb.sql("""
    SELECT
        COUNT(*) - COUNT(fare_amount) AS fare_amount_nulls,
        COUNT(*) - COUNT(passenger_count) AS passenger_nulls
    FROM 'file.parquet'
""")
```

### Querying multiple files at once with glob

```python
# Read every Yellow Taxi file in a directory at once
duckdb.sql("""
    SELECT COUNT(*)
    FROM 'data/raw/yellow_tripdata_*.parquet'
""")
```

DuckDB automatically unions matching files. Powerful for cross-month profiling.

### When to use DuckDB vs other tools

- **Use DuckDB for:** local profiling, ad-hoc analytical queries on Parquet/CSV, lightweight transformation pipelines, anywhere you'd reach for Pandas + a query engine
- **Don't use DuckDB for:** transactional workloads (use Postgres), distributed computation across many machines (use Spark), production warehouses (use Snowflake/BigQuery)

---

## 12. DuckDB ↔ Pandas Equivalencies

A reference table mapping common Pandas operations to their DuckDB SQL equivalents. Useful when you know one and need to do the same thing in the other.

| Task | DuckDB SQL | Pandas equivalent |
|---|---|---|
| Show schema (column types) | `DESCRIBE SELECT * FROM 'file.parquet'` | `df.info()` or `df.dtypes` |
| Row count | `SELECT COUNT(*) FROM 'file.parquet'` | `len(df)` |
| First N rows | `SELECT * FROM 'file.parquet' LIMIT 10` | `df.head(10)` |
| Summary statistics | `SUMMARIZE SELECT * FROM 'file.parquet'` | `df.describe()` |
| Distinct values in a column | `SELECT DISTINCT col FROM 'file.parquet'` | `df['col'].unique()` |
| Group by + count | `SELECT col, COUNT(*) FROM 'file.parquet' GROUP BY col` | `df.groupby('col').size()` |
| Filter rows | `SELECT * FROM 'file.parquet' WHERE col > 100` | `df[df['col'] > 100]` |
| Select columns | `SELECT col1, col2 FROM 'file.parquet'` | `df[['col1', 'col2']]` |
| Sort | `SELECT * FROM 'file.parquet' ORDER BY col DESC` | `df.sort_values('col', ascending=False)` |
| Aggregate (mean) | `SELECT AVG(col) FROM 'file.parquet'` | `df['col'].mean()` |
| Multiple aggregates | `SELECT MIN(col), MAX(col), AVG(col) FROM 'file.parquet'` | `df['col'].agg(['min', 'max', 'mean'])` |
| Unique count | `SELECT COUNT(DISTINCT col) FROM 'file.parquet'` | `df['col'].nunique()` |
| Null count | `SELECT COUNT(*) - COUNT(col) FROM 'file.parquet'` | `df['col'].isna().sum()` |

### Memory model difference (the most important distinction)

```python
# Pandas — loads the entire file into RAM, then queries the in-memory DataFrame
df = pd.read_parquet("yellow_tripdata_2024-01.parquet")
df.shape
# Memory cost: ~3GB resident in RAM for one month

# DuckDB — never loads the full file; streams chunks through the query
duckdb.sql("SELECT COUNT(*) FROM 'yellow_tripdata_2024-01.parquet'")
# Memory cost: ~50MB peak
```

The implication for data engineering work: **DuckDB lets you profile files larger than your RAM**. You can ask questions of a 100GB Parquet file on a laptop with 16GB of memory, as long as your individual query results fit.

---

## How to Add to This File

Whenever a new command or pattern proves useful in the project, add it under the appropriate section with:

1. The command itself in a code block
2. A `# comment` explaining what it does, especially if non-obvious
3. A brief "when to use" note if the command isn't self-explanatory
4. The `⚠️ destructive` marker if it can't be safely retried

Sections to add as the project grows:
- **dbt commands** (Phase 3)
- **Snowflake CLI / SnowSQL** (any phase)
- **Airflow CLI commands** (Phase 4)
- **Terraform** (Project 3)
- **GitHub Actions / `gh` CLI** (Phase 5)

---

*This cheatsheet is a living document. Each phase will append new commands as they're introduced.*
