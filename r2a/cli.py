"""r2a CLI. M0 ships `info`; `ingest`/`run`/`worker` arrive in M1–M4."""

from __future__ import annotations

import typer

from r2a import __version__
from r2a.config import Config
from r2a.factory import build_deps

app = typer.Typer(help="Research to Artifact — local-first agentic knowledge app.")


@app.command()
def info(config_path: str = typer.Option(None, "--config", help="TOML config")) -> None:
    """Show the active configuration and which adapters are wired."""
    cfg = Config.load(config_path)
    deps = build_deps(cfg)
    typer.echo(f"research-to-artifact {__version__}")
    typer.echo(f"  llm      : {deps.llm.name}  (routing={cfg.llm.routing})")
    typer.echo(f"  embedder : {deps.embedder.model_id}")
    typer.echo(f"  store    : {type(deps.store).__name__}")
    typer.echo(f"  workspace: {cfg.paths.root()}")


if __name__ == "__main__":
    app()
