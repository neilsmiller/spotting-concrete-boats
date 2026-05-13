# spotting-concrete-boats

Analyze US federal government solicitations to spot concrete boats

For more information about this project, check out a series of articles I am writing in partnership with the Niskanen Center's State Capacity team:

- [Spotting 'concrete boats': Why 'solicitation sins' doom contracts to struggle: part 1](https://www.niskanencenter.org/spotting-concrete-boats-why-solicitation-sins-doom-contracts-to-struggle-part-1/ )
- [Part 2](https://www.niskanencenter.org/spotting-concrete-boats-why-solicitation-sins-doom-contracts-to-struggle/)

---

## Setup

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/getting-started/installation/) - Fast Python package manager
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh  # macOS/Linux
  ```

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd spotting-concrete-boats

# Create and activate virtual environment
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies (includes pre-commit as a dev dependency)
uv sync --all-extras # On Windows: uv sync --all-extras

# Set up pre-commit hooks to run automatically on commit
.venv/bin/pre-commit install # On Windows: pre-commit install

# Copy the example env file and add your API keys
cp .env.example .env # On Windows: copy .env.example .env
```

The project uses `uv` for dependency management and `uv.lock` for reproducible builds. All dependencies are defined in `pyproject.toml`.

### Working with Dependencies

```bash
# Add a new package
uv add package-name

# Add a development dependency
uv add --dev package-name

# Update dependencies
uv sync --all-extras
```

### SAM.gov API Key

This project uses the [SAM.gov Opportunities API](https://open.gsa.gov/api/get-opportunities-public-api/) to search and download federal contract solicitations. You'll need an API key to run the extraction notebook.

**Getting your API key:**

1. Go to [sam.gov](https://sam.gov) and sign in (you'll be redirected to Login.gov — create an account if you don't have one).
2. Once signed in, go to your **Workspace** and select **Profile**.
3. Find the **"Public API Key"** field and click **"Request API Key"**.
4. Click the **eye icon**, enter the one-time password sent to your email, and click **Submit**.
5. Copy and securely store your API key.

> **Note:** API keys rotate automatically every 90 days.

**Rate limits:**

| Access Level | Requests/Day |
|---|---|
| Public (basic key) | 10 |
| Registered Entity User | 1,000 |
| Federal System User (.gov/.mil) | 10,000 |

The basic tier (10 requests/day) is enough to get started. To request higher limits, register your entity in SAM.gov and submit a role request with a business justification.

**Setting up your environment:**

```bash
# Copy the example env file and fill in your keys
cp .env.example .env
```

Then edit `.env` with your API keys:
```
SAM_API_KEY=your_sam_gov_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

The notebooks load these automatically via `python-dotenv`. The `.env` file is gitignored and will never be committed.

> **Google Colab:** If running in Colab instead of locally, add your keys via the **Secrets** panel (key icon in the left sidebar) with the names `SAM_API_KEY` and `ANTHROPIC_API_KEY`.

### Pre-commit Hooks

Pre-commit hooks are installed as a dev dependency and run automatically before each commit to maintain code quality:
- **Ruff** - Code formatting and linting
- **nbstripout** - Strips notebook outputs before commit

After running `uv sync --all-extras`, install the git hooks with `.venv/bin/pre-commit install` (see Installation section above).

---

## Project Structure

```
.
├── spotting_concrete_boats/   # Installable Python package
│   ├── sam.py                # SAM.gov API client
│   ├── documents.py          # PDF/DOCX/XLSX text extraction
│   ├── analyzer.py           # LLM-powered solicitation analysis
│   └── prompts/              # Analysis prompt templates (sins & virtues)
├── notebooks/                 # Jupyter notebooks for extraction & analysis
├── scripts/                   # CLI runner scripts
├── docs/                      # Reference articles on solicitation sins
├── .env.example               # Template for environment variables (API keys)
├── pyproject.toml             # Project configuration and dependencies
├── uv.lock                    # Locked dependency versions
└── .pre-commit-config.yaml    # Code quality checks configuration
```

---

## Development Notes

- Pre-commit hooks auto-fix most formatting issues - if a commit fails, stage the changes and commit again
- The `.venv` directory is gitignored and should not be committed
- `uv.lock` should be committed to ensure reproducible environments
