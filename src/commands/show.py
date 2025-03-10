import typer
import os
from rich.console import Console
from ..lib.problem_ui import ProblemDetails
from ..server.auth import Auth
from ..server.solution_manager import SolutionManager

auth_manager = Auth()
solution_manager = SolutionManager(auth_manager.get_session())
console = Console()

def show(
    problem: str = typer.Argument(..., help="Problem slug or number (e.g., 'two-sum' or '1')"),
    compact: bool = typer.Option(False, "--compact", "-c", help="Display in compact layout"),
    save: bool = typer.Option(False, "--save", "-s", help="Save problem description to a file")
):
    """
    Show problem details including description and test cases

    Fetches and displays the problem statement, examples, and metadata.
    Use --compact for a condensed view or --save to export to a file.
    """

    if not auth_manager.is_authenticated:
        typer.echo(typer.style("❌ Please login first using the login command", fg=typer.colors.RED))
        raise typer.Exit(1)

    try:
        data = solution_manager.get_question_data(problem)
        if not data.get('data', {}).get('question'):
            typer.echo(typer.style(f"❌ Problem '{problem}' not found", fg=typer.colors.RED))
            raise typer.Exit(1)

        question = data.get('data', {}).get('question')
        problem_details = ProblemDetails(question)

        if save:
            _save_problem_to_file(question)

        if compact:
            problem_details.display()
        else:
            problem_details.display_full()

    except Exception as e:
        typer.echo(typer.style(f"❌ Error: {str(e)}", fg=typer.colors.RED))
        raise typer.Exit(1)

def _save_problem_to_file(question_data):
    """Save the problem statement to a markdown file"""
    title_slug = question_data.get('titleSlug', 'problem')
    title = question_data.get('title', 'Untitled Problem')

    filename = f"{title_slug}.md"
    with open(filename, 'w') as f:
        f.write(f"# {title}\n\n")
        f.write(f"**Difficulty:** {question_data.get('difficulty', 'Unknown')}\n\n")
        f.write(question_data.get('content', ''))

    typer.echo(typer.style(f"✅ Problem saved to {os.path.abspath(filename)}", fg=typer.colors.GREEN))