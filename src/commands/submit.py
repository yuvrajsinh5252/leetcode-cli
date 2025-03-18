import os
from pathlib import Path
from typing import Optional

import typer


def submit(
    problem: str = typer.Argument(
        ..., help="Problem slug or number (e.g., 'two-sum' or '1')"
    ),
    file: Path = typer.Argument(..., help="Path to solution file"),
    lang: Optional[str] = typer.Option(
        None, help="Programming language (auto-detected if not specified)"
    ),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation prompt"),
):
    """
    Submit a solution to LeetCode

    Uploads your solution file to LeetCode and returns the verdict.
    Language is auto-detected from file extension if not specified.
    """

    from ..lib.submission_ui import (
        create_submission_progress,
        display_auth_error,
        display_exception_error,
        display_file_not_found_error,
        display_language_detection_error,
        display_language_detection_message,
        display_problem_not_found_error,
        display_submission_canceled,
        display_submission_details,
        display_submission_results,
    )
    from ..server.auth import Auth
    from ..server.config import LANGUAGE_MAP
    from ..server.solution_manager import SolutionManager

    auth_manager = Auth()
    solution_manager = SolutionManager(auth_manager.get_session())

    if not auth_manager.is_authenticated:
        display_auth_error()

    if not file.exists():
        display_file_not_found_error(file)

    try:
        # Auto-detect language from file extension if not provided
        if not lang:
            extension = os.path.splitext(file)[1].lower().replace(".", "")
            if extension in LANGUAGE_MAP:
                lang = LANGUAGE_MAP[extension]
                display_language_detection_message(lang)
            else:
                display_language_detection_error(extension)

        with open(file, "r") as f:
            code = f.read()

        # Confirm submission unless forced
        if not force:
            problem_name = (
                solution_manager.get_question_data(problem)
                .get("data", {})
                .get("question", {})
                .get("title")
            )

            if not problem_name:
                display_problem_not_found_error(problem)

            if not display_submission_details(problem, problem_name, lang, file):
                display_submission_canceled()
                return

        if not lang:
            display_language_detection_error("")
            return

        with create_submission_progress() as progress:
            progress.add_task("Submitting...", total=1)
            result = solution_manager.submit_solution(problem, code, lang)

        display_submission_results(result, is_test=False)

    except Exception as e:
        display_exception_error(e)
