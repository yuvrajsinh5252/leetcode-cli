import profile
import typer
from src import show, profile
from src.commands.list_problems import list_problems
from src.commands.login import login, logout
from src.commands.submit import submit
from src.commands.test import test

app = typer.Typer()

app.command(name="show")(show)
app.command(name="list")(list_problems)
app.command(name="profile")(profile)
app.command(name="login")(login)
app.command(name="logout")(logout)
app.command(name="submit")(submit)
app.command(name="test")(test)

if __name__ == "__main__":
    app()