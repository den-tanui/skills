from __future__ import annotations
import json
import logging
import sys
from pathlib import Path

import click

from .config import Config, load_config, save_config, DEFAULT_CONFIG_PATH
from .db import Database

logger = logging.getLogger(__name__)


def _make_embedder(cfg: Config):
    """Try to load the real embedder; fall back to MockEmbedder."""
    try:
        import sentence_transformers  # noqa: F401 — check availability
        from .embedder import Embedder
        return Embedder(cfg.embedding.model, cfg.embedding.device)
    except Exception:
        from .embedder import MockEmbedder
        logger.info("Real embedder not available, using mock (results will be poor)")
        return MockEmbedder()


def _get_db(cfg: Config) -> Database:
    db_path = cfg.db_path
    parent = Path(db_path).parent
    parent.mkdir(parents=True, exist_ok=True)
    return Database(db_path)


# ── top-level group ──────────────────────────────────────────────────────────


@click.group()
@click.option("--db-path", "-d", help="Path to SQLite database (overrides config)")
@click.option("--config", "-c", "config_path", help="Path to config file")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
@click.pass_context
def cli(ctx, db_path, config_path, verbose):
    """Skill Manager — semantic search for OpenCode skills."""
    if verbose:
        logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    else:
        logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")

    cfg = load_config(Path(config_path) if config_path else None)
    if db_path:
        cfg.db_path = db_path

    ctx.ensure_object(dict)
    ctx.obj["config"] = cfg
    ctx.obj["db"] = _get_db(cfg)


# ── scan ─────────────────────────────────────────────────────────────────────


@cli.command()
@click.argument("dir_path", required=False)
@click.pass_context
def scan(ctx, dir_path):
    """Scan skill directories and index them.

    If DIR_PATH is provided, scan that directory only.
    Otherwise scan all directories tracked in config.
    """
    cfg: Config = ctx.obj["config"]
    db: Database = ctx.obj["db"]
    embedder = _make_embedder(cfg)

    if dir_path:
        expanded = str(Path(dir_path).expanduser().resolve())
        if not Path(expanded).exists():
            click.echo(f"Error: directory not found: {expanded}", err=True)
            sys.exit(1)
        from .scanner import scan_directory
        count = scan_directory(db, expanded, embedder, cfg)
    else:
        from .scanner import scan_all
        count = scan_all(db, cfg, embedder)

    click.echo(f"Indexed {count} skill(s)")


# ── search ───────────────────────────────────────────────────────────────────


@cli.command()
@click.argument("query")
@click.option("--top-k", "-k", default=10, show_default=True, help="Number of results")
@click.option("--json", "-j", "as_json", is_flag=True, help="Output as JSON")
@click.option("--dir", "-d", "dir_filter", help="Filter by source directory")
@click.pass_context
def search(ctx, query, top_k, as_json, dir_filter):
    """Search indexed skills by semantic similarity."""
    cfg: Config = ctx.obj["config"]
    db: Database = ctx.obj["db"]
    embedder = _make_embedder(cfg)

    from .search import search_skills
    results = search_skills(db, query, embedder, cfg, top_k=top_k, dir_filter=dir_filter)

    if as_json:
        click.echo(json.dumps([r.to_dict() for r in results], indent=2, default=str))
    else:
        if not results:
            click.echo("No results found.")
            return
        for r in results:
            score_str = f"{r.score:.4f}"
            click.echo(f"{score_str}  {r.name}")
            if r.description:
                click.echo(f"      {r.description}")
            click.echo(f"      {r.source_dir}")
            if r.file_count:
                click.echo(f"      {r.file_count} file(s)")
            click.echo()


# ── config sub-group ─────────────────────────────────────────────────────────


@cli.group()
@click.pass_context
def config(ctx):
    """Manage configuration."""
    pass


@config.command("show")
@click.pass_context
def config_show(ctx):
    """Show current configuration."""
    cfg: Config = ctx.obj["config"]
    click.echo(f"Database: {cfg.db_path}")
    click.echo(f"Config file: {DEFAULT_CONFIG_PATH}")
    click.echo()
    click.echo("Tracked directories:")
    for d in cfg.dirs.tracked:
        click.echo(f"  - {d}")
    click.echo()
    click.echo("Weights:")
    click.echo(f"  frontmatter: {cfg.weights.frontmatter}")
    for k, v in cfg.weights.section_overrides.items():
        click.echo(f"  {k}: {v}")
    click.echo(f"  section:*: {cfg.weights.section_wildcard}")
    click.echo(f"  code_block:*: {cfg.weights.code_block_wildcard}")
    click.echo(f"  reference_file: {cfg.weights.reference_file}")
    click.echo(f"  script_file: {cfg.weights.script_file}")
    click.echo()
    click.echo("Embedding:")
    click.echo(f"  model: {cfg.embedding.model}")
    click.echo(f"  device: {cfg.embedding.device}")
    click.echo(f"  batch_size: {cfg.embedding.batch_size}")
    click.echo()
    click.echo(f"Scan interval: {cfg.scan.interval_minutes} min")


@config.command("set")
@click.argument("key")
@click.argument("value")
@click.pass_context
def config_set(ctx, key, value):
    """Set a configuration value.

    Keys use dotted notation, e.g.:

    \b
      dirs.tracked /path/to/skills
      weights.section:description 0.25
      embedding.model all-mpnet-base-v2
    """
    cfg: Config = ctx.obj["config"]

    parts = key.split(".", 1)
    if len(parts) < 2:
        click.echo("Error: use dotted key like 'dirs.tracked' or 'embedding.model'", err=True)
        sys.exit(1)

    section, subkey = parts

    try:
        if section == "dirs":
            if subkey == "tracked":
                cfg.dirs.tracked.append(str(Path(value).expanduser().resolve()))
            else:
                click.echo(f"Error: unknown dirs key: {subkey}", err=True)
                sys.exit(1)
        elif section == "weights":
            cfg.weights.section_overrides[subkey] = float(value)
        elif section == "embedding":
            if hasattr(cfg.embedding, subkey):
                setattr(cfg.embedding, subkey, value)
            else:
                click.echo(f"Error: unknown embedding key: {subkey}", err=True)
                sys.exit(1)
        elif section == "scan":
            setattr(cfg.scan, subkey, int(value))
        elif section == "db_path":
            cfg.db_path = value
        else:
            click.echo(f"Error: unknown section: {section}", err=True)
            sys.exit(1)
    except (ValueError, AttributeError) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    save_config(cfg)
    click.echo(f"Saved: {key} = {value}")


@config.command("init")
@click.option("--add-src", multiple=True, help="Add a source directory")
@click.pass_context
def config_init(ctx, add_src):
    """Initialize default configuration."""
    cfg = Config()
    for src in add_src:
        cfg.dirs.tracked.append(str(Path(src).expanduser().resolve()))

    save_config(cfg)
    click.echo(f"Config initialized at {DEFAULT_CONFIG_PATH}")
    for d in cfg.dirs.tracked:
        click.echo(f"  Tracked: {d}")


def main():
    cli()
