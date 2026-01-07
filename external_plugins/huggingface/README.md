# Hugging Face

[Hugging Face](https://huggingface.co) is the leading platform for machine learning models, datasets, and applications. This plugin provides both MCP server integration for interacting with the Hugging Face Hub and access to the official [Hugging Face Skills](https://github.com/huggingface/skills) for AI/ML development workflows.

## Features

### MCP Server Integration

Connect to the Hugging Face MCP server for direct access to:

- **Model Search & Discovery** - Find ML models by task, library, or author
- **Dataset Search** - Discover and explore datasets on the Hub
- **Paper Search** - Find ML research papers with semantic search
- **Space Discovery** - Search and interact with Hugging Face Spaces
- **Hub Repository Details** - Get comprehensive info about models, datasets, and spaces
- **Documentation Search** - Search Hugging Face product and library documentation
- **Image Generation** - Generate images using hosted models
- **Compute Jobs** - Run Python scripts on Hugging Face CPU/GPU infrastructure

### Hugging Face Skills

The official [huggingface/skills](https://github.com/huggingface/skills) repository provides comprehensive AI/ML development skills:

| Skill | Description |
|-------|-------------|
| **hf-datasets** | Create structured training datasets with prompts, templates, and scripts |
| **hf-evaluation** | Orchestrate evaluation jobs, generate reports, and map metrics |
| **hf-trainer** | Comprehensive model training with SFT examples, GGUF conversion, and cost estimation |
| **hf-papers** | Publish and manage research papers on Hugging Face Hub |
| **hf-tool-builder** | Build and deploy tools on Hugging Face |

## Setup

### 1. Authenticate with Hugging Face

Get a Hugging Face API token from [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens).

Add to your shell profile (`.bashrc`, `.zshrc`, etc.):

```bash
export HF_TOKEN="your-token-here"
```

Reload your shell or run `source ~/.zshrc`.

### 2. Install Skills (Optional)

For the full skills experience, register the Hugging Face skills as an additional plugin marketplace:

```
/plugin marketplace add huggingface/skills
```

Then install individual skills:

```
/plugin install hf-datasets@huggingface-skills
/plugin install hf-trainer@huggingface-skills
/plugin install hf-evaluation@huggingface-skills
/plugin install hf-cli@huggingface-skills
```

## MCP Tools Available

### Search & Discovery
- `model_search` - Find ML models with filtering by task, library, author
- `dataset_search` - Search datasets with tag filtering
- `paper_search` - Semantic search for ML research papers
- `space_search` - Find Hugging Face Spaces

### Hub Operations
- `hub_repo_details` - Get detailed info for models, datasets, or spaces
- `hf_doc_search` - Search Hugging Face documentation
- `hf_doc_fetch` - Fetch documentation pages

### Interactive Tools
- `use_space` - Access and interact with Hugging Face Spaces
- `dynamic_space` - Perform tasks with Spaces (image generation, OCR, TTS, etc.)
- `hf_jobs` - Run compute jobs on Hugging Face infrastructure

### Generation
- `flux1_schnell_infer` - Generate images with Flux 1 Schnell

## Example Usage

Ask Claude Code to:

- "Search for text-to-image models on Hugging Face"
- "Find datasets for sentiment analysis in English"
- "What are the latest papers on retrieval-augmented generation?"
- "Use the HF trainer skill to fine-tune a model on my dataset"
- "Generate an image of a sunset over mountains"
- "Show me the documentation for the transformers library"

## Documentation

- [Hugging Face Hub](https://huggingface.co/docs/hub)
- [Hugging Face Skills Repository](https://github.com/huggingface/skills)

