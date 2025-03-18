import typer

from src.commands.daily import daily
from src.commands.edit import edit
from src.commands.list_problems import list_problems
from src.commands.login import login, logout
from src.commands.profile import profile
from src.commands.show import show
from src.commands.solution import solutions
from src.commands.submit import submit
from src.commands.test import test
from src.lib.welcome import display_welcome

app = typer.Typer()

app.command(name="show")(show)
app.command(name="list")(list_problems)
app.command(name="daily")(daily)
app.command(name="profile")(profile)
app.command(name="login")(login)
app.command(name="logout")(logout)
app.command(name="submit")(submit)
app.command(name="test")(test)
app.command(name="edit")(edit)
app.command(name="solutions")(solutions)


@app.callback(invoke_without_command=True)
def callback(ctx: typer.Context):
    """LeetCode CLI - A command-line tool for LeetCode problems."""
    if ctx.invoked_subcommand is None:
        display_welcome(app)
        typer.echo(ctx.get_help())


def main():
    app()


if __name__ == "__main__":
    main()
