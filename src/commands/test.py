import typer
from pathlib import Path
from src.server.auth import Auth
from src.server.solution_manager import SolutionManager

auth_manager = Auth()
solution_manager = SolutionManager(auth_manager.get_session())

map_lang = {
    "py": "python3",
    "java": "java",
    "js": "javascript",
    "c": "c",
    "cpp": "cpp"
}

def test(
    problem: str = typer.Argument(..., help="Problem slug (e.g., 'two-sum')"),
    file: Path = typer.Argument(..., help="Path to solution file"),
):
    """Test a solution with LeetCode's test cases"""
    if not auth_manager.is_authenticated:
        typer.echo(typer.style("❌ Please login first using the login command", fg=typer.colors.RED))
        raise typer.Exit(1)

    if not file.exists():
        typer.echo(typer.style(f"❌ File not found: {file}", fg=typer.colors.RED))
        raise typer.Exit(1)

    with open(file, 'r') as f:
        code = f.read()

    lang = map_lang.get(file.suffix[1:])
    if not lang:
        typer.echo(typer.style(f"❌ Unsupported file extension: {file.suffix}", fg=typer.colors.RED))
        raise typer.Exit(1)

    typer.echo(typer.style("🧪 Testing solution with LeetCode test cases...", fg=typer.colors.YELLOW))
    result = solution_manager.test_solution(problem, code, lang)

    if result["success"]:
        status_color = typer.colors.GREEN if result["status"] == "Accepted" else typer.colors.RED
        typer.echo(typer.style(f"\n✨ Status: {result['status']}", fg=status_color))
        if "runtime" in result:
            typer.echo(f"⏱️  Runtime: {result['runtime']}")
        if "memory" in result:
            typer.echo(f"💾 Memory: {result['memory']}")
        typer.echo("\nTest Case Results:")
        typer.echo(f"📥 Input: {result['input']}")
        typer.echo(f"📤 Your Output: {result['output']}")
        typer.echo(f"✅ Expected: {result['expected']}")
    else:
        typer.echo(typer.style(f"\n❌ {result['error']}", fg=typer.colors.RED))