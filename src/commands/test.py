import typer
from pathlib import Path
from ..server.auth import Auth
from ..server.solution_manager import SolutionManager
from ..server.config import LANGUAGE_MAP
from ..lib.submission_ui import (
    display_auth_error, display_file_not_found_error,
    display_language_detection_error, display_submission_results, display_exception_error,
    create_submission_progress, display_language_detection_message
)

auth_manager = Auth()
solution_manager = SolutionManager(auth_manager.get_session())

FILE_EXT_TO_LANG = {ext.lstrip('.'): lang for ext, lang in LANGUAGE_MAP.items()}

def test(
    problem: str = typer.Argument(..., help="Problem slug (e.g., 'two-sum')"),
    file: Path = typer.Argument(..., help="Path to solution file"),
):
    """Test a solution with LeetCode's test cases"""
    if not auth_manager.is_authenticated:
        display_auth_error()

    if not file.exists():
        display_file_not_found_error(file)

    with open(file, 'r') as f:
        code = f.read()

    file_ext = file.suffix[1:] if file.suffix else ""
    lang = FILE_EXT_TO_LANG.get(file_ext)
    if not lang:
        display_language_detection_error(file.suffix)
        return

    display_language_detection_message(lang)

    typer.echo(typer.style("🧪 Testing solution with LeetCode test cases...", fg=typer.colors.YELLOW))

    try:
        with create_submission_progress() as progress:
            test_task = progress.add_task("Testing...", total=1)
            progress.update(test_task, advance=0.5)
            result = solution_manager.test_solution(problem, code, lang)
            progress.update(test_task, advance=0.5)

        display_submission_results(result)

    except Exception as e:
        display_exception_error(e)