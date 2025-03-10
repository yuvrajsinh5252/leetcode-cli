import typer
from pathlib import Path
from ..server.auth import Auth
from ..server.solution_manager import SolutionManager

auth_manager = Auth()
solution_manager = SolutionManager(auth_manager.get_session())

map_lang = {
    "py": "python3",
    "java": "java",
    "js": "javascript",
    "ts": "typescript",
    "c": "c",
    "cpp": "cpp",
    "cs": "csharp",
    "go": "golang",
    "rb": "ruby",
    "swift": "swift",
    "rs": "rust",
    "php": "php"
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
        typer.echo(f"Supported extensions: {', '.join(map_lang.keys())}")
        raise typer.Exit(1)

    typer.echo(typer.style("🧪 Testing solution with LeetCode test cases...", fg=typer.colors.YELLOW))
    try:
        result = solution_manager.test_solution(problem, code, lang)
    except Exception as e:
        typer.echo(typer.style(f"❌ Error connecting to LeetCode: {str(e)}", fg=typer.colors.RED))
        raise typer.Exit(1)

    if result["success"]:
        status_color = typer.colors.GREEN if result["status"] == "Accepted" else typer.colors.RED
        status_prefix = "✨" if result['status'] == "Accepted" else "❌"
        typer.echo(typer.style(f"\n{status_prefix} Status: {result['status']}", fg=status_color))
        if "runtime" in result:
            typer.echo(f"⏱️Runtime: {result['runtime']}")
        if "memory" in result:
            typer.echo(f"💾 Memory: {result['memory']}")
        typer.echo("\nTest Case Results:\n")
        typer.echo(f"📤 Your Output:\n{result['output']}")
        typer.echo(f"✅ Expected:\n{result['expected']}")
    else:
        typer.echo(typer.style(f"\n❌ {result['status']}", fg=typer.colors.BRIGHT_RED))
        error_message = f"\n{result['error']}"
        if result.get('full_error'):
            error_message += f"\n\nFull error:\n{result['full_error']}"
        typer.echo(typer.style(error_message, fg=typer.colors.RED))