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
# Clone and install
git clone <repo-url>
cd stock-image-gen
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
2. **Ethnicities** — East Asian, South Asian, Black, Hispanic, White, Middle Eastern, etc.
3. **Age groups** — Elementary, Middle School, High School, College
4. **Poses** — sitting at desk, standing with backpack, reading, presenting, etc.
5. **Props** — backpack, laptop, books, art supplies, lab coat, etc.
6. **Images per combination** — how many variants of each combination to generate

A cost estimate is shown before generation begins.

### Save and reuse configs

```bash
# Save selections for later
python generate.py --save-config my-run.json

# Re-run with saved config (no prompts)
python generate.py --config my-run.json

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
