import typer
import os
from pathlib import Path
from typing import Optional
from ..server.auth import Auth
from ..server.solution_manager import SolutionManager

auth_manager = Auth()
solution_manager = SolutionManager(auth_manager.get_session())

LANGUAGE_MAP = {
    '.py': 'python3',
    '.cpp': 'cpp',
    '.c': 'c',
    '.java': 'java',
    '.js': 'javascript',
    '.ts': 'typescript',
    '.go': 'golang',
    '.rs': 'rust',
    '.rb': 'ruby',
    '.cs': 'csharp',
    '.swift': 'swift',
    '.php': 'php',
}

def submit(
    problem: str = typer.Argument(..., help="Problem slug or number (e.g., 'two-sum' or '1')"),
    file: Path = typer.Argument(..., help="Path to solution file"),
    lang: Optional[str] = typer.Option(None, help="Programming language (auto-detected if not specified)"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation prompt")
):
    """
    Submit a solution to LeetCode

    Uploads your solution file to LeetCode and returns the verdict.
    Language is auto-detected from file extension if not specified.
    """
    if not auth_manager.is_authenticated:
        typer.echo(typer.style("❌ Please login first using the login command", fg=typer.colors.RED))
        raise typer.Exit(1)

    if not file.exists():
        typer.echo(typer.style(f"❌ File not found: {file}", fg=typer.colors.RED))
        raise typer.Exit(1)

    try:
        # Auto-detect language from file extension if not provided
        if not lang:
            extension = os.path.splitext(file)[1].lower()
            if extension in LANGUAGE_MAP:
                lang = LANGUAGE_MAP[extension]
                typer.echo(typer.style(f"🔍 Auto-detected language: {lang}", fg=typer.colors.BLUE))
            else:
                typer.echo(typer.style(f"❌ Could not detect language for {extension} files. Please specify with --lang", fg=typer.colors.RED))
                raise typer.Exit(1)

        with open(file, 'r') as f:
            code = f.read()

        # Confirm submission unless forced
        if not force:
            typer.echo(typer.style(f"Problem: {problem}", fg=typer.colors.BLUE))
            typer.echo(typer.style(f"Language: {lang}", fg=typer.colors.BLUE))
            typer.echo(typer.style(f"File: {file}", fg=typer.colors.BLUE))
            if not typer.confirm("Do you want to submit this solution?"):
                typer.echo(typer.style("Submission canceled", fg=typer.colors.YELLOW))
                raise typer.Exit(0)

        typer.echo(typer.style("📤 Submitting solution...", fg=typer.colors.YELLOW))
        result = solution_manager.submit_solution(problem, code, lang)

        if result["success"]:
            status = result['status']
            status_color = (
                typer.colors.GREEN if status == "Accepted"
                else typer.colors.YELLOW if status == "Runtime Error" or status == "Time Limit Exceeded"
                else typer.colors.RED
            )

            typer.echo(typer.style(f"\n✨ Status: {status}", fg=status_color))
            typer.echo(f"⏱️  Runtime: {result['runtime']}")
            typer.echo(f"💾 Memory: {result['memory']}")
            typer.echo(f"✅ Passed: {result['passed_testcases']}/{result['total_testcases']} test cases")

            if status != "Accepted":
                typer.echo(typer.style(f"\n❗ Error message: {result.get('error_message', 'No details available')}", fg=typer.colors.RED))
        else:
            typer.echo(typer.style(f"\n❌ Submission failed: {result['error']}", fg=typer.colors.RED))

    except Exception as e:
        typer.echo(typer.style(f"❌ Error: {str(e)}", fg=typer.colors.RED))
        raise typer.Exit(1)