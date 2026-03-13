# Codebase Structure

**Analysis Date:** 2026-03-12

## Directory Layout

```
stock-image-gen/
├── .planning/                      # GSD planning and analysis documents
│   └── codebase/                   # Codebase analysis output
├── .git/                           # Git repository metadata
├── generate.py                     # Main CLI entrypoint and orchestration
├── providers.py                    # Image generation provider implementations
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment variable template
├── .gitignore                      # Git ignore rules
└── output/                         # Generated images directory (gitignored)
    └── {age}/                      # Subdirectory per age group
        └── {ethnicity}/            # Subdirectory per ethnicity
            └── *.png               # Generated image files
```

## Directory Purposes

**.planning/codebase/:**
- Purpose: GSD-generated analysis documents (ARCHITECTURE.md, STRUCTURE.md, etc.)
- Contains: Markdown documentation files
- Key files: `ARCHITECTURE.md`, `STRUCTURE.md`
- Status: Generated; committed to git

**output/:**
- Purpose: Generated images organized by demographic attributes
- Contains: PNG image files in nested folder structure
- Organization: `output/{age_slug}/{ethnicity_slug}/{pose}_{prop}_{counter}.png`
- Status: Generated at runtime; gitignored (appears in .gitignore as "output/")

## Key File Locations

**Entry Points:**
- `generate.py`: Main CLI script; runs `python generate.py` from project root

**Core Logic:**
- `generate.py` (lines 1-284): Interactive CLI, prompt building, task orchestration
- `providers.py` (lines 1-175): Provider registry, async generators, HTTP request handling

**Configuration:**
- `.env.example`: Template showing required environment variables (OPENAI_API_KEY, FAL_KEY, STABILITY_API_KEY)
- `.env` (gitignored): Runtime environment file with actual API keys

**Build/Dependencies:**
- `requirements.txt`: Python package dependencies (httpx, questionary, python-dotenv)

**Version Control:**
- `.gitignore`: Excludes output/, .env, __pycache__/, *.pyc, .venv/

## Naming Conventions

**Files:**
- `generate.py`: Module name matches primary function (CLI generation)
- `providers.py`: Module name describes contents (provider implementations)
- `requirements.txt`: Standard Python conventions
- `.env.example`: Standard dotenv convention

**Directories:**
- Output structure uses kebab-case slugified directory names:
  - `elementary-6-10/` for "Elementary (6-10)"
  - `east-asian/` for "East Asian"
  - `sitting-at-a-desk-writing/` for "sitting at a desk writing"

**Functions (Python):**
- `select_provider()`, `select_variables()`: Interactive UI functions (snake_case, descriptive)
- `build_prompts()`: Core business logic function
- `_generate_openai()`, `_generate_fal()`: Provider implementations (leading underscore for private)
- `_request()`: Helper function (leading underscore for private)
- `generate_batch()`: Public async orchestrator

**Variables/Constants (Python):**
- `ETHNICITIES`, `AGE_GROUPS`, `POSES`, `PROPS`, `PROMPT_TEMPLATE`: Module-level constants (UPPERCASE for immutable data)
- `PROVIDERS`, `_GENERATORS`: Registry dicts (UPPERCASE for module constants, leading underscore for private)
- `provider_name`, `variables`, `tasks`: Local variables (snake_case)

**Slugs (Filesystem):**
- Function: `slugify()` (line 159-170)
- Transformation: lowercase, replace " / " with "-", replace "/" with "-", replace spaces with "-", remove parentheses/commas/apostrophes
- Examples: "East Asian" → "east-asian", "Elementary (6-10)" → "elementary-6-10"

## Where to Add New Code

**New Provider (Image Generation Service):**
1. Add entry to `PROVIDERS` dict in `providers.py`:
   ```python
   "Provider Name": {
       "env_var": "PROVIDER_API_KEY",
       "cost_per_image": 0.XX,
       "max_concurrent": N,
   }
   ```
2. Implement async generator function `_generate_provider_name()` in `providers.py`
3. Register function in `_GENERATORS` dict
4. Add environment variable to `.env.example`

**New Variable Type (Race/Age/Pose/Props):**
1. Add to appropriate constant list in `generate.py`:
   - `ETHNICITIES`, `AGE_GROUPS` (dict), `POSES`, or `PROPS`
2. Update `PROMPT_TEMPLATE` if new variable type requires new placeholder
3. Update `select_variables()` to include new questionary prompt if needed
4. Update `build_prompts()` to include new variable in product() if changing structure

**New CLI Flag/Argument:**
1. Add to `argparse.ArgumentParser` in `main()` function
2. Handle argument in main() logic

**Bug Fix/Refactor:**
- Small changes: Modify the relevant function in `generate.py` or `providers.py`
- Extraction of helper: Add new private function to either module (prefix with `_`)
- Shared utility across modules: Add to appropriate module, import in the other

## Special Directories

**output/ (Runtime Generated):**
- Purpose: Contains all generated images
- Generated: Yes (created at runtime by image generation functions)
- Committed: No (ignored in .gitignore)
- Cleanup: Safe to delete anytime; images regenerated on next run
- Structure: Nested folders by age_slug/ethnicity_slug created by `mkdir(parents=True, exist_ok=True)` in provider generators

**.planning/ (Analysis):**
- Purpose: GSD-generated documentation
- Generated: Yes (by `gsd:map-codebase` command)
- Committed: Yes
- Contents: ARCHITECTURE.md, STRUCTURE.md, CONVENTIONS.md, TESTING.md, CONCERNS.md (as generated)

**.git/:**
- Purpose: Version control metadata
- Status: Git repository initialized with initial commit

## Configuration Files

**`.env.example`:**
- Shows template for OPENAI_API_KEY, FAL_KEY, STABILITY_API_KEY
- Optional: IMAGE_PROVIDER for skipping provider selection prompt
- Copied to `.env` and populated with actual keys before running

**`requirements.txt`:**
- Lists dependencies: httpx, questionary, python-dotenv
- Versions: >=27 (httpx), >=2.0 (questionary), >=1.0 (python-dotenv)

## Module Dependencies

**generate.py imports:**
- argparse (stdlib): CLI argument parsing
- asyncio (stdlib): Async coordination
- json (stdlib): Config save/load
- os (stdlib): Environment variable access
- sys (stdlib): Exit codes, stdout writing
- itertools.product (stdlib): Combinatorial generation
- pathlib.Path (stdlib): Filesystem path handling
- questionary: Interactive CLI prompts
- dotenv.load_dotenv: Load .env file
- providers module: PROVIDERS registry, generate_batch() function

**providers.py imports:**
- asyncio (stdlib): Async/semaphore
- base64 (stdlib): Decode image data from APIs
- sys (stdlib): Progress output
- httpx: Async HTTP client

---

*Structure analysis: 2026-03-12*
