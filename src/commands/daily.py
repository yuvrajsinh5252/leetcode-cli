import typer


def daily(
    lang: str = typer.Argument("py", help="Programming language to use."),
    editor: str = typer.Option("vim", "--editor", "-e", help="Code editor to use."),
    full: bool = typer.Option(
        False, "--full", "-f", help="Show full problem description"
    ),
    no_editor: bool = typer.Option(False, "--no-editor", help="Skip opening editor"),
):
    """
    Get and work on today's LeetCode daily challenge.

    Fetches the daily coding challenge, displays problem details,
    and opens it in your preferred editor.
    """
    from ..server.api import get_daily_question
    from .edit import edit
    from .show import show

    if editor not in ["code", "vim", "nano"]:
        typer.echo(typer.style(f"❌ Unsupported editor: {editor}", fg=typer.colors.RED))
        raise typer.Exit(1)

    typer.echo(
        typer.style("Fetching daily challenge...", fg=typer.colors.GREEN), nl=False
    )
    try:
        result = get_daily_question()
        question = result["data"]["activeDailyCodingChallengeQuestion"]
        typer.echo("\r" + " " * 30 + "\r", nl=False)

        show(problem=question["question"]["titleSlug"], save=False, compact=not full)
    except Exception as e:
        typer.echo(
            "\n"
            + typer.style(
                f"❌ Failed to fetch daily question: {str(e)}", fg=typer.colors.RED
            )
        )
        raise typer.Exit(1)

    if not no_editor and editor:
        try:
            edit(problem=question["question"]["titleSlug"], lang=lang, editor=editor)
        except Exception as e:
            typer.echo(
                typer.style(f"❌ Failed to open editor: {str(e)}", fg=typer.colors.RED)
            )
            raise typer.Exit(1)
