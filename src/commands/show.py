import os

import typer


def show(
    problem: str = typer.Argument(
        ..., help="Problem slug or number (e.g., 'two-sum' or '1')"
    ),
    save: bool = typer.Option(
        False, "--save", "-s", help="Save problem description to a file"
    ),
    compact: bool = typer.Option(
        False, "--compact", "-c", help="Display in compact layout"
    ),
):
    """
    Show problem details including description and test cases

    Fetches and displays the problem statement, examples, and metadata.
    Use --compact for a condensed view or --save to export to a file.
    """

    from rich.progress import Progress, SpinnerColumn, TextColumn

    from ..lib.problem_ui import ProblemDetails
    from ..server.auth import Auth
    from ..server.solution_manager import SolutionManager

    auth_manager = Auth()
    solution_manager = SolutionManager(auth_manager.get_session())

    if not auth_manager.is_authenticated:
        typer.echo(
            typer.style(
                "❌ Please login first using the login command", fg=typer.colors.RED
            )
        )
        raise typer.Exit(1)

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            progress.add_task("Fetching problem data...", total=1)
            data = solution_manager.get_question_data(problem)

        if not data.get("data", {}).get("question"):
            typer.echo(
                typer.style(f"❌ Problem '{problem}' not found", fg=typer.colors.RED)
            )
            raise typer.Exit(data.get("errors", ["Unknown error"]))

        question = data.get("data", {}).get("question")
        problem_details = ProblemDetails(question)

        if save:
            _save_problem_to_file(question)

        problem_details.display_probelm()

        if not compact:
            problem_details.display_stats()
            problem_details.display_additional_info()

    except Exception as e:
        typer.echo(typer.style(f"❌ Error: {str(e)}", fg=typer.colors.RED))
        raise typer.Exit(1)


def _save_problem_to_file(question_data):
    """Save the problem statement to a markdown file"""
    title_slug = question_data.get("titleSlug", "problem")
    title = question_data.get("title", "Untitled Problem")

    filename = f"{title_slug}.md"
    with open(filename, "w") as f:
        f.write(f"# {title}\n\n")
        f.write(f"**Difficulty:** {question_data.get('difficulty', 'Unknown')}\n\n")
        f.write(question_data.get("content", ""))

    typer.echo(
        typer.style(
            f"✅ Problem saved to {os.path.abspath(filename)}", fg=typer.colors.GREEN
        )
    )
