import typer


def solutions(
    problem: str = typer.Argument(
        ..., help="Problem slug or number (e.g., 'two-sum' or '1')"
    ),
    best: bool = typer.Option(
        False, "--best", "-b", help="Show the best solution for the problem"
    ),
):
    """Fetch solution for a problem"""

    from rich.progress import Progress, SpinnerColumn, TextColumn

    from src.lib.solution_ui import SolutionUI

    from ..server.auth import Auth
    from ..server.solution_manager import SolutionManager

    auth = Auth()
    solution_manager = SolutionManager(auth.get_session())

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            progress.add_task("Fetching problem solutions...", total=1)
            fetched_solution = solution_manager.get_problem_solutions(problem, best)

            if not fetched_solution:
                typer.echo("No solution found")
            else:
                solution_ui = SolutionUI(
                    fetched_solution.get("data", {}).get("ugcArticleSolutionArticles")
                )
                solution_ui.show_solution()
    except Exception as e:
        typer.secho("Error fetching solution for problem ", fg="red", nl=False)
        typer.secho(f'"{problem}"', fg="bright_red", bold=True)
        typer.secho(f"\n{e}", fg="yellow", italic=True)
