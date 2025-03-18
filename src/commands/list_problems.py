from typing import Optional

import typer

status_map = {
    "attempted": "TRIED",
    "solved": "AC",
    "todo": "NOT_STARTED",
}


def list_problems(
    difficulty: Optional[str] = typer.Option(
        None, "--difficulty", "-d", help="Filter by difficulty (easy/medium/hard)"
    ),
    status: Optional[str] = typer.Option(
        None, "--status", "-s", help="Filter by status (todo/attempted/solved)"
    ),
    tag: Optional[str] = typer.Option(
        None, "--tag", "-t", help="Filter by tags (comma-separated)"
    ),
    category_slug: Optional[str] = typer.Option(
        "all-code-essentials", "--category-slug", "-c", help="Filter by category slug"
    ),
):
    """List available LeetCode problems with optional filters."""

    from rich.progress import Progress, SpinnerColumn, TextColumn

    from ..lib.profile_ui import display_problem_list
    from ..server.api import fetch_problem_list
    from ..server.auth import Auth

    AuthManager = Auth()

    if difficulty is not None or status is not None or tag is not None:
        if not AuthManager.is_authenticated:
            typer.echo(
                typer.style(
                    "❌ Please login first to enable problem listing with filters",
                    fg=typer.colors.RED,
                )
            )
            raise typer.Exit(1)

    tags = tag.split(",") if tag else []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task("Fetching problems...", total=1)

        session = AuthManager.session_manager.load_session()
        if not session:
            typer.echo(
                typer.style(
                    "❌ No valid session found. Please login first.",
                    fg=typer.colors.RED,
                )
            )
            raise typer.Exit(1)

        data = fetch_problem_list(
            csrf_token=session["csrftoken"],
            session_id=session["session_token"],
            categorySlug=category_slug or "all-code-essentials",
            filters={
                "difficulty": difficulty,
                "status": status_map.get(status) if status is not None else None,
                "tags": tags,
            },
        )
    display_problem_list(data)
