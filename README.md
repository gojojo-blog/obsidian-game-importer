# Obsidian Game Importer

This repository contains a simple Python script to populate an Obsidian vault with game entries fetched from the [RAWG](https://rawg.io/apidocs) video game database.

## Prerequisites

1. **RAWG API key** – create an account at [rawg.io/apidocs](https://rawg.io/apidocs) and generate a key.
2. Python 3.12+
3. Install dependencies:

```bash
pip install requests PyYAML
```

## Usage

Set your RAWG API key in the `RAWG_API_KEY` environment variable or pass `--api-key` on the command line.

```bash
python rawg_importer.py the-witcher-3-wild-hunt
```

Notes are written to `/Users/joelplourde/Documents/Obsidian/Vaults/Jojo/04 - Entertainment/00 - Hobbies/Games` by default. Use `--output-dir` to override the destination.

Each run creates or updates a Markdown note per game slug in the target directory:

- A cover image is downloaded to an `images/` subfolder and embedded in the note.
- The YAML front matter gains a `progress` field (default `backlog`). If a note already exists, its current `progress` value is preserved.
- Platforms, genres and release date are stored for quick reference.
- Blank `physical_game`, `physical_edition` and `collection_image` fields are provided for tracking physical copies and custom art.

## Notes

This project is a starting point. Extend the importer as needed for your vault organization.
