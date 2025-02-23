import typer
from .edit import edit
from ..server.api import get_daily_question

def daily(
    lang: str = typer.Argument("py", help="Programming language to use."),
    editor: str = typer.Option("code", '-e', help="Code editor to use."),
):
    """Check the daily problem."""
    from .show import show

    if editor not in ['code', 'vim', 'nano']:
        typer.echo(typer.style(f"❌ Unsupported editor: {editor}", fg=typer.colors.RED))
        raise typer.Exit(1)

    result = get_daily_question()
    question = result['data']['activeDailyCodingChallengeQuestion']

    show(problem=question['question']['titleSlug'], layout=True)

    if editor:
        edit(problem=question['question']['titleSlug'], lang=lang, editor=editor)