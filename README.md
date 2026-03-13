# Stock Image Generator

Batch generate diverse student stock photos using AI image generation APIs. Select combinations of ethnicity, age group, pose, and props through an interactive CLI, and the tool generates images in parallel — organized into folders by age and ethnicity.

## Supported Providers

| Provider | Model | Cost/Image | Notes |
|---|---|---|---|
| OpenAI GPT Image | gpt-image-1 | $0.009 | Best quality at low price |
| fal.ai Flux 2 Pro | flux-2-pro | $0.03 | Fast, excellent anatomy |
| Stability AI | SD 3.5 Large | $0.04 | Good quality, high concurrency |

You only need an API key for **one** provider.

## Setup

```bash
# Clone the repo
git clone <repo-url>
cd stock-image-gen

# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure API key(s)
cp .env.example .env
# Edit .env and add at least one API key
```

Requires Python 3.8+.

## Usage

### Interactive mode

```bash
python generate.py
```

You'll be prompted to select:
1. **Provider** — only providers with configured API keys are shown
2. **Image size** — resolution options vary by provider (e.g. square, portrait, landscape)
3. **Ethnicities** — East Asian, South Asian, Black, Hispanic, White, Middle Eastern, etc.
4. **Age groups** — Elementary, Middle School, High School, College
5. **Poses** — sitting at desk, standing with backpack, reading, presenting, etc.
6. **Props** — backpack, laptop, books, art supplies, lab coat, etc.
7. **Images per combination** — how many variants of each combination to generate

A cost estimate is shown before generation begins.

### Preview mode

By default, the tool asks if you'd like to run in **preview mode** — this generates 1 sample image per combination so you can check the results before committing to a full batch.

After previews generate, you can:
- **Approve** — proceed with the full batch using the current prompt
- **Adjust prompt** — add instructions like "zoom out more" or "show full body" that get appended to every prompt, then regenerate previews
- **Cancel** — stop without running the full batch

Preview images are saved to `output/_preview/` and overwrite on each iteration. Use `--no-preview` to skip this step.

### Save and reuse configs

```bash
# Save selections for later
python generate.py --save-config my-run.json

# Re-run with saved config (no prompts)
python generate.py --config my-run.json

# Skip preview mode, generate full batch immediately
python generate.py --no-preview

# Custom output directory
python generate.py --output ./photos
```

## Output Structure

Images are saved to `output/` (configurable with `--output`), organized by age group and ethnicity:

```
output/
├── elementary-6-10/
│   ├── east-asian/
│   │   ├── sitting-at-a-desk-writing_backpack_001.png
│   │   └── reading-a-book_laptop_001.png
│   ├── black-african-american/
│   └── ...
├── high-school-14-17/
│   ├── east-asian/
│   └── ...
└── ...
```

## Environment Variables

| Variable | Description |
|---|---|
| `OPENAI_API_KEY` | OpenAI API key |
| `FAL_KEY` | fal.ai API key |
| `STABILITY_API_KEY` | Stability AI API key |
| `IMAGE_PROVIDER` | Skip provider selection prompt (e.g. `OpenAI GPT Image`) |
