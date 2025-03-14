import typer

from ..server.auth import Auth
from ..server.config import LANGUAGE_MAP
from ..server.solution_manager import SolutionManager

solution_manager = SolutionManager(Auth().get_session())


def edit(
    problem: str = typer.Argument(..., help="Problem name or id."),
    lang: str = typer.Argument("cpp", help="Programming language to use."),
    editor: str = typer.Option(
        "vim", "-e", "--editor", help="Editor to use for code editing."
    ),
):
    """Solves a problem by passing lang param and open it with your code editor."""
    question_data = (
        solution_manager.get_question_data(problem).get("data", {}).get("question")
    )

    if not question_data:
        typer.echo(f"Problem {problem} not found.")
        return

    filename_prefix = question_data.get("questionFrontendId") or (
        problem if problem.isdigit() else question_data.get("questionId")
    )

    def create_file_with_template(lang: str):
        filename = f"{filename_prefix}.{lang}"
        with open(filename, "w") as f:
            for snippet in question_data.get("codeSnippets", []):
                if snippet.get("langSlug").lower() == LANGUAGE_MAP.get(lang):
                    f.write(snippet.get("code"))
                    return
            typer.echo(f"No template found for language {lang}")

    create_file_with_template(lang)

    import subprocess

    subprocess.run([editor, f"{filename_prefix}.{lang}"])
