import typer
import os
from pathlib import Path
from typing import Optional
from ..server.auth import Auth
from ..server.solution_manager import SolutionManager
from ..lib.submission_ui import (
    display_auth_error, display_file_not_found_error, display_language_detection_message,
    display_language_detection_error, display_problem_not_found_error, display_submission_details,
    display_submission_canceled, create_submission_progress, display_submission_results,
    display_exception_error
)

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
        display_auth_error()

    if not file.exists():
        display_file_not_found_error(file)

    try:
        # Auto-detect language from file extension if not provided
        if not lang:
            extension = os.path.splitext(file)[1].lower()
            if extension in LANGUAGE_MAP:
                lang = LANGUAGE_MAP[extension]
                display_language_detection_message(lang)
            else:
                display_language_detection_error(extension)

        with open(file, 'r') as f:
            code = f.read()

        # Confirm submission unless forced
        if not force:
            problem_name = solution_manager.get_question_data(problem).get('data', {}).get('question', {}).get('title')

            if not problem_name:
                display_problem_not_found_error(problem)

            if not display_submission_details(problem, problem_name, lang, file):
                display_submission_canceled()

        if not lang:
            display_language_detection_error("")
            return

        with create_submission_progress() as progress:
            submit_task = progress.add_task("Submitting...", total=1)
            progress.update(submit_task, advance=0.5)
            result = solution_manager.submit_solution(problem, code, lang)
            progress.update(submit_task, advance=0.5)

        display_submission_results(result)

    except Exception as e:
        display_exception_error(e)