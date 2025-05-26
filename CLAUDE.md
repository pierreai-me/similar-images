# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Setup
```bash
make create-venv  # Create virtual environment and install dependencies
```

### Development
```bash
make test         # Run unit tests (pytest tests/unit)
make integration-test  # Run integration tests (pytest tests/integration)
make ruff         # Format and lint code with ruff
make all          # Run both ruff and test
```

### Main CLI Usage
```bash
# Basic keyword search
si.py -q "cats" -n 10 -o output_dir

# Advanced search with database and filtering
si.py -q "(small|big) (cats|dogs)" --db db.jsonl --min-size=1500,1200 -t 5 -g filter_config.json

# Reverse image search (requires --visible mode)
si.py -p /path/to/image.jpg --visible

# Evaluation mode against local test images
si.py -l /path/to/test/images -o results -g evaluation_filter.json
```

## Architecture

**Similar Images** is a Python automation tool that uses LLMs to search, filter, and download images from web sources. The system follows a **pipeline architecture** with async processing.

### Core Pipeline Flow
1. **Image Sources** generate URLs from queries or existing images
2. **Scraper** orchestrates the download and filtering pipeline
3. **Filters** apply 4-stage filtering: URL → Contents → Hashes → LLM
4. **Database** provides simple JSONL storage for deduplication

### Key Components

**Entry Points:**
- `si.py` - Main CLI using Typer
- `scripts/scrape.py` - Configuration-based batch processing
- `scripts/evaluate.py` - Filter evaluation tool

**Image Sources (`similar_images/image_sources.py`):**
- `BrowserQuerySource` - Text searches via Bing
- `BrowserImageSource` - Reverse image search via Bing
- `GoogleQuerySource` - Text searches via Google
- `GoogleImageSource` - Reverse image search via Google
- `LocalFileImageSource` - Local file processing for evaluation

**Browser Automation:**
- `bing_selenium.py` - Selenium-based Bing automation
- `google_playwright.py` - Playwright-based Google automation (supports CAPTCHA via Puzzler)

**4-Stage Filter System (`similar_images/filters/`):**
1. **URL Stage** - `DbUrlFilter` (check previously seen URLs)
2. **Contents Stage** - `DbExactDupFilter`, `ImageFilter` (size/area filtering)
3. **Hashes Stage** - `DbNearDupFilter` (perceptual hash comparison)
4. **Expensive Stage** - `GeminiFilter` (LLM-based content analysis)

**Core Orchestration:**
- `scraper.py` - Main orchestrator coordinating sources, filters, and storage
- `crappy_db.py` - Simple JSONL database with URL/hash indexing
- `types.py` - Pydantic models for configuration and data structures

### LLM Integration
- `gemini.py` - Google Gemini API integration for image analysis
- Requires `GEMINI_API_KEY` environment variable
- Uses JSON configuration files to define filter criteria

### Key Design Patterns
- **Async Pipeline** - Heavy use of asyncio for concurrent processing
- **Filter Chain** - Pluggable filter system with different execution stages
- **Strategy Pattern** - Multiple image source implementations
- **Configuration-Driven** - JSON-based configuration for complex workflows
- **Fail-Fast** - Early filtering to avoid expensive operations

The architecture supports both simple CLI usage and complex batch processing scenarios with clear separation of concerns and extensibility.