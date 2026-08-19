#!/usr/bin/env python3
"""Build deterministic Claude Code adapters from portable Agent Plugins."""

from __future__ import annotations

import argparse
import filecmp
import json
import shutil
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGINS = ROOT / "plugins"
ADAPTER_ROOT = ROOT / "client-adapters" / "claude-code"
OUTPUT = ADAPTER_ROOT / "plugins"
SOURCES = ADAPTER_ROOT / "sources"
CONFIG = ADAPTER_ROOT / "config.json"
MARKETPLACE = ROOT / ".claude-plugin" / "marketplace.json"
HERMES_OUTPUT = ROOT / "hermes-skills"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(data: dict) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def adapter_manifest(portable: dict) -> dict:
    fields = (
        "name",
        "version",
        "description",
        "author",
        "homepage",
        "repository",
        "license",
        "keywords",
    )
    return {key: portable[key] for key in fields if key in portable}


def copy_tree(source: Path, target: Path) -> None:
    if source.exists():
        shutil.copytree(source, target, dirs_exist_ok=True)


def build_adapter(plugin_dir: Path, target: Path) -> None:
    portable = load_json(plugin_dir / "plugin.json")
    target.mkdir(parents=True)
    manifest_dir = target / ".claude-plugin"
    manifest_dir.mkdir()
    (manifest_dir / "plugin.json").write_text(
        dump_json(adapter_manifest(portable)), encoding="utf-8"
    )

    copy_tree(plugin_dir / "skills", target / "skills")

    for legal_name in ("LICENSE", "LICENSE.md", "NOTICE", "NOTICE.md"):
        legal_file = plugin_dir / legal_name
        if legal_file.exists():
            shutil.copy2(legal_file, target / legal_name)

    mcp_path = plugin_dir / "mcp.json"
    if mcp_path.exists():
        mcp = load_json(mcp_path)
        mcp.pop("$schema", None)
        (target / ".mcp.json").write_text(dump_json(mcp), encoding="utf-8")

    copy_tree(SOURCES / plugin_dir.name, target)


def build_output(target_root: Path, excluded: set[str]) -> list[dict]:
    entries: list[dict] = []
    for plugin_dir in sorted(PLUGINS.iterdir()):
        manifest_path = plugin_dir / "plugin.json"
        if not manifest_path.exists() or plugin_dir.name in excluded:
            continue
        portable = load_json(manifest_path)
        build_adapter(plugin_dir, target_root / plugin_dir.name)
        entries.append(
            {
                "name": portable["name"],
                "source": f"./client-adapters/claude-code/plugins/{plugin_dir.name}",
                "description": portable["description"],
                "version": portable["version"],
            }
        )
    return entries


def expected_marketplace(entries: list[dict]) -> dict:
    marketplace = load_json(MARKETPLACE)
    marketplace["plugins"] = entries
    return marketplace


def build_hermes_output(target_root: Path, copies: list[dict]) -> None:
    for item in copies:
        source = PLUGINS / item["plugin"] / "skills" / item["skill"]
        destination = target_root / item.get("destination", item["skill"])
        copy_tree(source, destination)


def directories_match(left: Path, right: Path) -> bool:
    comparison = filecmp.dircmp(left, right)
    if comparison.left_only or comparison.right_only or comparison.funny_files:
        return False
    if any(not filecmp.cmp(left / name, right / name, shallow=False) for name in comparison.common_files):
        return False
    return all(
        directories_match(left / name, right / name)
        for name in comparison.common_dirs
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    config = load_json(CONFIG) if CONFIG.exists() else {}
    excluded = set(config.get("exclude_from_claude_marketplace", []))
    hermes_copies = config.get("hermes_skill_copies", [])

    with tempfile.TemporaryDirectory(prefix="claude-adapters-") as temp_dir:
        expected_root = Path(temp_dir) / "plugins"
        expected_root.mkdir()
        entries = build_output(expected_root, excluded)
        marketplace_text = dump_json(expected_marketplace(entries))
        expected_hermes = Path(temp_dir) / "hermes-skills"
        expected_hermes.mkdir()
        build_hermes_output(expected_hermes, hermes_copies)

        if args.check:
            clean = OUTPUT.exists() and directories_match(expected_root, OUTPUT)
            clean = clean and MARKETPLACE.read_text(encoding="utf-8") == marketplace_text
            if hermes_copies:
                clean = clean and HERMES_OUTPUT.exists()
                clean = clean and directories_match(expected_hermes, HERMES_OUTPUT)
            if not clean:
                print("Claude adapters or marketplace metadata are out of date.", file=sys.stderr)
                return 1
            print("Claude adapters and marketplace metadata are current.")
            return 0

        if OUTPUT.exists():
            shutil.rmtree(OUTPUT)
        shutil.copytree(expected_root, OUTPUT)
        MARKETPLACE.write_text(marketplace_text, encoding="utf-8")
        if hermes_copies:
            if HERMES_OUTPUT.exists():
                shutil.rmtree(HERMES_OUTPUT)
            shutil.copytree(expected_hermes, HERMES_OUTPUT)
        print(f"Built {len(entries)} Claude Code adapters.")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
