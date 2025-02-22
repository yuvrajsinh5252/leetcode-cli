
from rich.spinner import Spinner
from rich.live import Live
from typing import Optional
from src.lib.ui import display_problem_list
from src.server.auth import Auth

import typer

from src.server.api import fetch_problem_list

status_map = {
  "attempted": "TRIED",
  "solved": "AC",
  "todo": "NOT_STARTED",
}

AuthManager = Auth()

def list_problems(
  difficulty: Optional[str] = typer.Option(None, "--difficulty", "-d", help="Filter by difficulty (easy/medium/hard)"),
  status: Optional[str] = typer.Option(None, "--status", "-s", help="Filter by status (todo/in-progress/done)"),
  tag: Optional[str] = typer.Option(None, "--tag", "-t", help="Filter by tags (comma-separated)"),
  category_slug: Optional[str] = typer.Option("all-code-essentials", "--category-slug", "-c", help="Filter by category slug")
):
  """List available LeetCode problems with optional filters."""
  if (difficulty is not None or status is not None or tag is not None):
    if not AuthManager.is_authenticated:
      typer.echo(typer.style("❌ Please login first to enable problem listing with filters", fg=typer.colors.RED))
      raise typer.Exit(1)

  tags = tag.split(',') if tag else []

  with Live(Spinner('dots'), refresh_per_second=10) as live:
    live.console.print("[cyan]Fetching problems...")

    session = AuthManager.session_manager.load_session()
    if not session:
        typer.echo(typer.style("❌ No valid session found. Please login first.", fg=typer.colors.RED))
        raise typer.Exit(1)

    data = fetch_problem_list(
      csrf_token=session["csrftoken"],
      session_id=session["session_token"],
      categorySlug=category_slug or "all-code-essentials",
      filters={
        "difficulty": difficulty,
        "status":  status_map.get(status) if status is not None else None,
        "tags": tags
      }
    )
  display_problem_list(data)