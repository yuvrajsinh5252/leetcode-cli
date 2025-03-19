import os
import subprocess

import typer


def edit(
    problem: str = typer.Argument(..., help="Problem name or id."),
    lang: str = typer.Argument("cpp", help="Programming language to use."),
    editor: str = typer.Option(
        "vim", "-e", "--editor", help="Editor to use for code editing."
    ),
):
    """Solves a problem by passing lang param and open it with your code editor."""
    from ..server.auth import Auth
    from ..server.config import LANGUAGE_MAP
    from ..server.solution_manager import SolutionManager
    from .show import _save_problem_to_file

    solution_manager = SolutionManager(Auth().get_session())

    question_data = (
        solution_manager.get_question_data(problem).get("data", {}).get("question")
    )

    if not question_data:
        typer.echo(f"Problem {problem} not found.")
        return

    filename_prefix = question_data.get("questionFrontendId") or (
        problem if problem.isdigit() else question_data.get("questionId")
    )

    try:
        _save_problem_to_file(question_data)
    except Exception as e:
        typer.echo(f"Warning: Could not save problem description: {str(e)}")

    problem_title_slug = question_data.get("titleSlug", problem)
    markdown_file = f"{problem_title_slug}.md"
    code_file_path = f"{filename_prefix}.{lang}"

    def create_file_with_template(lang: str):
        available_languages = {}
        for snippet in question_data.get("codeSnippets", []):
            available_languages[snippet.get("langSlug").lower()] = snippet.get("code")

        with open(code_file_path, "w") as f:
            if lang.lower() in available_languages:
                f.write(available_languages[lang.lower()])
                return code_file_path

            mapped_lang = LANGUAGE_MAP.get(lang.lower())
            if mapped_lang and mapped_lang in available_languages:
                f.write(available_languages[mapped_lang])
                return code_file_path

            reverse_map = {v: k for k, v in LANGUAGE_MAP.items()}
            if (
                lang.lower() in reverse_map
                and reverse_map[lang.lower()] in available_languages
            ):
                f.write(available_languages[reverse_map[lang.lower()]])
                return code_file_path

            typer.echo(f"No template found for language {lang}.")
            typer.echo(
                "Available language templates: " + ", ".join(available_languages.keys())
            )
            typer.echo("Creating empty file.")

        return code_file_path

    if not os.path.exists(code_file_path):
        code_file_path = create_file_with_template(lang)

    if not os.path.exists(markdown_file):
        typer.echo(f"Warning: Problem description file not found: {markdown_file}")
        subprocess.run([editor, code_file_path])
        return

    try:
        vim_like_editors = ["vim", "nvim", "gvim", "neovim", "mvim", "lvim", "vimr"]
        editor_name = os.path.basename(editor.split()[0]).lower()

        if editor_name in vim_like_editors:
            subprocess.run(
                [editor, "-O", code_file_path, markdown_file, "-c", "set noswapfile"]
            )
            typer.echo(
                f"Tip: In {editor_name}, you might need a plugin to preview markdown. "
                "Try ':set ft=markdown' to at least get syntax highlighting."
            )
        elif editor == "code" or editor == "code-insiders":
            try:
                subprocess.run(
                    [
                        editor,
                        "--goto",
                        code_file_path,
                        markdown_file,
                        "--command",
                        "markdown.showPreviewToSide",
                    ],
                    stderr=subprocess.DEVNULL,
                )
            except Exception as e:
                typer.echo(f"Failed to open VS Code with markdown preview: {str(e)}")
        elif editor == "nano":
            typer.echo(
                "Note: Nano doesn't support split view or markdown preview. Opening code file only."
            )
            subprocess.run([editor, code_file_path])
        else:
            typer.echo(f"Note: Split view might not work properly in {editor}.")
            subprocess.run([editor, code_file_path, markdown_file])
    except Exception as e:
        typer.echo(f"Failed to open editor: {str(e)}")
