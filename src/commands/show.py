import typer
from rich.console import Console
from src.lib.problem_ui import ProblemDetails
from src.server.auth import Auth
from src.server.solution_manager import SolutionManager

auth_manager = Auth()
solution_manager = SolutionManager(auth_manager.get_session())
console = Console()

def show(problem: str = typer.Argument(..., help="Problem slug (e.g., 'two-sum')")):
    """Show problem details including description and test cases"""
    if not auth_manager.is_authenticated:
        typer.echo(typer.style("❌ Please login first using the login command", fg=typer.colors.RED))
        raise typer.Exit(1)

    data = solution_manager.get_question_data(problem)
    if not data.get('data', {}).get('question'):
        typer.echo(typer.style(f"❌ Problem '{problem}' not found", fg=typer.colors.RED))
        raise typer.Exit(1)


    ProblemDetails(data.get('data', {}).get('question')).display()