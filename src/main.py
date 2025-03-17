import importlib
from typing import Optional

import typer

app = typer.Typer(
    help="A sleek command-line tool for LeetCode - solve, test, and submit problems directly from your terminal."
)


def import_and_call(module_path, function_name, *args, **kwargs):
    """Import a module and call a function from it with given args."""
    module = importlib.import_module(module_path)
    func = getattr(module, function_name)
    return func(*args, **kwargs)


@app.command(name="login")
def login():
    """Login to LeetCode account."""
    return import_and_call("src.commands.login", "login")


@app.command(name="logout")
def logout():
    """Logout from LeetCode."""
    return import_and_call("src.commands.login", "logout")


@app.command(name="profile")
def profile():
    """Display LeetCode profile."""
    return import_and_call("src.commands.profile", "profile")


@app.command(name="daily")
def daily(
    lang: Optional[str] = typer.Argument(None, help="Programming language"),
    editor: Optional[str] = typer.Option(
        None, "--editor", "-e", help="Preferred editor"
    ),
    full: bool = typer.Option(False, "--full", "-f", help="Show full description"),
    save: bool = typer.Option(False, "--save", "-s", help="Save to file"),
    no_editor: bool = typer.Option(False, "--no-editor", help="Skip editor"),
):
    """Show today's challenge."""
    return import_and_call(
        "src.commands.daily",
        "daily",
        lang=lang,
        editor=editor,
        full=full,
        save=save,
        no_editor=no_editor,
    )


@app.command(name="list")
def list_problems(
    difficulty: Optional[str] = typer.Option(
        None, "--difficulty", "-d", help="Difficulty level"
    ),
    status: Optional[str] = typer.Option(None, "--status", "-s", help="Problem status"),
    tag: Optional[str] = typer.Option(None, "--tag", "-t", help="Problem tag"),
    category_slug: Optional[str] = typer.Option(
        None, "--category-slug", "-c", help="Category"
    ),
    page: int = typer.Option(1, help="Page number"),
):
    """List available problems."""
    return import_and_call(
        "src.commands.list_problems",
        "list_problems",
        difficulty=difficulty,
        status=status,
        tag=tag,
        category_slug=category_slug,
        page=page,
    )


@app.command(name="show")
def show(
    problem_id: str = typer.Argument(..., help="Problem Name/Number"),
    compact: bool = typer.Option(False, "--compact", "-c", help="Compact layout"),
):
    """Display problem details."""
    return import_and_call("src.commands.show", "show", problem_id, compact=compact)


@app.command(name="test")
def test(
    problem_id: str = typer.Argument(..., help="Problem Name/Number"),
    file_path: str = typer.Argument(..., help="Solution file path"),
):
    """Test your solution."""
    return import_and_call("src.commands.test", "test", problem_id, file_path)


@app.command(name="submit")
def submit(
    problem_id: str = typer.Argument(..., help="Problem Name/Number"),
    file_path: str = typer.Argument(..., help="Solution file path"),
    lang: Optional[str] = typer.Option(None, "--lang", help="Programming language"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
):
    """Submit your solution."""
    return import_and_call(
        "src.commands.submit", "submit", problem_id, file_path, lang=lang, force=force
    )


@app.command(name="edit")
def edit(
    problem_id: str = typer.Argument(..., help="Problem Name/Number"),
    lang: str = typer.Argument(..., help="Programming language"),
    editor: Optional[str] = typer.Option(
        None, "--editor", "-e", help="Preferred editor"
    ),
):
    """Edit solution in editor."""
    return import_and_call("src.commands.edit", "edit", problem_id, lang, editor=editor)


@app.command(name="solutions")
def solutions(
    problem_id: str = typer.Argument(..., help="Problem Name/Number"),
    best: bool = typer.Option(False, "--best", "-b", help="Show best solutions"),
):
    """View problem solutions."""
    return import_and_call("src.commands.solution", "solutions", problem_id, best=best)


def main():
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
