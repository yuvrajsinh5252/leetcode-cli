import typer
from rich.console import Console
from ..lib.problem_ui import ProblemDetails
from ..server.auth import Auth
from ..server.solution_manager import SolutionManager

auth_manager = Auth()
solution_manager = SolutionManager(auth_manager.get_session())
console = Console()

def show(problem: str = typer.Argument(..., help="Problem slug or number (e.g., 'two-sum' or '1')"), layout: bool = False):
    """Show problem details including description and test cases"""

    if not auth_manager.is_authenticated:
        typer.echo(typer.style("❌ Please login first using the login command", fg=typer.colors.RED))
        raise typer.Exit(1)

    data = solution_manager.get_question_data(problem)
    if not data.get('data', {}).get('question'):
        typer.echo(typer.style(f"❌ Problem '{problem}' not found", fg=typer.colors.RED))
        raise typer.Exit(1)

    if not layout:
        ProblemDetails(data.get('data', {}).get('question')).display_full()
    else:
        ProblemDetails(data.get('data', {}).get('question')).display()