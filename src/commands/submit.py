import typer
from pathlib import Path
from ..server.auth import Auth
from ..server.solution_manager import SolutionManager

auth_manager = Auth()
solution_manager = SolutionManager(auth_manager.get_session())

def submit(
    problem: str = typer.Argument(..., help="Problem slug (e.g., 'two-sum')"),
    file: Path = typer.Argument(..., help="Path to solution file"),
    lang: str = typer.Option("python3", help="Programming language")
):
    """Submit a solution to LeetCode"""
    if not auth_manager.is_authenticated:
        typer.echo(typer.style("❌ Please login first using the login command", fg=typer.colors.RED))
        raise typer.Exit(1)

    if not file.exists():
        typer.echo(typer.style(f"❌ File not found: {file}", fg=typer.colors.RED))
        raise typer.Exit(1)

    with open(file, 'r') as f:
        code = f.read()

    typer.echo(typer.style("📤 Submitting solution...", fg=typer.colors.YELLOW))
    result = solution_manager.submit_solution(problem, code, lang)

    if result["success"]:
        status_color = typer.colors.GREEN if result["status"] == "Accepted" else typer.colors.RED
        typer.echo(typer.style(f"\n✨ Status: {result['status']}", fg=status_color))
        typer.echo(f"⏱️  Runtime: {result['runtime']}")
        typer.echo(f"💾 Memory: {result['memory']}")
        typer.echo(f"✅ Passed: {result['passed_testcases']}/{result['total_testcases']} test cases")
    else:
        typer.echo(typer.style(f"\n❌ Submission failed: {result['error']}", fg=typer.colors.RED))