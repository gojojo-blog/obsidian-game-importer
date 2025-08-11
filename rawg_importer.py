# Small utility to import RAWG game data into Markdown files for Obsidian.

import os
import argparse
from pathlib import Path
from urllib.parse import urlparse

import requests
import yaml

# Endpoint template to fetch a single game by slug
API_URL = "https://api.rawg.io/api/games/{slug}?key={key}"

# Default location in the user's vault for new game notes
DEFAULT_OUTPUT_DIR = "/Users/joelplourde/Documents/Obsidian/Vaults/Jojo/04 - Entertainment/00 - Hobbies/Games"


def fetch_game(slug: str, api_key: str) -> dict:
    # Retrieve detailed information for a game from RAWG by slug
    url = API_URL.format(slug=slug, key=api_key)
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError(f"Failed to fetch {slug}: {exc}") from exc
    return resp.json()


def read_existing_fields(file_path: Path) -> dict:
    # Return selected front matter fields so manual edits are preserved
    defaults = {
        "progress": "backlog",
        "physical_game": "",
        "physical_edition": "",
        "collection_image": "",
    }
    if not file_path.exists():
        return defaults

    lines = file_path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return defaults

    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            front = "\n".join(lines[1:i])
            data = yaml.safe_load(front) or {}
            return {k: data.get(k, v) for k, v in defaults.items()}
    return defaults


def download_image(url: str, output_dir: Path, base_name: str) -> str | None:
    # Download an image to the vault and return its relative path
    if not url:
        return None

    images_dir = output_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    # Determine file extension from the URL path
    path = urlparse(url).path
    ext = os.path.splitext(path)[1] or ".jpg"
    image_path = images_dir / f"{base_name}{ext}"

    if not image_path.exists():
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
        except requests.RequestException as exc:
            print(f"Failed to download image {url}: {exc}")
            return None
        image_path.write_bytes(resp.content)

    # Return path relative to the Markdown file location
    return image_path.relative_to(output_dir).as_posix()


def write_markdown(game: dict, output_dir: Path) -> Path:
    # Create or update a Markdown file with game data
    output_dir.mkdir(parents=True, exist_ok=True)
    name = game.get("name", "unknown")

    # Sanitize file name for most filesystems
    file_name = "".join(c for c in name if c.isalnum() or c in (" ", "-", "_")).rstrip()
    file_path = output_dir / f"{file_name}.md"

    # Preserve selected fields if the file already exists
    existing = read_existing_fields(file_path)

    # Download cover image (if any) and store relative path
    cover_rel = download_image(game.get("background_image"), output_dir, file_name)

    front_matter = {
        "title": name,
        "released": game.get("released"),
        "platforms": [p["platform"]["name"] for p in game.get("platforms", [])],
        "genres": [g["name"] for g in game.get("genres", [])],
        "progress": existing["progress"],
        "physical_game": existing["physical_game"],
        "physical_edition": existing["physical_edition"],
        "collection_image": existing["collection_image"],
    }
    if cover_rel:
        front_matter["cover"] = cover_rel

    description = game.get("description_raw", "").strip()

    with file_path.open("w", encoding="utf-8") as f:
        # YAML front matter block
        f.write("---\n")
        yaml.safe_dump(front_matter, f, sort_keys=False, allow_unicode=True)
        f.write("---\n\n")

        # Heading and embedded image
        f.write(f"# {name}\n\n")
        if cover_rel:
            f.write(f"![]({cover_rel})\n\n")

        if description:
            f.write(description + "\n")
    return file_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Import RAWG game data into an Obsidian vault")
    parser.add_argument("slugs", nargs="+", help="Game slugs to fetch from RAWG")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR, help="Directory inside the vault to write files")
    parser.add_argument("--api-key", default=os.environ.get("RAWG_API_KEY"), help="RAWG API key (or set RAWG_API_KEY env var)")
    args = parser.parse_args()

    if not args.api_key:
        parser.error("RAWG API key required via --api-key or RAWG_API_KEY env var")

    output_dir = Path(args.output_dir)
    for slug in args.slugs:
        try:
            game = fetch_game(slug, args.api_key)
        except RuntimeError as exc:
            print(exc)
            continue
        path = write_markdown(game, output_dir)
        print(f"Wrote {path}")


if __name__ == "__main__":
    main()
