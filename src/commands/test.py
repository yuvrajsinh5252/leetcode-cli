from pathlib import Path

import typer

from src.server.config import LANGUAGE_MAP


def test(
    problem: str = typer.Argument(..., help="Problem slug (e.g., 'two-sum')"),
    file: Path = typer.Argument(..., help="Path to solution file"),
):
    """Test a solution with LeetCode's test cases"""

    from ..lib.submission_ui import (
        create_submission_progress,
        display_auth_error,
        display_exception_error,
        display_file_not_found_error,
        display_language_detection_error,
        display_language_detection_message,
        display_submission_results,
    )
    from ..server.auth import Auth
    from ..server.solution_manager import SolutionManager

    auth_manager = Auth()
    solution_manager = SolutionManager(auth_manager.get_session())

    FILE_EXT_TO_LANG = {ext.lstrip("."): lang for ext, lang in LANGUAGE_MAP.items()}

    if not auth_manager.is_authenticated:
        display_auth_error()

    if not file.exists():
        display_file_not_found_error(file)

    with open(file, "r") as f:
        code = f.read()

    file_ext = file.suffix[1:] if file.suffix else ""
    lang = FILE_EXT_TO_LANG.get(file_ext)
    if not lang:
        display_language_detection_error(file.suffix)
        return

    display_language_detection_message(lang)

    try:
        with create_submission_progress() as progress:
            progress.add_task("Testing...", total=1)
            result = solution_manager.test_solution(problem, code, lang)

        display_submission_results(result, is_test=True)

    except Exception as e:
        display_exception_error(e)
